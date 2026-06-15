from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY
from src.utils.distribuciones import uniforme

class ActuadorBomba(AtomicDEVS):
    """
    Actuador de la Bomba (A)
    Modela la respuesta física y mecánica de la bomba
    Aplica una latencia mecánica aleatoria a las órdenes del controlador
    """
    def __init__(self, name="A"):
        super().__init__(name)

        # Puertos de entrada
        # X_A = ([0,200] x {in_caudal_obj}) U ({detenerBomba} x {in_stop})
        self.in_caudal_obj = self.addInPort("in_caudal_obj")
        self.in_stop = self.addInPort("in_stop")

        # Puertos de salida
        # Y_A = [0,200] x {out_caudal_real}
        self.out_caudal_real = self.addOutPort("out_caudal_real")

        # Estado inicial: s0 = (0.0, INFINITY)
        # s = (caudalReal, sigma)
        self.state = {
            "caudal_real_ml_h": 0.0,
            "sigma": INFINITY
        }

    def timeAdvance(self):
        # ta(caudalReal, sigma) = sigma 
        return self.state["sigma"]

    def outputFnc(self):
        # lambda(caudalReal, sigma) = (caudalReal, out_caudal_real)
        return {self.out_caudal_real: [self.state["caudal_real_ml_h"]]}

    def intTransition(self):
        # delta_int(caudalReal, sigma) = (caudalReal, INFINITY)
        self.state["sigma"] = INFINITY
        return self.state

    def extTransition(self, inputs):
        # delta_ext((caudalReal, sigma), e, (Xv, port))
        
        if self.in_caudal_obj in inputs:
            nuevo_caudal = inputs[self.in_caudal_obj][0]
            self.state["caudal_real_ml_h"] = nuevo_caudal
            
            # (Xv, Uniforme(0, 0.5)) si port = in_caudal_obj
            self.state["sigma"] = uniforme(0.0, 0.5)
            
        elif self.in_stop in inputs:
            # (0.0, Uniforme(0, 0.5)) si port = in_stop
            self.state["caudal_real_ml_h"] = 0.0
            self.state["sigma"] = uniforme(0.0, 0.5)
            
        return self.state