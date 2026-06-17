from tests.helpers.scenario_runner import ScenarioRunner
from tests.helpers.property_checkers import check_all_properties

def test_stochastic_extreme_sensor_noise():
    """
    Sube el ruido del sensor al 45% (sensor deteriorado).
    Las desviaciones ocurrirán constantemente de forma natural (estocástica).
    El controlador debe ser capaz de interceptarlas y escalar las alarmas sin violar Safety.
    """
    runner = ScenarioRunner(sim_time=500.0, sensor_noise=0.45, seed=42)
    trazas = runner.run()
    resultados = check_all_properties(trazas)
    
    for prop_name, resultado in resultados.items():
        assert resultado.passed, f"Propiedad violada bajo RUIDO EXTREMO ({prop_name}):\n{resultado.format_violations()}"