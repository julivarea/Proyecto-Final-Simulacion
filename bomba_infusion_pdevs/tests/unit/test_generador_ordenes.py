import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.generador_ordenes import GeneradorOrdenes
from tests.helpers.testing_utils import Recolector

class MockGenOrdenesModel(CoupledDEVS):
    def __init__(self, name="MockGenOrdenesModel"):
        super().__init__(name)
        self.gen = self.addSubModel(GeneradorOrdenes())
        self.rec = self.addSubModel(Recolector("Rec_ordenes"))
        self.connectPorts(self.gen.out_caudal_obj, self.rec.in_port)

def test_generador_ordenes():
    """
    Test del Generador de Órdenes Médicas (G_om).
    Comportamiento esperado:
    - Debe emitir de forma aleatoria (exponencial) órdenes de cambio de caudal.
    - Los caudales enviados deben estar distribuidos de manera uniforme entre 0 y 600 ml/h.
    - Se registran todas las órdenes emitidas durante 3600 segundos (1 hora).
    """
    modelo = MockGenOrdenesModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(3600.0)
    sim.simulate()

    eventos = modelo.rec.state["eventos"]
    print(f"\n{'='*60}")
    print("TEST: GENERADOR DE ÓRDENES MÉDICAS (3600s)")
    print(f"{'='*60}")
    print(f"  Órdenes emitidas: {len(eventos)}")
    for e in eventos[:3]:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | Caudal: {e['valor']:>6.2f} ml/h")
    if len(eventos) > 3: print("    ... (truncado)")
    
    assert len(eventos) > 0, "El generador de órdenes debería emitir eventos en 3600 segundos"
    for e in eventos:
        assert 0.0 <= e['valor'] <= 600.0, "El caudal generado debe estar entre 0.0 y 600.0 ml/h"
