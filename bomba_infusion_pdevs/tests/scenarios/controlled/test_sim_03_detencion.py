import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_03_detencion():
    """
    Escenario 3: Detención manual.
    Objetivo: Iniciar a 50 ml/h, y a los 30s detener la bomba (orden de 0 ml/h).
    """
    runner = ScenarioRunner(sim_time=50.0, sensor_noise=0.02, name="Test_Bomba_Esc_03_Detencion")
    runner.patch_ordenes([
        {"t": 2.0, "caudal": 50.0},
        {"t": 30.0, "caudal": 0.0}
    ])
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    detenciones = [e for e in eventos if e["evento"] == "DETENCION_MEDICA"]
    assert len(detenciones) == 1
    assert detenciones[0]["tiempo"] == 30.0
