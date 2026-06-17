import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_05_desvio_mayor():
    """
    Escenario 5: Desvío mayor corregido a tiempo.
    Objetivo: Falla mayor (>10%). Emite ALARMA MEDIA a los 5s de persistencia.
    """
    runner = ScenarioRunner(sim_time=40.0, sensor_noise=0.02, name="Test_Bomba_Esc_05_Desvio_Mayor")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    # Desvío del 30% -> 65 ml/h desde t=20s a t=28.5s
    runner.patch_sensor_fault(t_inicio=20.0, t_fin=28.5, caudal_falso=65.0)
    runner.patch_enfermero(silenciar=True)
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    alarmas = [e for e in eventos if e["evento"] == "ALARMA_MEDIA"]
    assert len(alarmas) == 1
    assert alarmas[0]["tiempo"] == pytest.approx(25.0, abs=2.0)
