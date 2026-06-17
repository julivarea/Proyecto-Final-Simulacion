import sys
import os

# Asegurar importaciones correctas desde el root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.helpers.scenario_runner import ScenarioRunner
from src.utils.metrics import SimulationMetrics
from analysis.plot_caudales import plot_caudales
from analysis.plot_desvios import plot_desvios
from analysis.plot_alarmas import plot_alarmas
from analysis.plot_estados import plot_estados

def main():
    print("==================================================")
    print("INICIANDO ANÁLISIS ESTOCÁSTICO DE LARGA DURACIÓN")
    print("==================================================")
    
    TIEMPO_SIMULACION = 1800.0 # 30 minutos
    SEED = 42
    RUIDO = 0.25 # Ruido un poco superior al normal para forzar fallas
    
    INFO_SIMULACION = f"Escenario: Operación Larga Estocástica | Seed: {SEED} | T. Sim: {TIEMPO_SIMULACION}s | Ruido Sensor: {RUIDO*100}%"
    
    # 1. Ejecutar Simulación
    print("\n[1/4] Corriendo simulación DEVS (esto puede tomar unos segundos)...")
    runner = ScenarioRunner(sim_time=TIEMPO_SIMULACION, sensor_noise=RUIDO, seed=SEED)
    trazas = runner.run()
    print("✓ Simulación finalizada con éxito.")
    
    # 2. Extraer Métricas
    print("\n[2/4] Calculando métricas de rendimiento...")
    metricas = SimulationMetrics(trazas, TIEMPO_SIMULACION)
    print(metricas.resumen())
    
    # 3. Generar Gráficos
    print("\n[3/4] Generando gráficos de análisis...")
    plot_caudales(trazas, INFO_SIMULACION)
    plot_desvios(trazas, INFO_SIMULACION)
    plot_alarmas(trazas, INFO_SIMULACION)
    plot_estados(trazas, INFO_SIMULACION)
    
    # 4. Finalizar
    print("\n[4/4] ¡Listo! Todos los gráficos fueron guardados en 'data/graficos/'")
    print("==================================================")

if __name__ == "__main__":
    main()