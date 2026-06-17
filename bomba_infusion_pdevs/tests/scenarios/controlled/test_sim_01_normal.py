import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_01_normal():
    """
    Escenario 1: Funcionamiento normal.
    Objetivo: Iniciar infusión a 50 ml/h y mantenerla estable.
    """
    runner = ScenarioRunner(sim_time=40.0, sensor_noise=0.02, name="Test_Bomba_Esc_01_Normal")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    assert any(e["evento"] == "NUEVA_ORDEN" and e["tiempo"] == 2.0 for e in eventos)
    assert not any(e["evento"].startswith("ALARMA") for e in eventos)
