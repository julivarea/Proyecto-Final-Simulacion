from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY


class RegistradorEventos(AtomicDEVS):
    """
    Registrador de Eventos (R_e)
    Componente sumidero pasivo que almacena el historial de decisiones
    emitidas por el Controlador de Bomba, formando una traza de auditoría.
    No posee puertos de salida ni transiciones internas activas.
    """
    def __init__(self, name="R_e"):
        super().__init__(name)

        # Puerto de entrada
        self.in_registrar = self.addInPort("in_registrar")

        # Estado inicial: s0 = ([], INFINITY)
        self.state = {
            "historial": [],
            "sigma": INFINITY
        }

    def timeAdvance(self):
        # ta(historial, sigma) = sigma (siempre INFINITY)
        return self.state["sigma"]

    def outputFnc(self):
        # lambda(historial, sigma) = vacío (no emite nada)
        return {}

    def intTransition(self):
        # delta_int(historial, sigma) = (historial, INFINITY)
        # No se ejecuta en la práctica porque sigma siempre es INFINITY
        return self.state

    def extTransition(self, inputs):
        # delta_ext((historial, sigma), e, (Xv, port)) = (historial ++ [Xv], INFINITY)
        eventos_recibidos = inputs[self.in_registrar]
        tiempo_absoluto = self.time_last[0] + self.elapsed # Para registrar el tiempo en el que ocurrió el evento recibido

        for evento in eventos_recibidos:
            self.state["historial"].append({
                "tiempo": tiempo_absoluto,
                "evento": evento
            })

        return self.state
