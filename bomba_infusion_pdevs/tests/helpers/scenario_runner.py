import sys
import os
import types
import pypdevs

sys.path.append(os.path.dirname(pypdevs.__file__))

from pypdevs.minimal import Simulator, AtomicDEVS
from src.models.coupled.bomba_acoplada import BombaAcoplada
from src.utils.monitor import SimulationMonitor
import src.models.atomic.sensor_flujo as sf

# Evita que heapq falle (TypeError) cuando hay componentes con el mismo timeAdvance
if not hasattr(AtomicDEVS, "__lt__"):
    AtomicDEVS.__lt__ = lambda self, other: id(self) < id(other)

class ScenarioRunner:
    """Runner genérico y reutilizable para escenarios de simulación."""
    
    def __init__(self, seed=42, sim_time=100.0, sensor_noise=0.20, name="Test_Bomba"):
        import random
        random.seed(seed)
        sf.PORCENTAJE_RUIDO_SENSOR = sensor_noise
        
        self.modelo = BombaAcoplada(name=name)
        self.sim_time = sim_time
        # Inyectamos el monitor para recolectar trazas
        self.monitor = SimulationMonitor(self.modelo)
    
    def patch_ordenes(self, ordenes: list[dict]):
        """
        Configura el generador de órdenes con eventos determinísticos.
        Ej: [{"t": 2.0, "caudal": 50.0}, {"t": 20.0, "caudal": 80.0}]
        """
        if not ordenes:
            return
            
        # Ordenamos por tiempo ascendente
        ordenes = sorted(ordenes, key=lambda x: x["t"])
        
        # Estado inicial para la primera orden
        self.modelo.g_om.state["caudalObjetivo"] = ordenes[0]["caudal"]
        self.modelo.g_om.state["sigma"] = ordenes[0]["t"]
        self.modelo.g_om.state["idx_orden"] = 1
        
        def int_trans_mod(self_gom):
            idx = self_gom.state["idx_orden"]
            if idx < len(ordenes):
                delay = ordenes[idx]["t"] - ordenes[idx-1]["t"]
                self_gom.state["caudalObjetivo"] = ordenes[idx]["caudal"]
                self_gom.state["sigma"] = delay
                self_gom.state["idx_orden"] += 1
            else:
                self_gom.state["sigma"] = float('inf')
            return self_gom.state
            
        self.modelo.g_om.intTransition = types.MethodType(int_trans_mod, self.modelo.g_om)

    def patch_sensor_fault(self, t_inicio: float, t_fin: float, caudal_falso: float):
        """Inyecta una falla determinística en el sensor de flujo."""
        sensor_out_orig = self.modelo.sensor.outputFnc
        def sensor_out_mod(self_sensor):
            t_actual = self_sensor.time_last[0] + self_sensor.state["sigma"]
            if t_inicio <= t_actual <= t_fin:
                return {self_sensor.out_caudal_medido: [caudal_falso]}
            return sensor_out_orig()
        self.modelo.sensor.outputFnc = types.MethodType(sensor_out_mod, self.modelo.sensor)

        
    def patch_enfermero(self, t_conf: float = None, silenciar: bool = False):
        """Configura el generador de confirmaciones del enfermero."""
        if silenciar:
            self.modelo.g_ce.state = {"sigma": float('inf')}
            def gce_int(self_gce):
                return self_gce.state
            self.modelo.g_ce.intTransition = types.MethodType(gce_int, self.modelo.g_ce)
        elif t_conf is not None:
            self.modelo.g_ce.state = {"sigma": t_conf}
            def gce_out(self_gce):
                return {self_gce.out_conf: [True]}
            self.modelo.g_ce.outputFnc = types.MethodType(gce_out, self.modelo.g_ce)
            def gce_int(self_gce):
                self_gce.state["sigma"] = float('inf')
                return self_gce.state
            self.modelo.g_ce.intTransition = types.MethodType(gce_int, self.modelo.g_ce)
            def gce_ext(self_gce, inputs):
                self_gce.state["sigma"] -= self_gce.elapsed
                return self_gce.state
            self.modelo.g_ce.extTransition = types.MethodType(gce_ext, self.modelo.g_ce)
            
    def patch_fin_bolsa(self, t_alerta: float):
        """Fuerza la alerta de fin de bolsa en un instante determinístico."""
        self.modelo.g_fb.state = {"sigma": t_alerta}
        def gfb_out(self_gfb):
            return {self_gfb.out_fin_bolsa: [True]}
        self.modelo.g_fb.outputFnc = types.MethodType(gfb_out, self.modelo.g_fb)
        def gfb_int(self_gfb):
            self_gfb.state["sigma"] = float('inf')
            return self_gfb.state
        self.modelo.g_fb.intTransition = types.MethodType(gfb_int, self.modelo.g_fb)
        def gfb_ext(self_gfb, inputs):
            self_gfb.state["sigma"] -= self_gfb.elapsed
            return self_gfb.state
        self.modelo.g_fb.extTransition = types.MethodType(gfb_ext, self.modelo.g_fb)

    def run(self) -> dict:
        """Ejecuta la simulación y retorna las trazas."""
        sim = Simulator(self.modelo)
        sim.setTerminationTime(self.sim_time)
        sim.simulate()
        return self.monitor.get_trazas()
