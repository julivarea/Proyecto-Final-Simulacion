from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_stochastic_long_run():
    """
    Simulación larga (30 minutos de tiempo simulado) para verificar estabilidad.
    Garantiza que no hay desbordamientos y las reglas se mantienen.
    """
    runner = ScenarioRunner(sim_time=1800.0, seed=123)
    trazas = runner.run()
    
    # Comprobación de estabilidad
    # Verificamos que las propiedades formales no se rompan a largo plazo
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' falló en LONG RUN:\n{resultado.format_violations()}"
        
    assert len(trazas["eventos_logicos"]) > 0, "No se registraron eventos lógicos en 30 minutos."