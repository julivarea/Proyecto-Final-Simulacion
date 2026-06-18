import sys
import os

# Asegurar que se importan los módulos locales correctamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.helpers.scenario_runner import ScenarioRunner

def generar_traza():
    print("Iniciando simulación estocástica (10 minutos)...")
    # Mismos parámetros que test_stochastic_normal_operation
    runner = ScenarioRunner(sim_time=600.0, seed=42, name="Analisis_Estocastico")
    
    # Ejecutamos la simulación
    trazas = runner.run()
    
    # Exportamos la traza al archivo de texto
    output_path = "analisis_traza.txt"
    runner.export_trace_log(output_path)
    print(f"\nSimulación completada. Revisa el archivo '{output_path}' para ver todo lo sucedido.")

if __name__ == "__main__":
    generar_traza()
