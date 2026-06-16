import os
import sys
import types
import random
import pypdevs

sys.path.append(os.path.dirname(pypdevs.__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pypdevs.minimal import Simulator
from src.models.coupled.bomba_acoplada import BombaAcoplada
import src.models.atomic.sensor_flujo as sf
from src.utils.monitor import SimulationMonitor

def ejecutar_escenario_03():
    # Configuración Determinística del Entorno
    random.seed(42)
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    # Instanciación del Modelo Global
    modelo = BombaAcoplada(name="Bomba_Esc_03_Detencion")

    # Parcheo del Generador de Órdenes (G_om)
    # 1er evento: encendemos la bomba a 50.0 ml/h en el segundo 2.0
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0
    modelo.g_om.state["paso_orden"] = 1

    # Modificamos la transición interna para enviar la orden de detención
    def intTransition_modificada(self):
        if self.state["paso_orden"] == 1:
            # En el segundo 20.0 (18s después), enviamos caudal 0.0
            self.state["caudalObjetivo"] = 0.0
            self.state["sigma"] = 18.0
            self.state["paso_orden"] = 2
        else:
            # Apagamos el generador
            self.state["sigma"] = float('inf')
        return self.state
    
    modelo.g_om.intTransition = types.MethodType(intTransition_modificada, modelo.g_om)

    # Inyectamos el monitor limpio
    monitor = SimulationMonitor(modelo)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(35.0) 
    
    print("Iniciando simulación: Escenario 3 (Detención por orden médica)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()
    
    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: Iniciar a 50 ml/h, y a los 20s apagar la bomba (orden 0 ml/h).")
    print("Tiempo | Caudal Indicado | Caudal Real Sensado")
    
    # 2.0s orden, 4.0s (luego de confirmación), 19.0s antes del paro, 20.0s orden de paro, 22.0s después del paro, 34.0s final
    momentos_clave = [2.0, 4.0, 19.0, 20.0, 22.0, 34.0]
    for t_esperado in momentos_clave:
        c_ind = next((val for t, val in reversed(trazas["caudal_indicado"]) if t <= t_esperado), 0.0)
        c_real = next((val for t, val in reversed(trazas["caudal_real"]) if t <= t_esperado), 0.0)
        
        estado = "OK" if abs(c_ind - c_real) <= (max(c_ind, 1) * 0.1) else "TRANSICIÓN/DESVÍO"
        if c_ind == 0.0 and c_real == 0.0: estado = "OK"
        print(f" t={t_esperado:05.2f}s |   {c_ind:05.2f} ml/h    |    {c_real:05.2f} ml/h ({estado})")
        
    return trazas

if __name__ == '__main__':
    ejecutar_escenario_03()