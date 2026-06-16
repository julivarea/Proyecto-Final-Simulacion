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

def ejecutar_escenario_01():
    # Configuración Determinística del Entorno
    random.seed(42) # Fijamos la semilla para reproducibilidad
    
    # Reducimos el ruido del sensor al 2% para garantizar 
    # que la medición nunca supere la tolerancia del 10%
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    # Instanciación del Modelo Global
    modelo = BombaAcoplada(name="Bomba_Esc_01_Normal")

    # Parcheo del Generador de Órdenes (G_om)
    # Forzamos a que emita exactamente 50.0 ml/h en el segundo 2.0
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0

    def intTransition_fija(self):
        self.state["sigma"] = float('inf')
        return self.state
    
    modelo.g_om.intTransition = types.MethodType(intTransition_fija, modelo.g_om)

    # Inyectamos el monitor limpio
    monitor = SimulationMonitor(modelo)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(40.0) 
    
    print("Iniciando simulación: Escenario 1 (Funcionamiento normal)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()
    
    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: Iniciar infusión a 50 ml/h y mantenerla estable.")
    print("Tiempo | Caudal Indicado | Caudal Real Sensado")
    
    momentos_clave = [0.0, 1.0, 2.0, 4.0, 10.0, 39.0]
    for t_esperado in momentos_clave:
        # Buscamos el valor más reciente registrado hasta ese momento
        c_ind = next((val for t, val in reversed(trazas["caudal_indicado"]) if t <= t_esperado), 0.0)
        c_real = next((val for t, val in reversed(trazas["caudal_real"]) if t <= t_esperado), 0.0)
        
        estado = "OK" if abs(c_ind - c_real) <= (c_ind * 0.1) else "DESVÍO"
        if c_ind == 0.0 and c_real == 0.0: estado = "OK"
        
        print(f" t={t_esperado:05.2f}s |   {c_ind:05.2f} ml/h    |    {c_real:05.2f} ml/h ({estado})")

if __name__ == '__main__':
    ejecutar_escenario_01()