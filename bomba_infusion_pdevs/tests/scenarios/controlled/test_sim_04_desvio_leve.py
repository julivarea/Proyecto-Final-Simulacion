import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_04_desvio_leve():
    """
    Escenario 4: Desvío leve transitorio.
    Objetivo: Falla menor (ej 8%) durante 20s. Al estar por debajo del umbral del 10%,
    el sistema corrige sin emitir alarmas.
    """
    runner = ScenarioRunner(sim_time=60.0, sensor_noise=0.02, name="Test_Bomba_Esc_04_Desvio_Leve")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    # Desvío del 8% de 50 es 54 ml/h
    runner.patch_sensor_fault(t_inicio=10.0, t_fin=30.0, caudal_falso=54.0)
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    assert not any(e["evento"].startswith("ALARMA") for e in eventos)
