from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY

# Constantes y Enums basados en la especificación formal 

class FasesControlador:
    NORMAL = "NORMAL"
    BLOQUEADO_CRITICO = "BLOQUEADO_CRITICO"
    PROC_NORMAL = "PROC_NORMAL"
    PROC_BLOQUEADO = "PROC_BLOQUEADO"

class EstadoBolsa:
    CON_LIQUIDO = "CON_LIQUIDO"
    POR_AGOTARSE = "POR_AGOTARSE"

class TokensRegistro:
    NUEVA_ORDEN = "NUEVA_ORDEN"
    AJUSTE_CAUDAL = "AJUSTE_CAUDAL"
    DETENCION_MEDICA = "DETENCION_MEDICA"
    ALARMA_BAJA = "ALARMA_BAJA"
    ALARMA_MEDIA = "ALARMA_MEDIA"
    ALARMA_CRITICA = "ALARMA_CRITICA"
    FIN_BOLSA_DETECTADO = "FIN_BOLSA_DETECTADO"
    CONFIRMACION_ENFERMERO = "CONFIRMACION_ENFERMERO"


class ControladorBomba(AtomicDEVS):
    """
    Controlador de Bomba (C)
    Núcleo lógico del sistema de lazo cerrado. Evalúa desviaciones de caudal, 
    gestiona alertas de fin de bolsa, y coordina acciones de actuadores y alarmas.
    Utiliza un buffer de salidas para emitir acciones en ráfaga (tiempo 0).
    """
    def __init__(self, name="C"):
        super().__init__(name)

        # Puertos de Entrada
        self.in_orden_medica = self.addInPort("in_orden_medica")
        self.in_caudal_medido = self.addInPort("in_caudal_medido")
        self.in_fin_bolsa = self.addInPort("in_fin_bolsa")
        self.in_conf_enfermero = self.addInPort("in_conf_enfermero")

        # Puertos de Salida 
        self.out_ajustar_caudal = self.addOutPort("out_ajustar_caudal")
        self.out_detener_bomba = self.addOutPort("out_detener_bomba")
        self.out_alarma_baja = self.addOutPort("out_alarma_baja")
        self.out_alarma_media = self.addOutPort("out_alarma_media")
        self.out_alarma_critica = self.addOutPort("out_alarma_critica")
        self.out_registrar_evento = self.addOutPort("out_registrar_evento")

        # Estado Inicial (s0) 
        self.state = {
            "fase": FasesControlador.NORMAL,
            "caudal_obj": 0.0,
            "seg_desvio": 0.0,
            "seg_fin_bolsa": 0.0,
            "estado_bolsa": EstadoBolsa.CON_LIQUIDO,
            "cola_salidas": [], # Buffer FIFO para emitir ráfagas
            "sigma": INFINITY
        }

    def timeAdvance(self):
        # ta(...) = sigma
        return self.state["sigma"]

    def outputFnc(self):
        # lambda: Extrae el primer elemento de la cola de salidas activas
        if len(self.state["cola_salidas"]) > 0:
            puerto_destino, valor_a_emitir = self.state["cola_salidas"][0]
            return {puerto_destino: [valor_a_emitir]}
        return {}

    def intTransition(self):
        # delta_int: Descarta secuencialmente los elementos ya procesados
        if len(self.state["cola_salidas"]) > 0:
            # tail(cola_salidas)
            self.state["cola_salidas"].pop(0) 

        # Si aún quedan elementos por emitir, nos mantenemos a tiempo 0
        if len(self.state["cola_salidas"]) > 0:
            self.state["sigma"] = 0.0
        else:
            # Si el buffer se vació, retornamos de forma segura a reposo
            fase_actual = self.state["fase"]
            if fase_actual == FasesControlador.PROC_NORMAL:
                self.state["fase"] = FasesControlador.NORMAL
                self.state["sigma"] = INFINITY
            elif fase_actual == FasesControlador.PROC_BLOQUEADO:
                self.state["fase"] = FasesControlador.BLOQUEADO_CRITICO
                self.state["sigma"] = INFINITY

        return self.state

    def extTransition(self, inputs):
        fase = self.state["fase"]
        caudal_obj = self.state["caudal_obj"]
        seg_desvio = self.state["seg_desvio"]
        seg_fin_bolsa = self.state["seg_fin_bolsa"]
        estado_bolsa = self.state["estado_bolsa"]
        cola_salidas = self.state["cola_salidas"]
        sigma = self.state["sigma"]

        # PUERTO: in_orden_medica
        if self.in_orden_medica in inputs:
            xv = inputs[self.in_orden_medica][0]
            
            if xv == 0.0:
                # Orden de detener bomba
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["caudal_obj"] = 0.0
                self.state["seg_desvio"] = 0.0
                self.state["cola_salidas"].extend([
                    (self.out_detener_bomba, True),
                    (self.out_registrar_evento, TokensRegistro.DETENCION_MEDICA)
                ])
                self.state["sigma"] = 0.0
            else:
                # Orden de ajustar caudal a nuevo valor
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["caudal_obj"] = xv
                self.state["seg_desvio"] = 0.0
                self.state["cola_salidas"].extend([
                    (self.out_ajustar_caudal, xv),
                    (self.out_registrar_evento, TokensRegistro.NUEVA_ORDEN)
                ])
                self.state["sigma"] = 0.0

            return self.state

        # PUERTO: in_caudal_medido 
        elif self.in_caudal_medido in inputs:
            xv = inputs[self.in_caudal_medido][0]

            # Si está bloqueado crítico, ignora silenciosamente
            if fase == FasesControlador.BLOQUEADO_CRITICO:
                self.state["sigma"] -= self.elapsed
                return self.state

            # El desvío supera el 10%?
            D = caudal_obj > 0 and abs(xv - caudal_obj) > (0.10 * caudal_obj):

            # Variables temporales matemáticas (sd' y sb')
            # Se suma 1.0 porque el sensor emite estrictamente cada 1 segundo
            sd_prime = seg_desvio + 1.0 if D else 0.0
            sb_prime = seg_fin_bolsa + 1.0 if estado_bolsa == EstadoBolsa.POR_AGOTARSE else seg_fin_bolsa

            # Evaluamos las sub-secuencias de salidas (Q_desvio y Q_bolsa)
            q_desvio = []
            if sd_prime == 5.0:
                # Desvío persistente 5s -> Alarma Media
                q_desvio = [
                    (self.out_alarma_media, True),
                    (self.out_registrar_evento, TokensRegistro.ALARMA_MEDIA)
                ]
            elif sd_prime == 10.0:
                # Desvío persistente 10s -> Alarma Crítica y Detención 
                q_desvio = [
                    (self.out_alarma_critica, True),
                    (self.out_detener_bomba, True),
                    (self.out_registrar_evento, TokensRegistro.ALARMA_CRITICA)
                ]

            q_bolsa = []
            if sb_prime == 60.0:
                # Fin de bolsa máximo excedido -> Detener Bomba
                q_bolsa = [
                    (self.out_detener_bomba, True),
                    (self.out_registrar_evento, TokensRegistro.DETENCION_MEDICA)
                ]

            q_nuevas = q_desvio + q_bolsa 

            # Resolucion del estado basado en q_nuevas y temporizadores
            if sd_prime == 10.0:
                self.state["fase"] = FasesControlador.PROC_BLOQUEADO
                self.state["caudal_obj"] = 0.0 # Bloqueo lógico
                self.state["seg_desvio"] = sd_prime
                self.state["seg_fin_bolsa"] = sb_prime
                self.state["cola_salidas"].extend(q_nuevas)
                self.state["sigma"] = 0.0

            elif sb_prime == 60.0 and sd_prime != 10.0:
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["caudal_obj"] = 0.0 # Detención
                self.state["seg_desvio"] = sd_prime
                self.state["seg_fin_bolsa"] = sb_prime
                self.state["cola_salidas"].extend(q_nuevas)
                self.state["sigma"] = 0.0

            elif len(q_nuevas) > 0 and sd_prime != 10.0 and sb_prime != 60.0:
                # Se emitirá una alarma media o similar, pero no se detiene ni bloquea
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["seg_desvio"] = sd_prime
                self.state["seg_fin_bolsa"] = sb_prime
                self.state["cola_salidas"].extend(q_nuevas)
                self.state["sigma"] = 0.0

            else:
                # Recibo lectura normal o desvío menor a 5s
                self.state["seg_desvio"] = sd_prime
                self.state["seg_fin_bolsa"] = sb_prime
                self.state["sigma"] -= self.elapsed

            return self.state

        # PUERTO: in_fin_bolsa
        elif self.in_fin_bolsa in inputs:
            # Se detecta que a la bolsa le restan 60s
            self.state["fase"] = FasesControlador.PROC_NORMAL
            self.state["estado_bolsa"] = EstadoBolsa.POR_AGOTARSE
            self.state["seg_fin_bolsa"] = 0.0
            self.state["cola_salidas"].extend([
                (self.out_alarma_baja, True),
                (self.out_registrar_evento, TokensRegistro.ALARMA_BAJA),
                (self.out_registrar_evento, TokensRegistro.FIN_BOLSA_DETECTADO)
            ])
            self.state["sigma"] = 0.0
            return self.state

        # PUERTO: in_conf_enfermero
        elif self.in_conf_enfermero in inputs:
            if fase == FasesControlador.BLOQUEADO_CRITICO:
                # Enfermero confirma la alarma crítica
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["cola_salidas"].extend([
                    (self.out_ajustar_caudal, caudal_obj), 
                    (self.out_registrar_evento, TokensRegistro.AJUSTE_CAUDAL)
                ])
                self.state["sigma"] = 0.0
            
            elif fase == FasesControlador.NORMAL:
                self.state["fase"] = FasesControlador.PROC_NORMAL
                self.state["cola_salidas"].extend([
                    (self.out_registrar_evento, TokensRegistro.CONFIRMACION_ENFERMERO)
                ])
                self.state["sigma"] = 0.0
            else:
                self.state["sigma"] -= self.elapsed
                
            return self.state

        # Fallback de seguridad (nunca debería alcanzarse)
        self.state["sigma"] -= self.elapsed
        return self.state