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

def ejecutar_escenario_06():
    # Configuración Determinística
    random.seed(42)
    sf.PORCENTAJE_RUIDO_SENSOR = 0.02 

    modelo = BombaAcoplada(name="Bomba_Esc_06_Fin_Bolsa")

    # G_om emite 50.0 ml/h en t=2.0s y se apaga
    modelo.g_om.state["caudalObjetivo"] = 50.0
    modelo.g_om.state["sigma"] = 2.0
    def gom_int(self):
        self.state["sigma"] = float('inf')
        return self.state
    modelo.g_om.intTransition = types.MethodType(gom_int, modelo.g_om)

    # Parche G_fb: Forzamos la alerta de Fin de Bolsa en t=20.0s
    modelo.g_fb.state = {"sigma": 20.0}
    def gfb_out(self):
        return {self.out_fin_bolsa: [True]}
    modelo.g_fb.outputFnc = types.MethodType(gfb_out, modelo.g_fb)
    def gfb_int(self):
        self.state["sigma"] = float('inf')
        return self.state
    modelo.g_fb.intTransition = types.MethodType(gfb_int, modelo.g_fb)
    def gfb_ext(self, inputs):
        self.state["sigma"] -= self.elapsed
        return self.state
    modelo.g_fb.extTransition = types.MethodType(gfb_ext, modelo.g_fb)

    # Parche G_ce: Forzamos al enfermero a confirmar en t=25.0s
    modelo.g_ce.state = {"sigma": 25.0}
    def gce_out(self):
        return {self.out_conf: [True]}
    modelo.g_ce.outputFnc = types.MethodType(gce_out, modelo.g_ce)
    def gce_int(self):
        self.state["sigma"] = float('inf')
        return self.state
    modelo.g_ce.intTransition = types.MethodType(gce_int, modelo.g_ce)
    def gce_ext(self, inputs):
        self.state["sigma"] -= self.elapsed
        return self.state
    modelo.g_ce.extTransition = types.MethodType(gce_ext, modelo.g_ce)

    # EXTRACTOR DE TRAZAS DINÁMICO
    modelo.controlador.state["historial_bolsa"] = []
    modelo.sensor.state["historial_caudal_real"] = [(0.0, 0.0)]

    ctrl_ext_orig = modelo.controlador.extTransition
    def ctrl_ext_mod(self, inputs):
        res = ctrl_ext_orig(inputs)
        # Extraemos el cronómetro interno de la bolsa cada vez que el sensor empuja un dato
        if self.in_caudal_medido in inputs:
            tiempo_actual = self.time_last[0] + self.elapsed
            self.state["historial_bolsa"].append((tiempo_actual, self.state["seg_fin_bolsa"]))
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
    sim.setTerminationTime(85.0) # Simulamos hasta el t=85 para ver la detención en el 80.
    
    print("Iniciando simulación: Escenario 6 (Fin de Bolsa y confirmación)...")
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

    print("\n--- Dinámica de Fin de Bolsa (Caudal y Cronómetro) ---")
    print("Tiempo | Caudal Sensado | Segundos de Bolsa Acumulados")
    caudales = {round(t): val for t, val in modelo.sensor.state["historial_caudal_real"]}
    for t, seg_bolsa in modelo.controlador.state["historial_bolsa"]:
        # Mostramos los instantes clave: cuando llega la alerta y cuando se detiene
        if (19.5 <= t <= 21.5) or (78.5 <= t <= 81.5):
            c_real = caudales.get(round(t), 50.0)
            print(f" t={t:05.2f}s |    {c_real:.2f} ml/h  | {seg_bolsa:.1f} s")

if __name__ == '__main__':
    ejecutar_escenario_06()