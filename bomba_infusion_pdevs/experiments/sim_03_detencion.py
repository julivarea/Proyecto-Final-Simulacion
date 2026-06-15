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

    # EXTRACTOR DE TRAZAS DINÁMICO
    modelo.controlador.state["historial_caudal_obj"] = [(0.0, 0.0)]
    modelo.sensor.state["historial_caudal_real"] = [(0.0, 0.0)]

    ctrl_ext_orig = modelo.controlador.extTransition
    def ctrl_ext_mod(self, inputs):
        res = ctrl_ext_orig(inputs)
        if self.in_orden_medica in inputs:
            tiempo_actual = self.time_last[0] + self.elapsed
            self.state["historial_caudal_obj"].append((tiempo_actual, self.state["caudal_obj"]))
        return res
    modelo.controlador.extTransition = types.MethodType(ctrl_ext_mod, modelo.controlador)

    sensor_int_orig = modelo.sensor.intTransition
    def sensor_int_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        self.state["historial_caudal_real"].append((tiempo_actual, self.state["caudal_real_ml_h"]))
        return sensor_int_orig()
    modelo.sensor.intTransition = types.MethodType(sensor_int_mod, modelo.sensor)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(35.0) 
    
    print("Iniciando simulación: Escenario 3 (Detención por orden médica)...")
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

    print("\n--- Muestra de Traza Física para Gráficos ---")
    print("Últimas 5 lecturas del caudal en la tubería del paciente:")
    for t, val in modelo.sensor.state["historial_caudal_real"][-5:]:
        print(f"  t={t:05.2f}s -> {val:.2f} ml/h")

if __name__ == '__main__':
    ejecutar_escenario_03()