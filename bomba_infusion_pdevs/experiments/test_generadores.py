"""
Test de simulación para los generadores (G_om y G_ce).
"""
from pypdevs.minimal import AtomicDEVS, CoupledDEVS, Simulator
from pypdevs.infinity import INFINITY

from src.models.atomic.generador_ordenes import GeneradorOrdenes
from src.models.atomic.generador_conf import GeneradorConfirmaciones


class Recolector(AtomicDEVS):
    """Componente sumidero que registra todos los eventos recibidos."""

    def __init__(self, name="Recolector"):
        super().__init__(name)
        self.in_port = self.addInPort("in")
        self.state = {"eventos": []}

    def timeAdvance(self):
        return INFINITY

    def extTransition(self, inputs):
        valores = inputs[self.in_port]
        self.state["eventos"].extend(valores)
        return self.state


class TestGeneradores(CoupledDEVS):
    """Acoplado mínimo: conecta ambos generadores a recolectores independientes."""

    def __init__(self, name="TestGeneradores"):
        super().__init__(name)

        self.gen_ordenes = self.addSubModel(GeneradorOrdenes())
        self.gen_conf = self.addSubModel(GeneradorConfirmaciones())
        self.rec_ordenes = self.addSubModel(Recolector("Rec_ordenes"))
        self.rec_conf = self.addSubModel(Recolector("Rec_conf"))

        self.connectPorts(self.gen_ordenes.out_caudal_obj, self.rec_ordenes.in_port)
        self.connectPorts(self.gen_conf.out_conf, self.rec_conf.in_port)


def main():
    modelo = TestGeneradores()
    sim = Simulator(modelo)
    sim.setTerminationTime(600.0)
    sim.simulate()

    eventos_ordenes = modelo.rec_ordenes.state["eventos"]
    eventos_conf = modelo.rec_conf.state["eventos"]

    print(f"\n{'='*60}")
    print("RESULTADOS DE LA SIMULACIÓN (600s)")
    print(f"{'='*60}")

    print(f"\n--- Generador de Órdenes Médicas (G_om) ---")
    print(f"  Órdenes emitidas: {len(eventos_ordenes)}")
    if eventos_ordenes:
        print(f"  Rango de caudales: [{min(eventos_ordenes):.2f}, {max(eventos_ordenes):.2f}] ml/h")
        promedio = sum(eventos_ordenes) / len(eventos_ordenes)
        print(f"  Caudal promedio:   {promedio:.2f} ml/h (esperado ~100)")

    print(f"\n--- Generador de Confirmaciones (G_ce) ---")
    print(f"  Confirmaciones emitidas: {len(eventos_conf)}")
    if eventos_conf:
        print(f"  Valor emitido: '{eventos_conf[0]}' (todos iguales: {len(set(eventos_conf)) == 1})")


if __name__ == "__main__":
    main()
