from pypdevs.minimal import CoupledDEVS

from src.models.atomic.generador_ordenes import GeneradorOrdenes
from src.models.atomic.generador_conf import GeneradorConfirmaciones
from src.models.atomic.generador_bolsa import GeneradorFinBolsa
from src.models.atomic.controlador import ControladorBomba
from src.models.atomic.actuador import ActuadorBomba
from src.models.atomic.sensor_flujo import SensorFlujo
from src.models.atomic.modulo_alarmas import ModuloAlarmas
from src.models.atomic.registrador import RegistradorEventos


class BombaAcoplada(CoupledDEVS):
    """
    Modelo Acoplado Global de la Bomba de Infusión (N)
    Integra todos los modelos atómicos en un sistema de lazo cerrado autocontenido.
    La única salida hacia el exterior (EOC) es la notificación del Módulo de Alarmas.
    """
    def __init__(self, name="BombaAcoplada"):
        super().__init__(name)

        # Instanciación de los submodelos (Componentes)
        self.g_om = self.addSubModel(GeneradorOrdenes("G_om"))
        self.g_ce = self.addSubModel(GeneradorConfirmaciones("G_ce"))
        self.g_fb = self.addSubModel(GeneradorFinBolsa("G_fb"))
        self.controlador = self.addSubModel(ControladorBomba("C"))
        self.actuador = self.addSubModel(ActuadorBomba("A"))
        self.sensor = self.addSubModel(SensorFlujo("G_sf"))
        self.alarmas = self.addSubModel(ModuloAlarmas("M_a"))
        self.registrador = self.addSubModel(RegistradorEventos("R_e"))

        # Definición de puertos del modelo acoplado
        # El sistema no tiene entradas externas (EIC) ya que es autocontenido.
        # Salida global del sistema (EOC) para emitir notificaciones al entorno hospitalario.
        self.out_alarma_global = self.addOutPort("out_alarma_global")

        # Conexiones Internas (IC) según la especificación formal

        # Entradas al Controlador
        # G_om -> C
        self.connectPorts(self.g_om.out_caudal_obj, self.controlador.in_orden_medica)
        
        # G_ce -> C y M_a
        self.connectPorts(self.g_ce.out_conf, self.controlador.in_conf_enfermero)
        self.connectPorts(self.g_ce.out_conf, self.alarmas.in_conf)
        
        # G_fb -> C
        self.connectPorts(self.g_fb.out_fin_bolsa, self.controlador.in_fin_bolsa)

        # Salidas del Controlador
        # C -> Actuador
        self.connectPorts(self.controlador.out_ajustar_caudal, self.actuador.in_caudal_obj)
        self.connectPorts(self.controlador.out_detener_bomba, self.actuador.in_stop)

        # C -> Módulo de Alarmas
        self.connectPorts(self.controlador.out_alarma_baja, self.alarmas.in_alarma_baja)
        self.connectPorts(self.controlador.out_alarma_media, self.alarmas.in_alarma_media)
        self.connectPorts(self.controlador.out_alarma_critica, self.alarmas.in_alarma_critica)

        # C -> Registrador de Eventos
        self.connectPorts(self.controlador.out_registrar_evento, self.registrador.in_registrar)

        # Lazo Físico
        # Actuador -> Sensor
        self.connectPorts(self.actuador.out_caudal_real, self.sensor.in_caudal_real)

        # Sensor -> C y G_fb
        self.connectPorts(self.sensor.out_caudal_medido, self.controlador.in_caudal_medido)
        self.connectPorts(self.sensor.out_caudal_medido, self.g_fb.in_caudal_medido)

        # Conexiones Externas de Salida (EOC)
        # M_a -> Entorno Exterior 
        self.connectPorts(self.alarmas.out_alarma, self.out_alarma_global)