from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.generador_conf import GeneradorConfirmaciones
from tests.testing_utils import Recolector

class TestGenConf(CoupledDEVS):
    def __init__(self, name="TestGenConf"):
        super().__init__(name)
        self.gen = self.addSubModel(GeneradorConfirmaciones())
        self.rec = self.addSubModel(Recolector("Rec_conf"))
        self.connectPorts(self.gen.out_conf, self.rec.in_port)

def correr_test():
    """
    Test del Generador de Confirmaciones (G_ce).
    Comportamiento esperado:
    - Debe emitir señales 'confirmacionEnfermero' aleatorias (distribución exponencial).
    - Representa la validación o silenciado de alarmas por parte del personal médico.
    - Se registra la cantidad de confirmaciones en un período de 360 segundos.
    """
    modelo = TestGenConf()
    sim = Simulator(modelo)
    sim.setTerminationTime(360.0)
    sim.simulate()

    eventos = modelo.rec.state["eventos"]
    print(f"\n{'='*60}")
    print("TEST: GENERADOR DE CONFIRMACIONES (360s)")
    print(f"{'='*60}")
    print(f"  Confirmaciones emitidas: {len(eventos)}")
    for e in eventos[:3]:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | Valor: {e['valor']}")
    if len(eventos) > 3: print("    ... (truncado)")

if __name__ == "__main__":
    correr_test()
