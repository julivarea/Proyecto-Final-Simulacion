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

def ejecutar_escenario_02():
    # Configuración Determinística del Entorno
    random.seed(42) # Fijamos la semilla para reproducibilidad
    
    # Reducimos el ruido del sensor al 2% para garantizar 
    # que la medición nunca supere la tolerancia del 10%
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    # Instanciación del Modelo Global
    modelo = BombaAcoplada(name="Bomba_Esc_02_Cambio_Orden")

    # Parcheo del Generador de Órdenes (G_om)
    # 1er evento: emitimos exactamente 50.0 ml/h en el segundo 2.0
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

    # EXTRACTOR DE TRAZAS DINÁMICO
    # Inyectamos listas en el estado para guardar los datos del gráfico
    modelo.controlador.state["historial_caudal_obj"] = [(0.0, 0.0)]
    modelo.sensor.state["historial_caudal_real"] = [(0.0, 0.0)]

    # Interceptamos el Controlador para guardar el Caudal Indicado
    ctrl_ext_orig = modelo.controlador.extTransition
    def ctrl_ext_mod(self, inputs):
        res = ctrl_ext_orig(inputs)
        if self.in_orden_medica in inputs:
            tiempo_actual = self.time_last[0] + self.elapsed
            self.state["historial_caudal_obj"].append((tiempo_actual, self.state["caudal_obj"]))
        return res
    modelo.controlador.extTransition = types.MethodType(ctrl_ext_mod, modelo.controlador)

    # Interceptamos el Sensor para guardar el Caudal Real Físico
    sensor_int_orig = modelo.sensor.intTransition
    def sensor_int_mod(self):
        tiempo_actual = self.time_last[0] + self.state["sigma"]
        # Guardamos la lectura real que la bomba tiene en este instante
        self.state["historial_caudal_real"].append((tiempo_actual, self.state["caudal_real_ml_h"]))
        return sensor_int_orig()
    modelo.sensor.intTransition = types.MethodType(sensor_int_mod, modelo.sensor)

    # Configuración del Simulador
    sim = Simulator(modelo)
    
    # Simulamos durante 50 segundos para ver cómo se estabiliza la segunda orden
    sim.setTerminationTime(50.0) 
    
    print("Iniciando simulación: Escenario 2 (Cambio de orden médica)...")
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
    ejecutar_escenario_02()