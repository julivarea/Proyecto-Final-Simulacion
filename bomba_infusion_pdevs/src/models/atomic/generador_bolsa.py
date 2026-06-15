from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY

class FasesBolsa:
    MONITOREANDO = "MONITOREANDO"
    ESPERANDO_RELLENO = "ESPERANDO_RELLENO"

class GeneradorFinBolsa(AtomicDEVS):
    """
    Generador de Fin de Bolsa (G_fb)
    Modela el vaciado físico de la bolsa de infusión y emite una alerta 
    unos segundos antes de agotarse. Luego simula un relleno automático.
    """
    def __init__(self, name="G_fb", capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0):
        super().__init__(name)
        
        self.capacidad_bolsa_ml = capacidad_bolsa_ml
        self.tiempo_anticipacion_alerta_segs = tiempo_anticipacion_alerta_segs
        
        # Puertos
        # X_Gfb = [0,200] x {in_caudal_medido}
        self.in_caudal_medido = self.addInPort("in_caudal_medido")
        # Y_Gfb = {T} x {out_fin_bolsa}
        self.out_fin_bolsa = self.addOutPort("out_fin_bolsa")
        
        # Estado inicial s0 = (MONITOREANDO, V0, 0.0, inf)
        self.state = {
            "fase": FasesBolsa.MONITOREANDO,
            "volumen_restante_ml": self.capacidad_bolsa_ml,
            "caudal_actual_ml_h": 0.0,
            "sigma": INFINITY
        }

    def _calcular_volumen_restante(self, volumen_actual_ml, caudal_ml_h, tiempo_transcurrido_segs):
        """Calcula el volumen restante tras e segundos al caudal especificado"""
        consumo_ml = caudal_ml_h * (tiempo_transcurrido_segs / 3600.0)
        return max(volumen_actual_ml - consumo_ml, 0.0)

    def _calcular_tiempo_hasta_alerta(self, volumen_actual_ml, caudal_ml_h):
        """Calcula cuánto falta en segundos para emitir la alerta de bolsa vacía"""
        if caudal_ml_h == 0.0:
            return INFINITY
        
        tiempo_vaciado_segs = volumen_actual_ml / (caudal_ml_h / 3600.0)
        
        if tiempo_vaciado_segs <= self.tiempo_anticipacion_alerta_segs:
            return 0.0
        else:
            return tiempo_vaciado_segs - self.tiempo_anticipacion_alerta_segs

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        if self.state["fase"] == FasesBolsa.MONITOREANDO:
            return {self.out_fin_bolsa: [True]}
        return {}

    def intTransition(self):
        fase = self.state["fase"]
        caudal_actual_ml_h = self.state["caudal_actual_ml_h"]
        
        if fase == FasesBolsa.MONITOREANDO:
            self.state["fase"] = FasesBolsa.ESPERANDO_RELLENO
            self.state["sigma"] = self.tiempo_anticipacion_alerta_segs
            
        elif fase == FasesBolsa.ESPERANDO_RELLENO:
            self.state["fase"] = FasesBolsa.MONITOREANDO
            self.state["volumen_restante_ml"] = self.capacidad_bolsa_ml
            self.state["sigma"] = self._calcular_tiempo_hasta_alerta(
                self.capacidad_bolsa_ml, 
                caudal_actual_ml_h
            )
            
        return self.state

    def extTransition(self, inputs):
        # Actualizamos el volumen basado en el tiempo físico que pasó
        nuevo_volumen_restante = self._calcular_volumen_restante(
            self.state["volumen_restante_ml"], 
            self.state["caudal_actual_ml_h"], 
            self.elapsed
        )
        
        # Leemos el nuevo caudal
        if self.in_caudal_medido in inputs:
            # El input fue un nuevo caudal del sensor
            nuevo_caudal_ml_h = inputs[self.in_caudal_medido][0]
        else:
            # El input fue una confirmacion del enfermero
            nuevo_caudal_ml_h = self.state["caudal_actual_ml_h"]
            
        fase = self.state["fase"]
        
        if fase == FasesBolsa.ESPERANDO_RELLENO:
            self.state["volumen_restante_ml"] = nuevo_volumen_restante
            self.state["caudal_actual_ml_h"] = nuevo_caudal_ml_h
            self.state["sigma"] -= self.elapsed
            
        elif fase == FasesBolsa.MONITOREANDO:
            self.state["volumen_restante_ml"] = nuevo_volumen_restante
            self.state["caudal_actual_ml_h"] = nuevo_caudal_ml_h
            self.state["sigma"] = self._calcular_tiempo_hasta_alerta(
                nuevo_volumen_restante, 
                nuevo_caudal_ml_h
            )
            
        return self.state
