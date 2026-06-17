import matplotlib.pyplot as plt
import os

def plot_alarmas(trazas, info_sim, out_dir="data/graficos/"):
    os.makedirs(out_dir, exist_ok=True)
    alarmas = trazas.get("emisiones_alarma", [])
    if not alarmas: return

    tiempos = [t for t, _ in alarmas]
    tipos = [tipo for _, tipo in alarmas]
    
    # Mapeo numérico para graficar
    niveles = {"BAJA": 1, "MEDIA": 2, "CRITICA": 3}
    valores = [niveles[t] for t in tipos]
    colores = {"BAJA": "yellow", "MEDIA": "orange", "CRITICA": "red"}
    c_list = [colores[t] for t in tipos]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # 1. Timeline
    ax1.scatter(tiempos, valores, c=c_list, s=100, edgecolor='black', zorder=5)
    ax1.set_yticks([1, 2, 3])
    ax1.set_yticklabels(["BAJA", "MEDIA", "CRITICA"])
    ax1.set_title("Timeline de Emisión de Alarmas")
    ax1.set_xlabel("Tiempo (s)")
    ax1.grid(True, axis='y', linestyle='--')

    # 2. Histograma/Barras
    conteos = {k: tipos.count(k) for k in niveles.keys()}
    ax2.bar(conteos.keys(), conteos.values(), color=['yellow', 'orange', 'red'], edgecolor='black')
    ax2.set_title("Frecuencia de Alarmas por Tipo")
    ax2.set_ylabel("Cantidad de Emisiones")

    fig.suptitle(info_sim)
    plt.tight_layout()
    
    filepath = os.path.join(out_dir, "plot_alarmas.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()