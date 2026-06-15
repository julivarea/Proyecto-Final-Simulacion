"""
Test de simulación para los generadores (G_om, G_ce y G_fb).
"""
from pypdevs.minimal import AtomicDEVS, CoupledDEVS, Simulator
from pypdevs.infinity import INFINITY

from src.models.atomic.generador_ordenes import GeneradorOrdenes
from src.models.atomic.generador_conf import GeneradorConfirmaciones
from src.models.atomic.generador_bolsa import GeneradorFinBolsa

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

class TestGeneradores(CoupledDEVS):
    """Prueba base con caudal constante a 600 ml/h"""
    def __init__(self, name="TestGeneradores"):
        super().__init__(name)

        self.gen_ordenes = self.addSubModel(GeneradorOrdenes())
        self.gen_conf = self.addSubModel(GeneradorConfirmaciones())
        
        cronograma_sensor = [{"delay": 10.0, "valor": 600.0}]
        self.gen_sensor_falso = self.addSubModel(GeneradorManual("SensorFalso", cronograma_sensor))
        self.gen_bolsa = self.addSubModel(GeneradorFinBolsa(capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0))

        self.rec_ordenes = self.addSubModel(Recolector("Rec_ordenes"))
        self.rec_conf = self.addSubModel(Recolector("Rec_conf"))
        self.rec_bolsa = self.addSubModel(Recolector("Rec_bolsa"))

        self.connectPorts(self.gen_ordenes.out_caudal_obj, self.rec_ordenes.in_port)
        self.connectPorts(self.gen_conf.out_conf, self.rec_conf.in_port)
        self.connectPorts(self.gen_sensor_falso.out_port, self.gen_bolsa.in_caudal_medido)
        self.connectPorts(self.gen_bolsa.out_fin_bolsa, self.rec_bolsa.in_port)


class TestGeneradorBolsaVariable(CoupledDEVS):
    """Prueba avanzada con caudal variable que cambia a lo largo del tiempo"""
    def __init__(self, name="TestBolsaVariable"):
        super().__init__(name)

        cronograma_variable = [
            {"delay": 10.0, "valor": 150.0},
            {"delay": 1000.0, "valor": 300.0},
            {"delay": 2000.0, "valor": 600.0}
        ]
        
        self.gen_sensor_variable = self.addSubModel(GeneradorManual("SensorVar", cronograma_variable))
        self.gen_bolsa_var = self.addSubModel(GeneradorFinBolsa(capacidad_bolsa_ml=500.0, tiempo_anticipacion_alerta_segs=60.0))
        self.rec_bolsa_var = self.addSubModel(Recolector("Rec_bolsa_var"))

        self.connectPorts(self.gen_sensor_variable.out_port, self.gen_bolsa_var.in_caudal_medido)
        self.connectPorts(self.gen_bolsa_var.out_fin_bolsa, self.rec_bolsa_var.in_port)

        # Hacemos un monkey-patching sólo para el test, para imprimir la evolución del volumen interno
        bolsa = self.gen_bolsa_var
        orig_ext = bolsa.extTransition
        orig_int = bolsa.intTransition
        
        def new_ext(inputs):
            t = bolsa.time_last[0] + bolsa.elapsed
            # Ejecutamos la transición real
            state = orig_ext(inputs)
            if bolsa.in_caudal_medido in inputs:
                caudal = inputs[bolsa.in_caudal_medido][0]
                print(f"  [t={t:>7.2f}s] Sensor envía nuevo caudal: {caudal:>6.2f} ml/h. Volumen restante en la bolsa: {state['volumen_restante_ml']:.2f} ml")
            return state

        def new_int():
            # El tiempo actual en intTransition corresponde al tiempo programado en time_next
            t = bolsa.time_next[0]
            # Ejecutamos la transición real
            state = orig_int()
            from src.models.atomic.generador_bolsa import FasesBolsa
            if state["fase"] == FasesBolsa.ESPERANDO_RELLENO:
                print(f"  [t={t:>7.2f}s] ¡Alerta interna disparada! Esperando 60s para que se vacíe completamente y se rellene...")
            elif state["fase"] == FasesBolsa.MONITOREANDO:
                print(f"  [t={t:>7.2f}s] ¡Bolsa rellenada! Nuevo volumen: {state['volumen_restante_ml']:.2f} ml")
            return state

        bolsa.extTransition = new_ext
        bolsa.intTransition = new_int


def correr_simulacion_base():
    modelo = TestGeneradores()
    sim = Simulator(modelo)
    sim.setTerminationTime(3600.0)
    sim.simulate()

    print(f"\n{'='*60}")
    print("TEST 1: CAUDAL CONSTANTE Y GENERADORES ALEATORIOS (3600s)")
    print(f"{'='*60}")

    eventos_ordenes = modelo.rec_ordenes.state["eventos"]
    print(f"\n--- Generador de Órdenes Médicas (G_om) ---")
    print(f"  Órdenes emitidas: {len(eventos_ordenes)}")
    for e in eventos_ordenes[:3]:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | Caudal: {e['valor']:>6.2f} ml/h")
    if len(eventos_ordenes) > 3: print("    ... (truncado)")

    eventos_bolsa = modelo.rec_bolsa.state["eventos"]
    print(f"\n--- Generador de Fin de Bolsa Constante (G_fb) ---")
    print(f"  (Consumiendo a 600 ml/h desde el segundo 10.0)")
    for e in eventos_bolsa:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | ¡Alarma Bolsa Vacía! (Valor: {e['valor']})")


def correr_simulacion_variable():
    modelo_var = TestGeneradorBolsaVariable()
    sim_var = Simulator(modelo_var)
    # Extendemos a 8000s para permitir que la bolsa se vacíe, se rellene, y vuelva a vaciarse al menos una vez más
    sim_var.setTerminationTime(8000.0) 
    
    print(f"\n{'='*60}")
    print("TEST 2: CAUDAL VARIABLE Y RELLENO AUTOMÁTICO DE LA BOLSA (8000s)")
    print(f"{'='*60}")
    
    print("  Cronograma inyectado:")
    print("  - [t=  10.0s] Setea flujo a 150 ml/h")
    print("  - [t=1010.0s] Setea flujo a 300 ml/h")
    print("  - [t=3010.0s] Setea flujo a 600 ml/h")
    print("\n--- Evolución Interna de la Bolsa (Traza en vivo) ---")

    sim_var.simulate()

    eventos_bolsa_var = modelo_var.rec_bolsa_var.state["eventos"]
    print(f"\n--- Resumen de Alertas Recibidas por el Recolector ---")
    print(f"  Alertas de fin de bolsa emitidas: {len(eventos_bolsa_var)}")
    for e in eventos_bolsa_var:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | ¡Alarma Bolsa Vacía! (Valor: {e['valor']})")


def main():
    correr_simulacion_base()
    correr_simulacion_variable()


if __name__ == "__main__":
    main()
