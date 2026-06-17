import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.controlador import ControladorBomba, TokensRegistro, FasesControlador, EstadoBolsa
from tests.helpers.testing_utils import GeneradorManual, Recolector

class MockControladorModel(CoupledDEVS):
    def __init__(self, name="MockControladorModel", cron_orden=None, cron_caudal=None, cron_fin_bolsa=None, cron_conf=None):
        super().__init__(name)
        
        self.gen_orden = self.addSubModel(GeneradorManual("GenOrden", cron_orden or []))
        self.gen_caudal = self.addSubModel(GeneradorManual("GenCaudal", cron_caudal or []))
        self.gen_fin_bolsa = self.addSubModel(GeneradorManual("GenFinBolsa", cron_fin_bolsa or []))
        self.gen_conf = self.addSubModel(GeneradorManual("GenConf", cron_conf or []))
        
        self.controlador = self.addSubModel(ControladorBomba("Controlador"))
        
        self.rec_ajuste = self.addSubModel(Recolector("RecAjuste"))
        self.rec_detener = self.addSubModel(Recolector("RecDetener"))
        self.rec_alarma_baja = self.addSubModel(Recolector("RecAlarmaBaja"))
        self.rec_alarma_media = self.addSubModel(Recolector("RecAlarmaMedia"))
        self.rec_alarma_crit = self.addSubModel(Recolector("RecAlarmaCrit"))
        self.rec_registro = self.addSubModel(Recolector("RecRegistro"))
        
        self.connectPorts(self.gen_orden.out_port, self.controlador.in_orden_medica)
        self.connectPorts(self.gen_caudal.out_port, self.controlador.in_caudal_medido)
        self.connectPorts(self.gen_fin_bolsa.out_port, self.controlador.in_fin_bolsa)
        self.connectPorts(self.gen_conf.out_port, self.controlador.in_conf_enfermero)
        
        self.connectPorts(self.controlador.out_ajustar_caudal, self.rec_ajuste.in_port)
        self.connectPorts(self.controlador.out_detener_bomba, self.rec_detener.in_port)
        self.connectPorts(self.controlador.out_alarma_baja, self.rec_alarma_baja.in_port)
        self.connectPorts(self.controlador.out_alarma_media, self.rec_alarma_media.in_port)
        self.connectPorts(self.controlador.out_alarma_critica, self.rec_alarma_crit.in_port)
        self.connectPorts(self.controlador.out_registrar_evento, self.rec_registro.in_port)


def test_controlador_orden_medica():
    """
    Verifica que al recibir una orden médica se envíe ajuste_caudal
    y al recibir orden de 0.0 se envíe detener_bomba.
    """
    cron_orden = [
        {"delay": 5.0, "valor": 100.0},
        {"delay": 10.0, "valor": 0.0},
        {"delay": 1000.0, "valor": "DUMMY"}
    ]
    modelo = MockControladorModel(cron_orden=cron_orden)
    sim = Simulator(modelo)
    sim.setTerminationTime(20.0)
    sim.simulate()
    
    ajustes = modelo.rec_ajuste.state["eventos"]
    detenciones = modelo.rec_detener.state["eventos"]
    
    assert len(ajustes) == 1
    assert ajustes[0]["tiempo"] == 5.0
    assert ajustes[0]["valor"] == 100.0
    
    assert len(detenciones) == 1
    assert detenciones[0]["tiempo"] == 15.0
    assert detenciones[0]["valor"] is True

def test_controlador_desvio_caudal():
    """
    Verifica que si el desvío dura 5s emite alarma media,
    y si dura 10s emite alarma crítica y se detiene.
    """
    cron_orden = [{"delay": 1.0, "valor": 100.0}, {"delay": 1000.0, "valor": "DUMMY"}]
    
    # 2.0s es la primer medición, luego una cada segundo.
    cron_caudal = [{"delay": 2.0, "valor": 150.0}] + [{"delay": 1.0, "valor": 150.0} for _ in range(11)] + [{"delay": 1000.0, "valor": "DUMMY"}]
    
    modelo = MockControladorModel(cron_orden=cron_orden, cron_caudal=cron_caudal)
    sim = Simulator(modelo)
    sim.setTerminationTime(15.0)
    sim.simulate()
    
    alarmas_medias = modelo.rec_alarma_media.state["eventos"]
    alarmas_crit = modelo.rec_alarma_crit.state["eventos"]
    detenciones = modelo.rec_detener.state["eventos"]
    
    assert len(alarmas_medias) == 1
    assert alarmas_medias[0]["tiempo"] == 6.0 # t=2,3,4,5,6 (5 segundos de desvio)
    
    assert len(alarmas_crit) == 1
    assert alarmas_crit[0]["tiempo"] == 11.0 # t=...7,8,9,10,11 (10 segundos de desvio)
    
    assert len(detenciones) == 1
    assert detenciones[0]["tiempo"] == 11.0

def test_controlador_fin_bolsa():
    """
    Verifica que al recibir fin de bolsa inicie el temporizador,
    lanzando alarma baja inmediatamente y detener bomba a los 60s.
    """
    cron_orden = [{"delay": 1.0, "valor": 100.0}, {"delay": 1000.0, "valor": "DUMMY"}]
    cron_fin_bolsa = [{"delay": 5.1, "valor": True}, {"delay": 1000.0, "valor": "DUMMY"}]
    
    # Sensor emite lecturas normales para avanzar el tiempo interno del controlador
    cron_caudal = [{"delay": 2.0, "valor": 100.0}] + [{"delay": 1.0, "valor": 100.0} for _ in range(70)] + [{"delay": 1000.0, "valor": "DUMMY"}]
    
    modelo = MockControladorModel(cron_orden=cron_orden, cron_fin_bolsa=cron_fin_bolsa, cron_caudal=cron_caudal)
    sim = Simulator(modelo)
    sim.setTerminationTime(70.0)
    sim.simulate()
    
    alarmas_bajas = modelo.rec_alarma_baja.state["eventos"]
    detenciones = modelo.rec_detener.state["eventos"]
    
    assert len(alarmas_bajas) == 1
    assert alarmas_bajas[0]["tiempo"] == 5.1
    
    assert len(detenciones) >= 1
    assert detenciones[0]["tiempo"] == 65.0
