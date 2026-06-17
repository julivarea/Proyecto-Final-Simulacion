import matplotlib.pyplot as plt
import os

def plot_estados(trazas, info_sim, out_dir="data/graficos/"):
    os.makedirs(out_dir, exist_ok=True)
    
    # Recolectar todos los instantes de tiempo donde hubo algún cambio
    tiempos = set()
    if trazas.get("caudal_real"):
        tiempos.update([t for t, _ in trazas["caudal_real"]])
    if trazas.get("desvio"):
        tiempos.update([t for t, _ in trazas["desvio"]])
        
    tiempos = sorted(list(tiempos))
    if not tiempos:
        return

    # Función auxiliar para saber el valor de una métrica en un tiempo 't'
    def get_val_at_t(serie, t):
        val_actual = 0.0
        for t_i, v_i in serie:
            if t_i <= t:
                val_actual = v_i
            else:
                break
        return val_actual

    estados = []
    
    # Determinar el estado lógico de la bomba en cada instante de tiempo
    for t in tiempos:
        caudal = get_val_at_t(trazas.get("caudal_real", []), t)
        desvio = get_val_at_t(trazas.get("desvio", []), t)
        
        if caudal == 0.0:
            estados.append(0) # ESTADO 0: Detenida / Apagada
        elif desvio > 0.0:
            estados.append(2) # ESTADO 2: Anomalía (Infundiendo pero con desvío)
        else:
            estados.append(1) # ESTADO 1: Infundiendo Normalmente
            
    plt.figure(figsize=(12, 4)) # Más bajito y alargado, ideal para líneas de tiempo
    
    # step() genera el gráfico escalonado característico de sistemas discretos
    plt.step(tiempos, estados, where='post', color='teal', linewidth=2)
    
    # Colorear el fondo según el estado para que sea súper visual
    plt.fill_between(tiempos, estados, step='post', color='teal', alpha=0.15)
    
    # Configurar el eje Y para que muestre texto en lugar de números
    plt.yticks([0, 1, 2], ["Detenida", "Normal", "Anomalía"])
    plt.ylim(-0.5, 2.5) # Márgenes visuales
    
    plt.title(f"Estado Operativo de la Bomba de Infusión\n{info_sim}")
    plt.xlabel("Tiempo de Simulación (s)")
    plt.grid(True, axis='x', alpha=0.4)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    filepath = os.path.join(out_dir, "plot_estados.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()