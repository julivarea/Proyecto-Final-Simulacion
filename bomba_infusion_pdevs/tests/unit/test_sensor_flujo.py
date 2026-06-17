import pytest
import statistics
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.sensor_flujo import SensorFlujo
from tests.helpers.testing_utils import GeneradorManual, Recolector

class MockSensorFlujoModel(CoupledDEVS):
    def __init__(self, name="TestSensorFlujo"):
        super().__init__(name)
        cronograma_caudal = [{"delay": 1.0, "valor": 100.0}]
        self.gen_caudal = self.addSubModel(GeneradorManual("FuenteCaudal", cronograma_caudal))
        self.sensor = self.addSubModel(SensorFlujo())
        self.rec_sensor = self.addSubModel(Recolector("Rec_sensor"))

        self.connectPorts(self.gen_caudal.out_port, self.sensor.in_caudal_real)
        self.connectPorts(self.sensor.out_caudal_medido, self.rec_sensor.in_port)

def test_sensor_flujo_ruido_gaussiano(reset_globals):
    """
    Test del Sensor de Flujo (G_sf) con inyección de ruido Gaussiano.
    - Se inyecta un caudal real constante de 100 ml/h.
    - El sensor muestrea 1 vez por segundo.
    - El ruido es normal N(100, 20^2).
    """
    modelo = MockSensorFlujoModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(22.0)
    sim.simulate()

    eventos = modelo.rec_sensor.state["eventos"]
    valores = [e["valor"] for e in eventos]
    
    assert len(eventos) >= 20, "El sensor debe haber emitido al menos 20 lecturas (1 por segundo)"
    
    # Validaciones estadísticas
    media = statistics.mean(valores)
    desvio = statistics.stdev(valores)
    
    # 20% de ruido en un valor de 100 implica std ~ 20. Toleramos varianza en test unitario:
    assert 85.0 <= media <= 115.0, f"Media fuera del rango esperado: {media:.2f}"
    assert 5.0 <= desvio <= 35.0, f"Desvío fuera del rango esperado: {desvio:.2f}"
