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
    TIEMPO_SIMULACION = 1800.0 # 30 minutos

    print("==================================================")
    print(f"INICIANDO ANÁLISIS ESTOCÁSTICO ({TIEMPO_SIMULACION} segundos)")
    print("==================================================")
    
    SEED = 42
    
    import src.models.atomic.sensor_flujo as sf
    ruido_actual = sf.PORCENTAJE_RUIDO_SENSOR
    
    INFO_SIMULACION = f"Escenario: Operación Larga Estocástica | Seed: {SEED} | T. Sim: {TIEMPO_SIMULACION}s | Ruido Sensor: {ruido_actual*100}%"
    
    # 1. Ejecutar Simulación
    print("\n[1/4] Corriendo simulación DEVS (esto puede tomar unos segundos)...")
    runner = ScenarioRunner(sim_time=TIEMPO_SIMULACION, seed=SEED)
    trazas = runner.run()
    print("✓ Simulación finalizada con éxito.")
    
    # 2. Extraer Métricas
    print("\n[2/4] Calculando métricas de rendimiento...")
    metricas = SimulationMetrics(trazas, TIEMPO_SIMULACION)
    print(metricas.resumen())
    
    # 3. Generar Gráficos
    print("\n[3/4] Generando gráficos de análisis...")
    import shutil
    proyecto_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    graficos_dir = os.path.join(proyecto_dir, "data", "graficos")
    os.makedirs(graficos_dir, exist_ok=True)

    plot_caudales(trazas, INFO_SIMULACION, out_dir=graficos_dir)
    plot_desvios(trazas, INFO_SIMULACION, out_dir=graficos_dir)
    plot_alarmas(trazas, INFO_SIMULACION, out_dir=graficos_dir)
    plot_estados(trazas, INFO_SIMULACION, out_dir=graficos_dir)
    
    # Copiar gráficos automáticamente a la carpeta de LaTeX para compilar el PDF actualizado
    latex_images_dir = os.path.join(os.path.dirname(proyecto_dir), "latex", "images")
    if os.path.exists(latex_images_dir):
        print(f"-> Copiando gráficos actualizados a la carpeta de LaTeX: {latex_images_dir}")
        for grafico in ["plot_caudales.png", "plot_desvios.png", "plot_alarmas.png", "plot_estados.png"]:
            src_path = os.path.join(graficos_dir, grafico)
            if os.path.exists(src_path):
                shutil.copy(src_path, os.path.join(latex_images_dir, grafico))
        print("✓ Gráficos copiados con éxito a la carpeta de LaTeX.")
    else:
        print(f"[Aviso] No se encontró el directorio de imágenes de LaTeX en {latex_images_dir}")
    
    # 4. Finalizar
    print(f"\n[4/4] ¡Listo! Todos los gráficos fueron guardados en '{graficos_dir}'")
    print("==================================================")

if __name__ == "__main__":
    main()