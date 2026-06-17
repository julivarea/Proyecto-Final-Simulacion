import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.registrador import RegistradorEventos
from tests.helpers.testing_utils import GeneradorManual

class MockRegistradorModel(CoupledDEVS):
    def __init__(self, name="MockRegistradorModel"):
        super().__init__(name)

        cronograma_eventos = [
            {"delay": 5.0, "valor": "ALERTA: Bolsa Vacía"},
            {"delay": 15.0, "valor": "COMANDO: Detener bomba"},
            {"delay": 10.0, "valor": "INFO: Reanudar bomba"},
            {"delay": 1000.0, "valor": "DUMMY"}
        ]
        
        self.gen_eventos = self.addSubModel(GeneradorManual("GenEventos", cronograma_eventos))
        self.registrador = self.addSubModel(RegistradorEventos("Registrador"))

        self.connectPorts(self.gen_eventos.out_port, self.registrador.in_registrar)

def test_registrador():
    """
    Test del Registrador de Eventos (R_e).
    Comportamiento esperado:
    - Componente pasivo (sigma = INFINITY), sólo reacciona ante entradas externas.
    - Se inyectan eventos manuales en tiempos absolutos t=5s, t=20s y t=30s.
    - Se inyecta un evento "DUMMY" lejano (t=1030s) para evitar el error de "heap vacío" de PyPDEVS.
    - El historial resultante debe almacenar los 3 primeros eventos con sus marcas de tiempo exactas.
    """
    modelo_reg = MockRegistradorModel()
    sim = Simulator(modelo_reg)
    sim.setTerminationTime(40.0)
    sim.simulate()

    historial = modelo_reg.registrador.state["historial"]

    print(f"\n{'='*60}")
    print("TEST: REGISTRADOR DE EVENTOS (40s)")
    print(f"{'='*60}")
    print(f"  Eventos inyectados manualmente. Esperados en t=5.0s, t=20.0s y t=30.0s.")
    print(f"  Cantidad de eventos registrados: {len(historial)}")
    print(f"\n  Historial recuperado luego de la simulación:")
    for entrada in historial:
        print(f"    - Tiempo: {entrada['tiempo']:>5.2f}s | Evento: {entrada['evento']}")

    assert len(historial) == 3, "El historial debe contener 3 eventos (ignorando el DUMMY fuera del tiempo de simulación)"
    
    assert historial[0]['tiempo'] == 5.0 and historial[0]['evento'] == "ALERTA: Bolsa Vacía"
    assert historial[1]['tiempo'] == 20.0 and historial[1]['evento'] == "COMANDO: Detener bomba"
    assert historial[2]['tiempo'] == 30.0 and historial[2]['evento'] == "INFO: Reanudar bomba"
