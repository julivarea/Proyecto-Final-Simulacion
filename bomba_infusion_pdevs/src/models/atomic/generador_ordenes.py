from pypdevs.minimal import AtomicDEVS
from src.utils.distribuciones import uniforme, exponencial

class GeneradorOrdenes(AtomicDEVS):
    def __init__(self, name="G_om"):
        super().__init__(name)
        
        # Puertos
        # Y_Gom = [0,200] x {out_caudal_obj} 
        self.out_caudal_obj = self.addOutPort("out_caudal_obj")
        
        # Estado Inicial (s0)
        # s0 = (Uniforme(0, 200), Exponencial(1/300.0))
        self.state = {
            "caudalObjetivo": uniforme(0, 200),
            "sigma": exponencial(1/300.0)
        }

    def timeAdvance(self):
        # ta(caudalObjetivo, sigma) = sigma
        return self.state["sigma"]

    def outputFnc(self):
        # lambda(caudalObjetivo, sigma) = (caudalObjetivo, out_caudal_obj)
        # PyPDEVS espera un diccionario que mapee el puerto al valor a emitir
        return {self.out_caudal_obj: [self.state["caudalObjetivo"]]}

    def intTransition(self):
        # delta_int(caudalObjetivo, sigma) = (Uniforme(0, 200), Exponencial(1/300.0))
        self.state["caudalObjetivo"] = uniforme(0, 200)
        self.state["sigma"] = exponencial(1/300.0)
        
        return self.state

    # PyPDEVS maneja automáticamente las transiciones externas vacías si no las sobreescribimos.