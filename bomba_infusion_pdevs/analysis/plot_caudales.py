import matplotlib.pyplot as plt
import numpy as np
import os

def plot_caudales(trazas, info_sim, out_dir="data/graficos/"):
    os.makedirs(out_dir, exist_ok=True)
    
    t_obj, v_obj = zip(*trazas["caudal_indicado"]) if trazas["caudal_indicado"] else ([0], [0])
    t_real, v_real = zip(*trazas["caudal_real"]) if trazas["caudal_real"] else ([0], [0])
    t_med, v_med = zip(*trazas["caudal_medido"]) if trazas.get("caudal_medido") else ([0], [0])
    
    # Preparamos las bandas del 10%
    v_obj_array = np.array(v_obj)
    limite_sup = v_obj_array * 1.10
    limite_inf = v_obj_array * 0.90
    
    plt.figure(figsize=(12, 6))
    
    # Graficar mediciones individuales del sensor con ruido en el fondo
    if len(t_med) > 1:
        plt.scatter(t_med, v_med, s=3, color='orange', alpha=0.4, label='Lecturas del Sensor (Señal con Ruido)', zorder=1)
    
    # Step plots para mantener la naturaleza discreta de DEVS
    plt.step(t_obj, v_obj, where='post', label='Caudal Objetivo (Prescripción Médica)', color='blue', linewidth=2, zorder=3)
    plt.step(t_real, v_real, where='post', label='Caudal Real (Entrega Física al Paciente)', color='red', alpha=0.8, linewidth=1.5, zorder=2)
    
    # Bandas de tolerancia
    plt.fill_between(t_obj, limite_inf, limite_sup, step='post', color='blue', alpha=0.1, label='Tolerancia ±10%')
    
    # Marcas de nuevas órdenes
    ordenes = [e["tiempo"] for e in trazas.get("eventos_logicos", []) if e["evento"] == "NUEVA_ORDEN"]
    for t in ordenes:
        plt.axvline(x=t, color='green', linestyle='--', alpha=0.5)

    plt.title(f"Evolución de Caudales\n{info_sim}")
    plt.xlabel("Tiempo de Simulación (s)")
    plt.ylabel("Caudal (ml/h)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filepath = os.path.join(out_dir, "plot_caudales.png")
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()