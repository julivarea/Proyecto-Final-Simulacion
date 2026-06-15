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

    # EXTRACTOR DE TRAZAS DINÁMICO
    modelo.controlador.state["historial_caudal_obj"] = [(0.0, 0.0)]
    modelo.controlador.state["historial_desvio"] = []
    modelo.sensor.state["historial_caudal_real"] = [(0.0, 0.0)]

    # Inyección de Falla en el Sensor
    # Sobrescribimos la salida para simular una perturbación física
    sensor_out_orig = modelo.sensor.outputFnc
    def sensor_out_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        # Falla: el caudal medido sube a 60.0 ml/h entre los segs 20 y 23.5
        if 20.0 <= tiempo_actual <= 23.5:
            return {self.out_caudal_medido: [60.0]}
        return sensor_out_orig()
    modelo.sensor.outputFnc = types.MethodType(sensor_out_mod, modelo.sensor)

    # Interceptamos transición interna para guardar las lecturas en la lista
    sensor_int_orig = modelo.sensor.intTransition
    def sensor_int_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        res = sensor_int_orig()
        if 20.0 <= tiempo_actual <= 23.5:
            self.state["historial_caudal_real"].append((tiempo_actual, 60.0))
        else:
            self.state["historial_caudal_real"].append((tiempo_actual, self.state["caudal_medido_ml_h"]))
        return res
    modelo.sensor.intTransition = types.MethodType(sensor_int_mod, modelo.sensor)

    # Interceptamos el Controlador para observar sus variables internas
    ctrl_ext_orig = modelo.controlador.extTransition
    def ctrl_ext_mod(self, inputs):
        res = ctrl_ext_orig(inputs)
        if self.in_orden_medica in inputs:
            tiempo_actual = self.time_last[0] + self.elapsed
            self.state["historial_caudal_obj"].append((tiempo_actual, self.state["caudal_obj"]))
        if self.in_caudal_medido in inputs:
            tiempo_actual = self.time_last[0] + self.elapsed
            # Guardamos cuántos segundos de desvío lleva acumulados
            self.state["historial_desvio"].append((tiempo_actual, self.state["seg_desvio"]))
        return res
    modelo.controlador.extTransition = types.MethodType(ctrl_ext_mod, modelo.controlador)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(30.0) 
    
    print("Iniciando simulación: Escenario 4 (Desvío leve tolerado)...")
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

    print("\n--- Dinámica del Desvío (Variables Internas del Controlador) ---")
    print("Tiempo | Caudal Sensado | Segundos de Desvío Acumulado")
    
    # Armamos un diccionario para buscar rápido el caudal en un t dado
    caudales = {round(t): val for t, val in modelo.sensor.state["historial_caudal_real"]}
    for t, desv in modelo.controlador.state["historial_desvio"]:
        if 18.5 <= t <= 25.5: # Mostramos la ventana donde ocurre y desaparece la falla
            c_real = caudales.get(round(t), 50.0)
            print(f" t={t:05.2f}s |    {c_real:.2f} ml/h  | {desv:.1f} s")

if __name__ == '__main__':
    ejecutar_escenario_04()