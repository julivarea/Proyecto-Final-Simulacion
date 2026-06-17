import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_02_cambio_orden():
    """
    Escenario 2: Cambio de orden médica.
    Objetivo: Iniciar a 50 ml/h, y a los 20s cambiar orden a 80 ml/h.
    """
    runner = ScenarioRunner(sim_time=50.0, sensor_noise=0.02, name="Test_Bomba_Esc_02_Cambio")
    runner.patch_ordenes([
        {"t": 2.0, "caudal": 50.0},
        {"t": 20.0, "caudal": 80.0}
    ])
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    ajustes = [e for e in eventos if e["evento"] == "NUEVA_ORDEN"]
    assert len(ajustes) >= 2
    assert abs(ajustes[1]["tiempo"] - 20.0) <= 2.0
