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

def ejecutar_escenario_07():
    # Configuración Determinística
    random.seed(42)
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    modelo = BombaAcoplada(name="Bomba_Esc_07_Alarma_Critica")

    # G_om emite 50.0 ml/h en t=2.0s y se apaga
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0
    def gom_int(self):
        self.state["sigma"] = float('inf')
        return self.state
    modelo.g_om.intTransition = types.MethodType(gom_int, modelo.g_om)

    # Silenciamos al Enfermero: Forzamos a que G_ce nunca actúe
    modelo.g_ce.state = {"sigma": float('inf')}
    def gce_int(self):
        return self.state
    modelo.g_ce.intTransition = types.MethodType(gce_int, modelo.g_ce)

    # Inyectamos Falla Sostenida y Permanente en el Sensor desde t=20.0s
    sensor_out_orig = modelo.sensor.outputFnc
    def sensor_out_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        # Falla: el caudal medido sube a 65.0 ml/h (30% de desvío)
        if tiempo_actual >= 20.0:
            return {self.out_caudal_medido: [65.0]}
        return sensor_out_orig()
    modelo.sensor.outputFnc = types.MethodType(sensor_out_mod, modelo.sensor)

    modelo.sensor.outputFnc = types.MethodType(sensor_out_mod, modelo.sensor)

    # Inyectamos el monitor limpio para extraer trazas (incluidas las de alarma)
    monitor = SimulationMonitor(modelo)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(85.0) # Simulamos hasta el t=85 para ver varias repeticiones
    
    print("Iniciando simulación: Escenario 7 (Alarma crítica no confirmada)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()

    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: Ocurre una falla sostenida. Tras 5s emite ALARMA_MEDIA. Si en 5s no se confirma, pasa a ALARMA_CRITICA.")
    print("Como el enfermero está silenciado, la ALARMA_CRITICA no se confirma y debe repetirse cada 10s para molestar.")
    print("Historial de emisiones físicas hacia el entorno hospitalario:")
    
    emisiones = trazas["emisiones_alarma"]
    if not emisiones:
        print(" No hubo emisiones de alarma.")
    else:
        for t, alarma in emisiones:
            notas = " (Debe repetirse cada 10s si nadie confirma)" if alarma == "CRITICA" else " (Primera advertencia)"
            print(f" t={t:05.2f}s -> Emite Sonido/Luz: {alarma}{notas}")
            
    return trazas

if __name__ == '__main__':
    ejecutar_escenario_07()