import matplotlib.pyplot as plt
import os

def plot_desvios(trazas, info_sim, out_dir="data/graficos/"):
    os.makedirs(out_dir, exist_ok=True)
    
    if not trazas.get("desvio"): return
    t_desv, v_desv = zip(*trazas["desvio"])
    
    plt.figure(figsize=(10, 5))
    plt.step(t_desv, v_desv, where='post', color='purple', linewidth=2, label="Desvío Acumulado")
    
    plt.axhline(y=5.0, color='orange', linestyle='--', label="Umbral Alarma Media (5s)")
    plt.axhline(y=10.0, color='red', linestyle='--', label="Umbral Alarma Crítica (10s)")
    
    plt.title(f"Desviación Persistente del Caudal\n{info_sim}")
    plt.xlabel("Tiempo de Simulación (s)")
    plt.ylabel("Segundos de Desvío Sostenido")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filepath = os.path.join(out_dir, "plot_desvios.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()