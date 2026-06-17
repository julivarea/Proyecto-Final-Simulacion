import logging

logger = logging.getLogger(__name__)

class CheckResult:
    def __init__(self, passed: bool, violations: list[str] = None):
        self.passed = passed
        self.violations = violations or []
        
    def format_violations(self) -> str:
        return "\n".join(self.violations)

def format_sim_time(t: float) -> str:
    """Formatea el tiempo interno de simulación a HH:MM:SS."""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def _log_violation(component: str, t: float, message: str) -> str:
    """Genera y loguea un mensaje de violación estandarizado usando tiempo simulado."""
    formatted_msg = f"{format_sim_time(t)} - {component} - {message}"
    logger.error(formatted_msg)
    return formatted_msg

# =========================================================================
# SAFETY PROPERTIES
# =========================================================================

# Propiedad de Safety: La bomba debe interrumpir de inmediato el suministro físico de fluidos si la última prescripción médica recibida indica un caudal igual a cero (detención).
def check_safety_caudal_nulo_tras_detencion(trazas, t_detencion: float, tolerancia=0.1) -> CheckResult:
    violations = []
    for (t, val) in [(t, val) for t, val in trazas["caudal_real"] if t > (t_detencion + 5.0)]:
        if val > tolerancia:
            violations.append(_log_violation("SAFETY", t, f"Caudal real es {val} ml/h habiendo orden de detención previa"))
    return CheckResult(len(violations) == 0, violations)

# Propiedad de Safety: El caudal real no debe exceder en ningún caso el límite máximo de seguridad física (200 ml/h).
def check_safety_caudal_max(trazas, max_caudal=200.0) -> CheckResult:
    violations = []
    for t, val in trazas["caudal_real"]:
        if val > max_caudal:
            violations.append(_log_violation("SAFETY", t, f"Caudal excedió {max_caudal} ml/h (fue {val} ml/h)"))
    return CheckResult(len(violations) == 0, violations)

# Propiedad de Safety: Ante una alarma crítica sin confirmación del personal, la bomba debe permanecer bloqueada (sin infundir líquido).
def check_safety_bloqueo_critico(trazas) -> CheckResult:
    violations = []
    alarmas_criticas = [t for t, tipo in trazas["emisiones_alarma"] if tipo == "CRITICA"]
    if not alarmas_criticas:
        return CheckResult(True)
        
    t_primera_critica = alarmas_criticas[0]
    eventos = trazas["eventos_logicos"]
    conf_posterior = next((evt for evt in eventos if evt["evento"] in ("CONFIRMACION_ENFERMERO", "AJUSTE_CAUDAL") and evt["tiempo"] > t_primera_critica), None)
    
    for t, val in trazas["caudal_real"]:
        if t > (t_primera_critica + 1.0):
            if conf_posterior and t > conf_posterior["tiempo"]:
                continue
            if val > 0.1:
                violations.append(_log_violation("SAFETY", t, f"Se infundió líquido ({val} ml/h) estando en ALARMA CRÍTICA no confirmada"))
                
    return CheckResult(len(violations) == 0, violations)

# =========================================================================
# LIVENESS PROPERTIES
# =========================================================================

# Propiedad de Liveness: Una orden médica con caudal positivo debe traducirse eventualmente en infusión física de fluido.
def check_liveness_orden_produce_accion(trazas) -> CheckResult:
    violations = []
    ordenes_positivas = [val for t, val in trazas["caudal_indicado"] if val > 0.0]
    if not ordenes_positivas:
        return CheckResult(True)
        
    max_caudal = max(val for t, val in trazas["caudal_real"])
    if max_caudal <= 0.1:
        t_final = trazas["caudal_real"][-1][0] if trazas["caudal_real"] else 0.0
        violations.append(_log_violation("LIVENESS", t_final, "La bomba recibió órdenes de infusión pero nunca bombeó líquido"))
        
    return CheckResult(len(violations) == 0, violations)

# Propiedad de Liveness: Una alarma crítica activa no confirmada por el enfermero debe re-notificarse (repetirse) después de 30 segundos, y a partir de allí cada 10 segundos.
def check_liveness_alarma_critica_repite(trazas) -> CheckResult:
    violations = []
    alarmas_criticas = [t for t, tipo in trazas["emisiones_alarma"] if tipo == "CRITICA"]
    if not alarmas_criticas:
        return CheckResult(True)
        
    t_primera_critica = alarmas_criticas[0]
    eventos = trazas["eventos_logicos"]
    conf_posterior = next((evt for evt in eventos if evt["evento"] in ("CONFIRMACION_ENFERMERO", "AJUSTE_CAUDAL") and evt["tiempo"] > t_primera_critica), None)
    
    t_limite = conf_posterior["tiempo"] if conf_posterior else (trazas["caudal_real"][-1][0] if trazas["caudal_real"] else 0.0)
    
    # Calculamos los tiempos teóricos esperados de las repeticiones
    tiempos_esperados = []
    
    # La primera repetición es a los 30 segundos de la alarma inicial
    t_esperado = t_primera_critica + 30.0
    if t_esperado < t_limite - 0.1:
        tiempos_esperados.append(t_esperado)
        
        # A partir de ahí, se repite cada 10 segundos
        t_esperado += 10.0
        while t_esperado < t_limite - 0.1:
            tiempos_esperados.append(t_esperado)
            t_esperado += 10.0
            
    # Validamos que exista una emisión real de alarma crítica cercana a cada tiempo esperado
    tolerancia = 0.5
    for t_esp in tiempos_esperados:
        emision_cercana = any(abs(t - t_esp) <= tolerancia for t in alarmas_criticas)
        if not emision_cercana:
            violations.append(_log_violation("LIVENESS", t_esp, f"Se esperaba una repetición de la alarma crítica en t={t_esp:.1f}s pero no se emitió"))
            
    return CheckResult(len(violations) == 0, violations)

# Propiedad de Liveness: La detección de fin de bolsa debe provocar la detención de la infusión habiendo pasado el tiempo de gracia (incluso sin confirmación humana).
def check_liveness_fin_bolsa_detiene(trazas) -> CheckResult:
    violations = []
    eventos = trazas["eventos_logicos"]
    t_fin_bolsa = next((evt["tiempo"] for evt in eventos if evt["evento"] == "FIN_BOLSA_DETECTADO"), None)
    if not t_fin_bolsa:
        return CheckResult(True)
        
    t_detencion = next((evt["tiempo"] for evt in eventos if evt["evento"] == "DETENCION_MEDICA" and evt["tiempo"] > t_fin_bolsa), None)
    
    if not t_detencion:
        t_final = eventos[-1]["tiempo"] if eventos else 0.0
        if (t_final - t_fin_bolsa) > 60.0:
            violations.append(_log_violation("LIVENESS", t_final, "La bomba no se detuvo tras el fin de bolsa habiendo pasado exactamente el tiempo de gracia (60s)"))
            
    return CheckResult(len(violations) == 0, violations)

# =========================================================================
# TEMPORAL PROPERTIES
# =========================================================================

# Propiedad Temporal: Tras una orden médica de infusión, la bomba debe iniciar el bombeo físico en un tiempo máximo estipulado (por defecto <= 3.0s).
def check_temporal_inicio_rapido(trazas, max_demora=3.0) -> CheckResult:
    violations = []
    t_orden = next((t for t, val in trazas["caudal_indicado"] if val > 0.0), None)
    if t_orden is None:
        return CheckResult(True)
        
    t_inicio_real = next((t for t, val in trazas["caudal_real"] if val > 0.1), None)
    if not t_inicio_real:
        return CheckResult(True)
        
    demora = t_inicio_real - t_orden
    if demora > max_demora:
        violations.append(_log_violation("TEMPORAL", t_inicio_real, f"Bomba tardó {demora:.1f}s en arrancar. Debió ser <= {max_demora}s"))
        
    return CheckResult(len(violations) == 0, violations)

# Propiedad Temporal: Se debe emitir una ALARMA_MEDIA en un tiempo de tolerancia (+/- 1.0s) respecto a los 5 segundos de desvío sostenido del caudal (discrepancia >= 10%).
def check_temporal_alarma_media_5s(trazas) -> CheckResult:
    violations = []
    t_desvio_5 = next((t for t, val in trazas["desvio"] if val >= 5.0), None)
    if not t_desvio_5:
        return CheckResult(True)
        
    eventos = trazas["eventos_logicos"]
    t_alarma_media = next((evt["tiempo"] for evt in eventos if evt["evento"] == "ALARMA_MEDIA"), None)
    
    if not t_alarma_media:
        violations.append(_log_violation("TEMPORAL", t_desvio_5, "El desvío llegó a 5s pero nunca se emitió ALARMA_MEDIA"))
    else:
        diff = abs(t_alarma_media - t_desvio_5)
        if diff > 1.0:
            violations.append(_log_violation("TEMPORAL", t_alarma_media, f"La ALARMA_MEDIA se emitió {diff:.1f}s fuera de tiempo respecto a los 5s de desvío"))
            
    return CheckResult(len(violations) == 0, violations)

# Propiedad Temporal: Al cumplirse la ventana de gracia de 60 segundos tras la alerta de fin de bolsa, la bomba debe detenerse a lo sumo en 60.0s.
def check_temporal_fin_bolsa_60s(trazas) -> CheckResult:
    violations = []
    eventos = trazas["eventos_logicos"]
    t_fin_bolsa = next((evt["tiempo"] for evt in eventos if evt["evento"] == "FIN_BOLSA_DETECTADO"), None)
    if not t_fin_bolsa:
        return CheckResult(True)
        
    t_detencion = next((evt["tiempo"] for evt in eventos if evt["evento"] == "DETENCION_MEDICA" and evt["tiempo"] > t_fin_bolsa), None)
    
    if t_detencion:
        tiempo_transcurrido = t_detencion - t_fin_bolsa
        if tiempo_transcurrido > 60.0:
            violations.append(_log_violation("TEMPORAL", t_detencion, f"La bomba tardó {tiempo_transcurrido:.1f}s en detenerse tras el fin de bolsa (> 60.0s)"))
            
    return CheckResult(len(violations) == 0, violations)

def check_all_properties(trazas) -> dict[str, CheckResult]:
    """Ejecuta TODAS las verificaciones y retorna un reporte completo."""
    return {
        "safety_caudal_max": check_safety_caudal_max(trazas),
        "safety_bloqueo_critico": check_safety_bloqueo_critico(trazas),
        "liveness_orden": check_liveness_orden_produce_accion(trazas),
        "liveness_critica": check_liveness_alarma_critica_repite(trazas),
        "liveness_fin_bolsa": check_liveness_fin_bolsa_detiene(trazas),
        "temporal_inicio_rapido": check_temporal_inicio_rapido(trazas),
        "temporal_alarma_media": check_temporal_alarma_media_5s(trazas),
        "temporal_fin_bolsa_60s": check_temporal_fin_bolsa_60s(trazas)
    }
