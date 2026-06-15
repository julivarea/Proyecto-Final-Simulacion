import statistics
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.sensor_flujo import SensorFlujo
from tests.testing_utils import GeneradorManual, Recolector

class TestSensorFlujo(CoupledDEVS):
    def __init__(self, name="TestSensorFlujo"):
        super().__init__(name)
        cronograma_caudal = [{"delay": 1.0, "valor": 100.0}]
        self.gen_caudal = self.addSubModel(GeneradorManual("FuenteCaudal", cronograma_caudal))
        self.sensor = self.addSubModel(SensorFlujo())
        self.rec_sensor = self.addSubModel(Recolector("Rec_sensor"))

        self.connectPorts(self.gen_caudal.out_port, self.sensor.in_caudal_real)
        self.connectPorts(self.sensor.out_caudal_medido, self.rec_sensor.in_port)

def correr_test():
    """
    Test del Sensor de Flujo (G_sf) con inyección de ruido Gaussiano.
    Comportamiento esperado:
    - Se inyecta un caudal real constante de 100 ml/h.
    - El sensor debe muestrear este valor 1 vez por segundo (ta = 1.0s).
    - Las lecturas de salida deben incorporar un ruido normal N(100, 20^2), 
      resultando en valores que varían pero mantienen una media cercana a 100 y desvío de 20.
    """
    modelo = TestSensorFlujo()
    sim = Simulator(modelo)
    sim.setTerminationTime(22.0)
    sim.simulate()

    eventos = modelo.rec_sensor.state["eventos"]
    valores = [e["valor"] for e in eventos]

    print(f"\n{'='*60}")
    print("TEST: SENSOR DE FLUJO CON RUIDO GAUSSIANO (22s)")
    print(f"{'='*60}")
    print(f"  Primeras 10 lecturas del sensor:")
    for e in eventos[:10]:
        error = ((e["valor"] - 100.0) / 100.0) * 100
        print(f"    - Tiempo: {e['tiempo']:>5.2f}s | Medición: {e['valor']:>7.2f} ml/h | Error: {error:>+6.2f}%")
    if len(eventos) > 10: print("    ... (truncado)")

    if len(valores) >= 2:
        media = statistics.mean(valores)
        desvio = statistics.stdev(valores)
        print(f"\n  Estadísticas:")
        print(f"    Media:          {media:>7.2f} ml/h (esperado: ~100.00)")
        print(f"    Desvío estándar: {desvio:>6.2f} ml/h (esperado: ~20.00)")
        print(f"    Rango:          [{min(valores):.2f}, {max(valores):.2f}] ml/h")

if __name__ == "__main__":
    correr_test()
