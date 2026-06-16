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

    # Inyectamos el monitor limpio para extraer trazas automáticamente
    monitor = SimulationMonitor(modelo)

    # Configuración del Simulador
    sim = Simulator(modelo)
    sim.setTerminationTime(85.0) # Simulamos hasta el t=85 para ver la detención en el 80.
    
    print("Iniciando simulación: Escenario 6 (Fin de Bolsa y confirmación)...")
    sim.simulate()
    print("Simulación finalizada.\n")

    # Extracción de Resultados
    trazas = monitor.get_trazas()

    print("--- Eventos Lógicos (Auditoría) ---")
    historial = trazas["eventos_logicos"]
    for registro in historial:
        print(f"Tiempo: {registro['tiempo']:05.2f}s | Evento: {registro['evento']}")

    print("\n--- Momentos Clave de la Simulación ---")
    print("Objetivo: El sensor detecta fin de bolsa a los 20s. Debe emitir ALARMA_BAJA y dar 60s antes de detener la bomba.")
    print("Tiempo | Caudal Real | Segundos desde Fin de Bolsa | Estado esperado")
    
    momentos_clave = [19.0, 20.0, 21.0, 79.0, 80.0, 81.0]
    for t_esperado in momentos_clave:
        c_real = next((val for t, val in reversed(trazas["caudal_real"]) if t <= t_esperado), 0.0)
        seg_b = next((val for t, val in reversed(trazas["fin_bolsa"]) if t <= t_esperado), 0.0)
        
        estado = "OK (Bolsa llena)"
        if 20.0 <= t_esperado < 80.0:
            estado = "ALARMA BAJA (Esperando confirmación o fin de gracia)"
        elif t_esperado >= 80.0:
            estado = "DETENIDA (Pasaron 60s sin nueva bolsa)"
            
        print(f" t={t_esperado:05.2f}s |  {c_real:05.2f} ml/h  | {seg_b:04.1f} s                       | {estado}")
        
    return trazas

if __name__ == '__main__':
    ejecutar_escenario_06()