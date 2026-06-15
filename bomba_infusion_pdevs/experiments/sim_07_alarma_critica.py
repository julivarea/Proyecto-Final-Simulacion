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

    # EXTRACTOR DE TRAZAS DINÁMICO (Para M_a)
    modelo.alarmas.state["historial_emisiones"] = []
    
    # Interceptamos el Módulo de Alarmas para ver cuándo chilla
    ma_out_orig = modelo.alarmas.outputFnc
    def ma_out_mod(self):
        res = ma_out_orig()
        if self.out_alarma in res:
            tiempo_actual = self.time_last[0] + self.state["sigma"]
            self.state["historial_emisiones"].append((tiempo_actual, res[self.out_alarma][0]))
        return res
    modelo.alarmas.outputFnc = types.MethodType(ma_out_mod, modelo.alarmas)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(85.0) # Simulamos hasta el t=85 para ver varias repeticiones
    
    print("Iniciando simulación: Escenario 7 (Alarma crítica no confirmada)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    print("--- Registro de Eventos Lógicos (Auditoría) ---")
    historial = modelo.registrador.state["historial"]
    if not historial:
        print("No se registraron eventos.")
    else:
        for registro in historial:
            print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Dinámica del Módulo de Alarmas ---")
    print("Historial de emisiones físicas hacia el entorno hospitalario:")
    for t, alarma in modelo.alarmas.state["historial_emisiones"]:
        print(f" t={t:05.2f}s -> Emite Sonido/Luz: {alarma}")

if __name__ == '__main__':
    ejecutar_escenario_07()