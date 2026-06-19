from pypdevs.minimal import AtomicDEVS
from src.utils.distribuciones import exponencial

CONFIRMACION_ENFERMERO = "confirmacionEnfermero"

class GeneradorConfirmaciones(AtomicDEVS):
    def __init__(self, name="G_ce"):
        super().__init__(name)

        # Y_Gce = {confirmacionEnfermero} x {out_conf}
        self.out_conf = self.addOutPort("out_conf")

        # s0 = Exponencial(1/8.0)
        self.state = {
            "sigma": exponencial(1 / 8.0)
        }

    def timeAdvance(self):
        # ta(sigma) = sigma
        return self.state["sigma"]

    def outputFnc(self):
        # lambda(sigma) = (confirmacionEnfermero, out_conf)
        return {self.out_conf: [CONFIRMACION_ENFERMERO]}

    def intTransition(self):
        # delta_int(sigma) = Exponencial(1/8.0)
        self.state["sigma"] = exponencial(1 / 8.0) 
        return self.state
