import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_07_alarma_critica():
    """
    Escenario 7: Alarma crítica no confirmada.
    Objetivo: Desvío permanente sin confirmación. Se bloquea a los 10s y re-notifica alarma cada 10s (tras 30s).
    """
    runner = ScenarioRunner(sim_time=90.0, sensor_noise=0.02, name="Test_Bomba_Esc_07_Alarma_Critica")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    # Desvío permanente
    runner.patch_sensor_fault(t_inicio=20.0, t_fin=200.0, caudal_falso=65.0)
    # Silenciamos al enfermero
    runner.patch_enfermero(silenciar=True)
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    alarmas_crit = [e for e in eventos if e["evento"] == "ALARMA_CRITICA"]
    assert len(alarmas_crit) > 0
    assert alarmas_crit[0]["tiempo"] == pytest.approx(30.0, abs=2.0)
