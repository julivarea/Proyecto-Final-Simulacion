import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.actuador import ActuadorBomba
from tests.helpers.testing_utils import GeneradorManual, Recolector

class MockActuadorModel(CoupledDEVS):
    def __init__(self, name="TestActuador"):
        super().__init__(name)

        # Emitiremos órdenes:
        # t=10.0: caudal_obj = 300.0
        # t=10.0+20.0=30.0: caudal_obj = 600.0
        cron_caudal = [
            {"delay": 10.0, "valor": 300.0},
            {"delay": 20.0, "valor": 600.0},
            {"delay": 1000.0, "valor": "DUMMY"}
        ]
        self.gen_caudal = self.addSubModel(GeneradorManual("GenCaudal", cron_caudal))
        
        # t=50.0: stop (True)
        cron_stop = [
            {"delay": 50.0, "valor": True},
            {"delay": 1000.0, "valor": "DUMMY"}
        ]
        self.gen_stop = self.addSubModel(GeneradorManual("GenStop", cron_stop))
        
        self.actuador = self.addSubModel(ActuadorBomba("Actuador"))
        self.rec_act = self.addSubModel(Recolector("Rec_actuador"))
        
        self.connectPorts(self.gen_caudal.out_port, self.actuador.in_caudal_obj)
        self.connectPorts(self.gen_stop.out_port, self.actuador.in_stop)
        self.connectPorts(self.actuador.out_caudal_real, self.rec_act.in_port)

def test_actuador_latencia_mecanica(reset_globals):
    """
    Test del Actuador de la Bomba (A).
    - Recibe órdenes de cambio de caudal y señales de detención.
    - Aplica una latencia mecánica (distribución Uniforme entre 0 y 0.5s).
    """
    modelo = MockActuadorModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(60.0)
    sim.simulate()

    eventos = modelo.rec_act.state["eventos"]
    
    assert len(eventos) == 3, "El actuador debe haber emitido 3 eventos de cambio de caudal"
    
    # 1era orden en t=10.0 con valor 300.0, pero acotado a 200.0
    assert 10.0 <= eventos[0]["tiempo"] <= 10.5
    assert eventos[0]["valor"] == 200.0
    
    # 2da orden en t=30.0 con valor 600.0, pero acotado a 200.0
    assert 30.0 <= eventos[1]["tiempo"] <= 30.5
    assert eventos[1]["valor"] == 200.0
    
    # 3era orden en t=50.0 (STOP -> 0.0)
    assert 50.0 <= eventos[2]["tiempo"] <= 50.5
    assert eventos[2]["valor"] == 0.0
