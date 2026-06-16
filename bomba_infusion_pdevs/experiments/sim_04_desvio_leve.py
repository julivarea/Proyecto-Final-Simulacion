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

def ejecutar_escenario_04():
    # Configuración Determinística
    random.seed(42)
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    modelo = BombaAcoplada(name="Bomba_Esc_04_Desvio_Leve")

    # G_om emite 50.0 ml/h en t=2.0s y se apaga
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0
    def intTransition_fija(self):
        self.state["sigma"] = float('inf')
        return self.state
    modelo.g_om.intTransition = types.MethodType(intTransition_fija, modelo.g_om)

    # Inyectamos el monitor limpio para extraer trazas automáticamente
    monitor = SimulationMonitor(modelo)

    # Inyección de Falla en el Sensor (Mantenemos esto porque define el escenario)
    # Sobrescribimos la salida para simular una perturbación física
    sensor_out_orig = modelo.sensor.outputFnc
    def sensor_out_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        # Falla: el caudal medido sube a 60.0 ml/h entre los segs 20 y 23.5
        if 20.0 <= tiempo_actual <= 23.5:
            return {self.out_caudal_medido: [60.0]}
        return sensor_out_orig()
    modelo.sensor.outputFnc = types.MethodType(sensor_out_mod, modelo.sensor)

    # Interceptamos transición interna para que el sensor asimile la falla internamente también (para gráficas)
    sensor_int_orig = modelo.sensor.intTransition
    def sensor_int_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        res = sensor_int_orig() # original, llama al monitor inyectado también
        if 20.0 <= tiempo_actual <= 23.5:
            # Sobrescribimos la traza del monitor con el valor con falla
            monitor.trazas_caudal_real[-1] = (tiempo_actual, 60.0)
        return res
    modelo.sensor.intTransition = types.MethodType(sensor_int_mod, modelo.sensor)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(30.0) 
    
    print("Iniciando simulación: Escenario 4 (Desvío leve tolerado)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()

    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: Tolerancia a fallas leves. A los 20s ocurre un desvío mayor al 10% que dura 3.5s (menor al límite de 5s).")
    print("Verificación: El contador de desvío debe subir pero NO se debe emitir ALARMA_MEDIA.")
    print("Tiempo | Caudal Indicado | Caudal Real Sensado | Segundos de Desvío Acumulado")
    
    momentos_clave = [19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
    for t_esperado in momentos_clave:
        c_ind = next((val for t, val in reversed(trazas["caudal_indicado"]) if t <= t_esperado), 0.0)
        c_real = next((val for t, val in reversed(trazas["caudal_real"]) if t <= t_esperado), 0.0)
        desv = next((val for t, val in reversed(trazas["desvio"]) if t <= t_esperado), 0.0)
        estado = "FALLA INYECTADA" if 20.0 <= t_esperado <= 23.5 else "OK"
        print(f" t={t_esperado:05.2f}s |   {c_ind:05.2f} ml/h    |    {c_real:05.2f} ml/h       | {desv:.1f} s ({estado})")

if __name__ == '__main__':
    ejecutar_escenario_04()