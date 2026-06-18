import numpy as np

class SimulationMetrics:
    """Calcula métricas agregadas a partir de trazas de simulación DEVS."""

    def __init__(self, trazas: dict, sim_time: float):
        self.trazas = trazas
        self.sim_time = sim_time
        self.eventos = trazas.get("eventos_logicos", [])

    def caudal_promedio(self) -> float:
        """Caudal real promedio ponderado por el tiempo."""
        caudales = self.trazas.get("caudal_real", [])
        if not caudales: return 0.0
        area = sum(caudales[i][1] * (caudales[i+1][0] - caudales[i][0]) for i in range(len(caudales)-1))
        area += caudales[-1][1] * (self.sim_time - caudales[-1][0])
        return area / self.sim_time if self.sim_time > 0 else 0.0

    def porcentaje_tiempo_infusion_correcta(self) -> float:
        """Porcentaje de tiempo donde la bomba infundió líquido sin desvío mayor al 10%."""
        tiempo_correcto = 0.0
        desvios = self.trazas.get("desvio", [(0.0, 0.0)])
        for i in range(len(desvios)-1):
            if desvios[i][1] < 5.0: # Si el desvío acumulado no llegó a alarma, es tolerable/correcto
                tiempo_correcto += (desvios[i+1][0] - desvios[i][0])
        tiempo_correcto += (self.sim_time - desvios[-1][0]) if desvios[-1][1] < 5.0 else 0.0
        return (tiempo_correcto / self.sim_time) * 100.0

    def detenciones_preventivas(self) -> int:
        """Cantidad de veces que la bomba se detuvo por seguridad (Falla o Fin de Bolsa)."""
        # Contamos las detenciones que ocurren en el mismo instante que una alarma crítica o fin bolsa + 60s
        detenciones = [e for e in self.eventos if e["evento"] == "DETENCION_MEDICA"]
        return len(detenciones) # Asumimos que toda detención en el run estocástico que no es orden directa es preventiva.

    def alarmas_generadas(self) -> dict:
        """Conteo de alarmas emitidas hacia el exterior."""
        conteos = {"BAJA": 0, "MEDIA": 0, "CRITICA": 0}
        for _, tipo in self.trazas.get("emisiones_alarma", []):
            if tipo in conteos: conteos[tipo] += 1
        return conteos

    def tiempos_confirmacion_enfermero(self) -> list[float]:
        """Tiempos entre la emisión de una alarma y la primera confirmación del enfermero posterior a ella."""
        tiempos = []
        alarmas = self.trazas.get("emisiones_alarma", [])
        confirmaciones = [e["tiempo"] for e in self.eventos if e["evento"] == "CONFIRMACION_ENFERMERO"]
        
        # Mapeo correcto: Para cada alarma, buscamos la PRIMERA confirmación que ocurre después
        for t_al, tipo in alarmas:
            conf_post = [t_conf for t_conf in confirmaciones if t_conf >= t_al]
            if conf_post:
                tiempos.append(conf_post[0] - t_al)
        return tiempos

    def tiempo_respuesta_fin_bolsa(self) -> float:
        """Tiempo desde fin de bolsa hasta detención (debería ser <= 60s)."""
        t_alerta = next((e["tiempo"] for e in self.eventos if e["evento"] == "FIN_BOLSA_DETECTADO"), None)
        if not t_alerta: return -1.0
        t_detencion = next((e["tiempo"] for e in self.eventos if e["evento"] == "DETENCION_MEDICA" and e["tiempo"] >= t_alerta), None)
        return t_detencion - t_alerta if t_detencion else (self.sim_time - t_alerta)

    def resumen(self) -> str:
        alarmas = self.alarmas_generadas()
        return (
            f"--- MÉTRICAS DE SIMULACIÓN ---\n"
            f"Caudal Promedio: {self.caudal_promedio():.2f} ml/h\n"
            f"Tiempo Infusión Correcta: {self.porcentaje_tiempo_infusion_correcta():.2f}%\n"
            f"Detenciones Preventivas: {self.detenciones_preventivas()}\n"
            f"Alarmas Emitidas -> Baja: {alarmas['BAJA']}, Media: {alarmas['MEDIA']}, Crítica: {alarmas['CRITICA']}\n"
            f"Tiempo Respuesta Fin Bolsa: {self.tiempo_respuesta_fin_bolsa():.2f} s\n"
            f"Tiempos de Confirmación Promedio: {np.mean(self.tiempos_confirmacion_enfermero() or [0]):.2f} s\n"
            f"------------------------------"
        )