from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_stochastic_normal_operation():
    """
    Ejecución natural del modelo acoplado utilizando las distribuciones estocásticas.
    Sin monkey-patching. Verifica formalmente safety, liveness y tiempos.
    """
    # 600 segundos (10 minutos) da tiempo a que la exponencial de órdenes (media 300s) dispare.
    runner = ScenarioRunner(sim_time=600.0, seed=42)
    
    # NO aplicamos ningún patch. Dejamos que los atómicos usen su lógica natural.
    trazas = runner.run()
    
    # Evaluación automática de propiedades
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad '{prop_name}' violada en simulación estocástica:\n{resultado.format_violations()}"