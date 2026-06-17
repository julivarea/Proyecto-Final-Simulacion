import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_08_desvio_critico():
    """
    Escenario 8: Desvío crítico confirmado.
    Objetivo: Desvío permanente. Dispara alarma crítica y bloquea la bomba.
    El enfermero confirma la alarma a los 45s.
    """
    runner = ScenarioRunner(sim_time=60.0, sensor_noise=0.02, name="Test_Bomba_Esc_08_Desvio_Critico")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    # Desvío permanente
    runner.patch_sensor_fault(t_inicio=20.0, t_fin=200.0, caudal_falso=65.0)
    # Enfermero confirma a los 45s
    runner.patch_enfermero(t_conf=45.0)
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    alarmas_crit = [e for e in eventos if e["evento"] == "ALARMA_CRITICA"]
    assert len(alarmas_crit) > 0
    
    confirmaciones = [e for e in eventos if e["evento"] == "AJUSTE_CAUDAL"]
    assert any(abs(c["tiempo"] - 45.0) <= 2.0 for c in confirmaciones)
