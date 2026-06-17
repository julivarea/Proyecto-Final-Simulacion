import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.generador_conf import GeneradorConfirmaciones
from tests.helpers.testing_utils import Recolector

class MockGenConfModel(CoupledDEVS):
    def __init__(self, name="MockGenConfModel"):
        super().__init__(name)
        self.gen = self.addSubModel(GeneradorConfirmaciones())
        self.rec = self.addSubModel(Recolector("Rec_conf"))
        self.connectPorts(self.gen.out_conf, self.rec.in_port)

def test_generador_confirmaciones():
    """
    Test del Generador de Confirmaciones (G_ce).
    Comportamiento esperado:
    - Debe emitir señales 'confirmacionEnfermero' aleatorias (distribución exponencial).
    - Representa la validación o silenciado de alarmas por parte del personal médico.
    - Se registra la cantidad de confirmaciones en un período de 360 segundos.
    """
    modelo = MockGenConfModel()
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

    assert len(eventos) > 0, "El generador de confirmaciones debería emitir eventos en 360 segundos"
    for e in eventos:
        assert e['valor'] == "confirmacionEnfermero", "El evento emitido debe ser 'confirmacionEnfermero'"
