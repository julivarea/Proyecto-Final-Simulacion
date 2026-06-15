from pypdevs.minimal import AtomicDEVS
from pypdevs.infinity import INFINITY

class GeneradorManual(AtomicDEVS):
    """Generador que emite eventos específicos en tiempos específicos predefinidos."""
    def __init__(self, name="G_Manual", cronograma=None):
        super().__init__(name)
        self.out_port = self.addOutPort("out")
        
        # cronograma es una lista de diccionarios: [{"delay": 10, "valor": 100}, {"delay": 50, "valor": 200}]
        self.cronograma = cronograma if cronograma else []
        self.indice = 0
        
        if self.cronograma:
            self.state = {"sigma": self.cronograma[0]["delay"]}
        else:
            self.state = {"sigma": INFINITY}

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.out_port: [self.cronograma[self.indice]["valor"]]}

    def intTransition(self):
        self.indice += 1
        if self.indice < len(self.cronograma):
            self.state["sigma"] = self.cronograma[self.indice]["delay"]
        else:
            self.state["sigma"] = INFINITY
        return self.state

class Recolector(AtomicDEVS):
    """Componente sumidero que registra todos los eventos y su tiempo absoluto de ocurrencia."""
    def __init__(self, name="Recolector"):
        super().__init__(name)
        self.in_port = self.addInPort("in")
        self.state = {"eventos": []}

    def timeAdvance(self):
        return INFINITY

    def extTransition(self, inputs):
        valores = inputs[self.in_port]
        tiempo_absoluto = self.time_last[0] + self.elapsed
        
        for v in valores:
            self.state["eventos"].append({"tiempo": tiempo_absoluto, "valor": v})
            
        return self.state
