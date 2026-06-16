import types

class SimulationMonitor:
    """
    Clase utilitaria para extraer métricas continuas y de estado de la simulación
    sin necesidad de ensuciar los scripts de escenarios con parcheos (monkey patching).
    Se encarga de interceptar de forma limpia las transiciones de los modelos clave.
    """
    def __init__(self, modelo_acoplado):
        self.modelo = modelo_acoplado
        
        # Estructuras para guardar la evolución temporal
        self.trazas_caudal_obj = [(0.0, 0.0)]
        self.trazas_caudal_real = [(0.0, 0.0)]
        # El controlador suele arrancar en una fase de espera (habría que confirmar su fase inicial, 
        # asumimos 'ESPERANDO_ORDEN' o similar, pero lo capturará en el primer evento)
        self.trazas_fase_controlador = [] 
        self.trazas_desvio = []
        self.trazas_bolsa = []
        self.trazas_alarmas = []
        
        self._inyectar_monitores()
        
    def _inyectar_monitores(self):
        # Referencias a componentes del modelo acoplado
        controlador = self.modelo.controlador
        sensor = self.modelo.sensor
        alarmas = self.modelo.alarmas
        
        # Guardamos las funciones originales
        ctrl_ext_orig = controlador.extTransition
        ctrl_int_orig = controlador.intTransition
        sensor_int_orig = sensor.intTransition
        alarmas_out_orig = alarmas.outputFnc
        
        monitor_self = self # Referencia local para acceder dentro de las funciones parcheadas
        
        # 1. Monitorear extTransition del Controlador
        def ctrl_ext_mod(self, inputs):
            res = ctrl_ext_orig(inputs)
            tiempo_actual = self.time_last[0] + self.elapsed
            
            # Guardamos caudal objetivo si entró una orden médica
            if self.in_orden_medica in inputs:
                caudal = self.state.get("caudal_obj", 0.0)
                monitor_self.trazas_caudal_obj.append((tiempo_actual, caudal))
                
            # Guardamos cambio de fase de la bomba
            fase_actual = self.state.get("fase", "DESCONOCIDO")
            if not monitor_self.trazas_fase_controlador or monitor_self.trazas_fase_controlador[-1][1] != fase_actual:
                monitor_self.trazas_fase_controlador.append((tiempo_actual, fase_actual))
                
            # Guardamos desvío acumulado si entra una medición de sensor
            if self.in_caudal_medido in inputs:
                monitor_self.trazas_desvio.append((tiempo_actual, self.state.get("seg_desvio", 0.0)))
                # También extraemos el cronómetro interno de bolsa
                monitor_self.trazas_bolsa.append((tiempo_actual, self.state.get("seg_fin_bolsa", 0.0)))
            
            return res
            
        # 2. Monitorear intTransition del Controlador
        def ctrl_int_mod(self):
            res = ctrl_int_orig()
            tiempo_actual = self.time_last[0] + self.state["sigma"]
            
            # Al ocurrir eventos internos (ej. cambio a alarma crítica), registramos la fase
            fase_actual = self.state.get("fase", "DESCONOCIDO")
            if not monitor_self.trazas_fase_controlador or monitor_self.trazas_fase_controlador[-1][1] != fase_actual:
                monitor_self.trazas_fase_controlador.append((tiempo_actual, fase_actual))
                
            return res

        # 3. Monitorear intTransition del SensorFlujo
        def sensor_int_mod(self):
            tiempo_actual = self.time_last[0] + self.state["sigma"]
            # Guardamos la lectura física antes de que ejecute
            caudal_físico = self.state.get("caudal_real_ml_h", 0.0)
            monitor_self.trazas_caudal_real.append((tiempo_actual, caudal_físico))
            
            return sensor_int_orig()

        # 4. Monitorear outputFnc del Módulo de Alarmas
        def alarmas_out_mod(self):
            res = alarmas_out_orig()
            if self.out_alarma in res:
                tiempo_actual = self.time_last[0] + self.state["sigma"]
                monitor_self.trazas_alarmas.append((tiempo_actual, res[self.out_alarma][0]))
            return res

        # Aplicamos los parches al modelo
        controlador.extTransition = types.MethodType(ctrl_ext_mod, controlador)
        controlador.intTransition = types.MethodType(ctrl_int_mod, controlador)
        sensor.intTransition = types.MethodType(sensor_int_mod, sensor)
        alarmas.outputFnc = types.MethodType(alarmas_out_mod, alarmas)
        
    def get_trazas(self):
        """Devuelve un diccionario con todas las trazas recolectadas listas para graficar."""
        return {
            "caudal_indicado": self.trazas_caudal_obj,
            "caudal_real": self.trazas_caudal_real,
            "fase_controlador": self.trazas_fase_controlador,
            "desvio": self.trazas_desvio,
            "fin_bolsa": self.trazas_bolsa,
            "emisiones_alarma": self.trazas_alarmas,
            "eventos_logicos": self.modelo.registrador.state["historial"] if hasattr(self.modelo, "registrador") else []
        }
