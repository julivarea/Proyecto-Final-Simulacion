from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_stochastic_absent_nurse():
    """
    Dinámica natural, pero el enfermero jamás confirma.
    Asegura que cualquier alarma que salte naturalmente se repetirá ad-infinitum
    y que la bomba eventualmente quedará en Bloqueo Crítico Seguro.
    """
    runner = ScenarioRunner(sim_time=800.0, seed=77)
    runner.patch_enfermero(silenciar=True) # Único patch: silenciar al entorno humano
    
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Fallo con ENFERMERO AUSENTE ({prop_name}):\n{resultado.format_violations()}"