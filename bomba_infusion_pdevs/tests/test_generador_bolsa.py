from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.generador_bolsa import GeneradorFinBolsa
from src.models.atomic.generador_bolsa import FasesBolsa
from tests.testing_utils import GeneradorManual, Recolector

class TestGeneradorBolsaConstante(CoupledDEVS):
    def __init__(self, name="TestBolsaConstante"):
        super().__init__(name)
        cronograma_sensor = [{"delay": 10.0, "valor": 600.0}]
        self.gen_sensor = self.addSubModel(GeneradorManual("SensorFalso", cronograma_sensor))
        self.gen_bolsa = self.addSubModel(GeneradorFinBolsa(capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0))
        self.rec_bolsa = self.addSubModel(Recolector("Rec_bolsa"))

        self.connectPorts(self.gen_sensor.out_port, self.gen_bolsa.in_caudal_medido)
        self.connectPorts(self.gen_bolsa.out_fin_bolsa, self.rec_bolsa.in_port)


class TestGeneradorBolsaVariable(CoupledDEVS):
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

        # Monkey-patching para traza en vivo
        bolsa = self.gen_bolsa
        orig_ext = bolsa.extTransition
        orig_int = bolsa.intTransition
        
        def new_ext(inputs):
            t = bolsa.time_last[0] + bolsa.elapsed
            state = orig_ext(inputs)
            if bolsa.in_caudal_medido in inputs:
                caudal = inputs[bolsa.in_caudal_medido][0]
                print(f"  [t={t:>7.2f}s] Sensor envía caudal: {caudal:>6.2f} ml/h. Volumen restante: {state['volumen_restante_ml']:.2f} ml")
            return state

        def new_int():
            t = bolsa.time_next[0]
            state = orig_int()
            if state["fase"] == FasesBolsa.ESPERANDO_RELLENO:
                print(f"  [t={t:>7.2f}s] ¡Alerta disparada! Esperando 60s para que se vacíe y se rellene...")
            elif state["fase"] == FasesBolsa.MONITOREANDO:
                print(f"  [t={t:>7.2f}s] ¡Bolsa rellenada! Nuevo volumen: {state['volumen_restante_ml']:.2f} ml")
            return state

        bolsa.extTransition = new_ext
        bolsa.intTransition = new_int


def test_constante():
    """
    Test del Generador de Fin de Bolsa (G_fb) con caudal de entrada constante.
    Comportamiento esperado:
    - Se inyecta un caudal constante de 600 ml/h medido por el sensor (llegando a los 10s).
    - La bolsa tiene 500 ml y una anticipación de alerta de 60s.
    - Tarda 500 / 600 = 0.833h = 3000s en vaciarse por completo.
    - Como avisa 60s antes, la alerta se debe disparar exactamente a los 2950s de simulacion.
    """
    modelo = TestGeneradorBolsaConstante()
    sim = Simulator(modelo)
    sim.setTerminationTime(3600.0)
    sim.simulate()

    eventos = modelo.rec_bolsa.state["eventos"]
    print(f"\n{'='*60}")
    print("TEST: GENERADOR DE BOLSA (CAUDAL CONSTANTE 600 ml/h)")
    print(f"{'='*60}")
    for e in eventos:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | ¡Alarma Bolsa Vacía! (Valor: {e['valor']})")

def test_variable():
    """
    Test del Generador de Fin de Bolsa (G_fb) con caudal variable y simulación de relleno automático.
    Comportamiento esperado:
    - El caudal inyectado varía a lo largo de la simulación (150 -> 300 -> 600 ml/h).
    - La capacidad de la bolsa disminuye dinámicamente en función del flujo de ese instante.
    - Cuando se dispara la alerta de bolsa vacía, se espera 60 segundos y se asume que un enfermero la rellena a 500 ml.
    - Se verifica que el ciclo de vaciado, alerta y relleno se cumpla múltiples veces durante 8000s.
    """
    modelo = TestGeneradorBolsaVariable()
    sim = Simulator(modelo)
    sim.setTerminationTime(8000.0) 
    print(f"\n{'='*60}")
    print("TEST: GENERADOR DE BOLSA (CAUDAL VARIABLE Y RELLENO AUTOMÁTICO)")
    print(f"{'='*60}")
    sim.simulate()

    eventos = modelo.rec_bolsa.state["eventos"]
    print(f"\n  Alertas de fin de bolsa emitidas: {len(eventos)}")
    for e in eventos:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | ¡Alarma Bolsa Vacía! (Valor: {e['valor']})")

def correr_test():
    test_constante()
    test_variable()

if __name__ == "__main__":
    correr_test()
