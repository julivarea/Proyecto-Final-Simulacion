import pytest
from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

# Parametrizamos con 10 semillas arbitrarias
@pytest.mark.parametrize("seed", [10, 42, 99, 1024, 2048, 777, 13, 88, 500, 9999])
def test_stochastic_multiple_seeds(seed):
    """
    Somete la bomba a 10 universos estocásticos distintos.
    Garantiza que el sistema sea robusto sin importar el orden de los eventos aleatorios.
    """
    runner = ScenarioRunner(sim_time=400.0, seed=seed)
    trazas = runner.run()
    
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Violación con SEED {seed} en propiedad '{prop_name}':\n{resultado.format_violations()}"