import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_sim_06_fin_bolsa():
    """
    Escenario 6: Fin de bolsa de infusión.
    Objetivo: Fuerza el evento de fin de bolsa a los 20s. Verifica alarma y detención.
    """
    runner = ScenarioRunner(sim_time=90.0, sensor_noise=0.02, name="Test_Bomba_Esc_06_Fin_Bolsa")
    runner.patch_ordenes([{"t": 2.0, "caudal": 50.0}])
    # Desfasado a 20.1 para no chocar con el tick 20.0 del sensor de caudal
    runner.patch_fin_bolsa(t_alerta=20.1)
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló:\n{resultado.format_violations()}"
        
    eventos = trazas["eventos_logicos"]
    fin_bolsa = [e for e in eventos if e["evento"] == "FIN_BOLSA_DETECTADO"]
    assert len(fin_bolsa) == 1
    assert fin_bolsa[0]["tiempo"] == 20.1
