from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.actuador import ActuadorBomba
from tests.testing_utils import GeneradorManual, Recolector

class TestActuador(CoupledDEVS):
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

def correr_test():
    """
    Test del Actuador de la Bomba (A).
    Comportamiento esperado:
    - Recibe órdenes de cambio de caudal y señales de detención.
    - Aplica una latencia mecánica (distribución Uniforme entre 0 y 0.5s) antes de aplicar el cambio.
    - Se verifica que el tiempo de reacción incluye ese retardo pequeño respecto al tiempo exacto de la orden.
    """
    modelo = TestActuador()
    sim = Simulator(modelo)
    sim.setTerminationTime(60.0)
    sim.simulate()

    eventos = modelo.rec_act.state["eventos"]
    print(f"\n{'='*60}")
    print("TEST: ACTUADOR DE LA BOMBA (60s)")
    print(f"{'='*60}")
    print("  Órdenes enviadas:")
    print("    t=10.0s -> caudal = 300.0 ml/h")
    print("    t=30.0s -> caudal = 600.0 ml/h")
    print("    t=50.0s -> STOP (0.0 ml/h)")
    print("\n  Respuestas del Actuador (con latencia mecánica U(0, 0.5)):")
    for e in eventos:
        print(f"    - Tiempo Real de Salida: {e['tiempo']:>7.3f}s | Caudal Físico: {e['valor']:>6.2f} ml/h")

if __name__ == "__main__":
    correr_test()
