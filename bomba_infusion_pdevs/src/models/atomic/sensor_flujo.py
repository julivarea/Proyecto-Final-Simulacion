from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY

from src.utils.distribuciones import normal

PORCENTAJE_RUIDO_SENSOR = 0.20
PERIODO_MUESTREO_SEGS = 1.0


def _aplicar_ruido_gaussiano(caudal_real_ml_h):
    """
    Aplica ruido Gaussiano del 20% al caudal real.
    Normal(caudalReal, (0.20 * caudalReal)^2)
    Si el caudal es 0, no hay ruido posible (desvío = 0).
    """
    if caudal_real_ml_h == 0.0:
        return 0.0
    varianza = (PORCENTAJE_RUIDO_SENSOR * caudal_real_ml_h) ** 2
    return normal(caudal_real_ml_h, varianza)


class SensorFlujo(AtomicDEVS):
    """
    Sensor de Flujo (G_sf)
    Muestrea periódicamente el caudal real del actuador e inyecta un 
    ruido Gaussiano del 20% para simular el error de medición físico.
    Emite una lectura cada 1 segundo una vez que recibe el primer caudal.
    """
    def __init__(self, name="G_sf"):
        super().__init__(name)

        # Puertos
        # X_Gsf = [0,200] x {in_caudal_real}
        self.in_caudal_real = self.addInPort("in_caudal_real")
        # Y_Gsf = [0,200] x {out_caudal_medido}
        self.out_caudal_medido = self.addOutPort("out_caudal_medido")

        # Estado inicial: s0 = (0.0, 0.0, INFINITY)
        self.state = {
            "caudal_real_ml_h": 0.0,
            "caudal_medido_ml_h": 0.0,
            "sigma": INFINITY
        }

    def timeAdvance(self):
        # ta(caudalReal, caudalMedido, sigma) = sigma
        return self.state["sigma"]

    def outputFnc(self):
        # lambda(caudalReal, caudalMedido, sigma) = (caudalMedido, out_caudal_medido)
        return {self.out_caudal_medido: [self.state["caudal_medido_ml_h"]]}

    def intTransition(self):
        # delta_int(caudalReal, caudalMedido, sigma) = 
        #   (caudalReal, Normal(caudalReal, (0.20 * caudalReal)^2), 1.0)
        caudal_real = self.state["caudal_real_ml_h"]
        self.state["caudal_medido_ml_h"] = _aplicar_ruido_gaussiano(caudal_real)
        self.state["sigma"] = PERIODO_MUESTREO_SEGS
        return self.state

    def extTransition(self, inputs):
        # delta_ext((caudalReal, caudalMedido, sigma), e, (Xv, port))
        nuevo_caudal_real = inputs[self.in_caudal_real][0]
        sigma_actual = self.state["sigma"]

        nuevo_caudal_medido = _aplicar_ruido_gaussiano(nuevo_caudal_real)

        if sigma_actual == INFINITY:
            # Primera vez que recibe un caudal: arranca el muestreo inmediatamente
            # sigma = infinity => sigma = 0.0 (emitir de inmediato)
            nuevo_sigma = 0.0
        else:
            # Ya estaba muestreando: mantiene el ciclo restante
            # sigma < infinity => sigma = sigma - e
            nuevo_sigma = sigma_actual - self.elapsed

        self.state["caudal_real_ml_h"] = nuevo_caudal_real
        self.state["caudal_medido_ml_h"] = nuevo_caudal_medido
        self.state["sigma"] = nuevo_sigma
        return self.state
