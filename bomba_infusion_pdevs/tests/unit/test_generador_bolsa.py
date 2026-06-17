import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.generador_bolsa import GeneradorFinBolsa, FasesBolsa
from tests.helpers.testing_utils import GeneradorManual, Recolector

class MockBolsaConstanteModel(CoupledDEVS):
    def __init__(self, name="TestBolsaConstante"):
        super().__init__(name)
        cronograma_sensor = [{"delay": 10.0, "valor": 600.0}]
        self.gen_sensor = self.addSubModel(GeneradorManual("SensorFalso", cronograma_sensor))
        self.gen_bolsa = self.addSubModel(GeneradorFinBolsa(capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0))
        self.rec_bolsa = self.addSubModel(Recolector("Rec_bolsa"))

        self.connectPorts(self.gen_sensor.out_port, self.gen_bolsa.in_caudal_medido)
        self.connectPorts(self.gen_bolsa.out_fin_bolsa, self.rec_bolsa.in_port)

def test_generador_bolsa_caudal_constante(reset_globals):
    """
    Test del Generador de Fin de Bolsa (G_fb) con caudal de entrada constante.
    - Se inyecta un caudal constante de 600 ml/h medido por el sensor a los 10s.
    - La bolsa tiene 500 ml y alerta de 60s.
    - Tarda 500 / 600 = 0.833h = 3000s en vaciarse por completo.
    - Como avisa 60s antes, la alerta se debe disparar a los 2950s.
    """
    modelo = MockBolsaConstanteModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(3600.0)
    sim.simulate()

    eventos = modelo.rec_bolsa.state["eventos"]
    assert len(eventos) >= 1, "Debe haber emitido al menos una alerta de fin de bolsa"
    
    # 10s de espera + 3000s de vaciado - 60s de anticipo = 2950s
    assert 2949.0 <= eventos[0]["tiempo"] <= 2951.0, f"La alerta debía emitirse en ~2950s, pero fue a los {eventos[0]['tiempo']}s"
    assert eventos[0]["valor"] is True

class MockBolsaVariableModel(CoupledDEVS):
    def __init__(self, name="TestBolsaVariable"):
        super().__init__(name)
        cronograma_variable = [
            {"delay": 10.0, "valor": 150.0},
            {"delay": 1000.0, "valor": 300.0},
            {"delay": 2000.0, "valor": 600.0}
        ]
        self.gen_sensor = self.addSubModel(GeneradorManual("SensorVar", cronograma_variable))
        self.gen_bolsa = self.addSubModel(GeneradorFinBolsa(capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0))
        self.rec_bolsa = self.addSubModel(Recolector("Rec_bolsa_var"))

        self.connectPorts(self.gen_sensor.out_port, self.gen_bolsa.in_caudal_medido)
        self.connectPorts(self.gen_bolsa.out_fin_bolsa, self.rec_bolsa.in_port)

def test_generador_bolsa_caudal_variable_y_relleno(reset_globals):
    """
    Test del Generador de Fin de Bolsa (G_fb) con caudal variable y simulación de relleno automático.
    - El caudal inyectado varía (150 -> 300 -> 600 ml/h).
    - Cuando se dispara la alerta, se espera 60 segundos y se asume relleno a 500 ml.
    """
    modelo = MockBolsaVariableModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(8000.0) 
    sim.simulate()

    eventos = modelo.rec_bolsa.state["eventos"]
    assert len(eventos) >= 2, "La bolsa debió vaciarse y rellenarse más de una vez en 8000s"
