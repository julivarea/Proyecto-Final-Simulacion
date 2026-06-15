from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY

class FasesAlarma:
    OCIOSO = "OCIOSO"
    NOTIFICAR = "NOTIFICAR"
    ESPERANDO_CONF = "ESPERANDO_CONF"
    REPETIR = "REPETIR"

class TiposAlarma:
    NINGUNA = "NINGUNA"
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    CRITICA = "CRITICA"

def prio(tipo_alarma):
    """Función de prioridad matemática."""
    prioridades = {
        TiposAlarma.NINGUNA: 0,
        TiposAlarma.BAJA: 1,
        TiposAlarma.MEDIA: 2,
        TiposAlarma.CRITICA: 3
    }
    return prioridades.get(tipo_alarma, 0)

class ModuloAlarmas(AtomicDEVS):
    """
    Módulo de Alarmas (M_a)
    Gestiona la presentación de alarmas al entorno hospitalario.
    Implementa un esquema jerárquico de prioridades y un ciclo de re-notificación 
    (cada 10s) para alarmas críticas no confirmadas (tras 30s).
    """
    def __init__(self, name="M_a"):
        super().__init__(name)

        # Puertos de entrada
        self.in_alarma_baja = self.addInPort("in_alarma_baja")
        self.in_alarma_media = self.addInPort("in_alarma_media")
        self.in_alarma_critica = self.addInPort("in_alarma_critica")
        self.in_conf = self.addInPort("in_conf")

        # Puertos de salida
        self.out_alarma = self.addOutPort("out_alarma")

        # Estado inicial: s0 = (OCIOSO, NINGUNA, INFINITY)
        self.state = {
            "fase": FasesAlarma.OCIOSO,
            "a": TiposAlarma.NINGUNA,
            "sigma": INFINITY
        }

    def timeAdvance(self):
        # ta(fase, a, sigma) = sigma
        return self.state["sigma"]

    def outputFnc(self):
        fase = self.state["fase"]
        a = self.state["a"]
        
        # lambda: Emite la alarma solo en las fases activas
        if fase == FasesAlarma.NOTIFICAR or fase == FasesAlarma.REPETIR:
            return {self.out_alarma: [a]}
        return {}

    def intTransition(self):
        fase = self.state["fase"]
        a = self.state["a"]

        if fase == FasesAlarma.NOTIFICAR and a != TiposAlarma.CRITICA:
            # Las alarmas menores se notifican y vuelven a silenciarse
            self.state["fase"] = FasesAlarma.OCIOSO
            self.state["a"] = TiposAlarma.NINGUNA
            self.state["sigma"] = INFINITY
            
        elif fase == FasesAlarma.NOTIFICAR and a == TiposAlarma.CRITICA:
            # La alarma crítica inicia la ventana de espera de 30 segundos
            self.state["fase"] = FasesAlarma.ESPERANDO_CONF
            self.state["sigma"] = 30.0
            
        elif fase == FasesAlarma.ESPERANDO_CONF:
            # Se agotó el tiempo de espera, transiciona a repetir inmediatamente
            self.state["fase"] = FasesAlarma.REPETIR
            self.state["sigma"] = 0.0
            
        elif fase == FasesAlarma.REPETIR:
            # Bucle de re-notificación cada 10 segundos
            self.state["sigma"] = 10.0

        return self.state

    def extTransition(self, inputs):
        fase_actual = self.state["fase"]
        a_actual = self.state["a"]
        
        # 1. Procesar confirmaciones del enfermero
        if self.in_conf in inputs:
            if a_actual == TiposAlarma.CRITICA:
                # Se confirma la alarma crítica, el módulo se silencia
                self.state["fase"] = FasesAlarma.OCIOSO
                self.state["a"] = TiposAlarma.NINGUNA
                self.state["sigma"] = INFINITY
            else:
                # Confirmación ignorada (no hay alarma crítica activa)
                self.state["sigma"] -= self.elapsed
            return self.state

        # 2. Identificar qué alarma entrante llegó (a')
        a_prime = TiposAlarma.NINGUNA
        if self.in_alarma_critica in inputs:
            a_prime = TiposAlarma.CRITICA
        elif self.in_alarma_media in inputs:
            a_prime = TiposAlarma.MEDIA
        elif self.in_alarma_baja in inputs:
            a_prime = TiposAlarma.BAJA

        # 3. Lógica de jerarquía y preempción
        if a_prime != TiposAlarma.NINGUNA:
            if fase_actual == FasesAlarma.OCIOSO or prio(a_prime) > prio(a_actual):
                # La nueva alarma tiene mayor prioridad o el sistema estaba libre
                self.state["fase"] = FasesAlarma.NOTIFICAR
                self.state["a"] = a_prime
                self.state["sigma"] = 0.0
            else:
                # La alarma entrante es de menor o igual prioridad, se ignora
                self.state["sigma"] -= self.elapsed

        return self.state