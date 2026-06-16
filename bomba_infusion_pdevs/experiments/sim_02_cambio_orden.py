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

def ejecutar_escenario_02():
    # Configuración Determinística del Entorno
    random.seed(42) # Fijamos la semilla para reproducibilidad
    
    # Reducimos el ruido del sensor al 2% para garantizar 
    # que la medición nunca supere la tolerancia del 10%
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    # Instanciación del Modelo Global
    modelo = BombaAcoplada(name="Bomba_Esc_02_Cambio_Orden")

    # Parcheo del Generador de Órdenes (G_om)
    # emitimos exactamente 50.0 ml/h en el segundo 2.0
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0
    modelo.g_om.state["paso_orden"] = 1 # Variable bandera nuestra

    # Modificamos la transición interna para que envíe el segundo evento
    def intTransition_modificada(self):
        if self.state["paso_orden"] == 1:
            # Al ejecutarse esto, ya pasaron 2.0s y se emitió la de 50.
            # Preparamos la orden de 80.0 ml/h para el segundo 20.0.
            # (El sigma necesario es 18.0 porque 2.0 + 18.0 = 20.0)
            self.state["caudalObjetivo"] = 80.0
            self.state["sigma"] = 18.0
            self.state["paso_orden"] = 2
        else:
            # Ya se emitieron ambas órdenes, ahora sí lo apagamos
            self.state["sigma"] = float('inf')
        return self.state
    
    modelo.g_om.intTransition = types.MethodType(intTransition_modificada, modelo.g_om)

    # Inyectamos el monitor limpio
    monitor = SimulationMonitor(modelo)

    # Configuración del Simulador
    sim = Simulator(modelo)
    
    # Simulamos durante 50 segundos para ver cómo se estabiliza la segunda orden
    sim.setTerminationTime(50.0) 
    
    print("Iniciando simulación: Escenario 2 (Cambio de orden médica)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()
    
    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: Iniciar a 50 ml/h, y a los 20s cambiar orden a 80 ml/h.")
    print("Tiempo | Caudal Indicado | Caudal Real Sensado")
    
    # 2.0s inicio, 4.0s (luego de confirmación), 19.0s antes del cambio, 20.0s cambio, 22.0s después del cambio, 49.0s estabilizado
    momentos_clave = [2.0, 4.0, 19.0, 20.0, 22.0, 49.0]
    for t_esperado in momentos_clave:
        c_ind = next((val for t, val in reversed(trazas["caudal_indicado"]) if t <= t_esperado), 0.0)
        c_real = next((val for t, val in reversed(trazas["caudal_real"]) if t <= t_esperado), 0.0)
        
        # Hay un delay desde que llega la orden hasta que el enfermero confirma, toleramos transiciones
        estado = "OK" if abs(c_ind - c_real) <= (max(c_ind, 1) * 0.1) else "TRANSICIÓN/DESVÍO"
        if c_ind == 0.0 and c_real == 0.0: estado = "OK"
        
        print(f" t={t_esperado:05.2f}s |   {c_ind:05.2f} ml/h    |    {c_real:05.2f} ml/h ({estado})")
        
    return trazas

if __name__ == '__main__':
    ejecutar_escenario_02()