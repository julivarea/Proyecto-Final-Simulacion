from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.modulo_alarmas import ModuloAlarmas, TiposAlarma
from tests.testing_utils import GeneradorManual, Recolector

class TestModuloAlarmas(CoupledDEVS):
    def __init__(self, name="TestAlarmas"):
        super().__init__(name)

        # t=5s -> Baja
        cron_baja = [{"delay": 5.0, "valor": True}, {"delay": 1000.0, "valor": "DUMMY"}]
        self.gen_baja = self.addSubModel(GeneradorManual("GenBaja", cron_baja))
        
        # t=10s -> Media
        cron_media = [{"delay": 10.0, "valor": True}, {"delay": 1000.0, "valor": "DUMMY"}]
        self.gen_media = self.addSubModel(GeneradorManual("GenMedia", cron_media))
        
        # t=20s -> Crítica. Deberá notificar, luego en t=50s (30s despues) repetirá, en t=60s repetirá...
        cron_crit = [{"delay": 20.0, "valor": True}, {"delay": 1000.0, "valor": "DUMMY"}]
        self.gen_crit = self.addSubModel(GeneradorManual("GenCritica", cron_crit))
        
        # t=75s -> Confirmación. Silencia la alarma crítica (ya no repite en t=80s).
        cron_conf = [{"delay": 75.0, "valor": True}, {"delay": 1000.0, "valor": "DUMMY"}]
        self.gen_conf = self.addSubModel(GeneradorManual("GenConf", cron_conf))

        self.modulo = self.addSubModel(ModuloAlarmas("ModuloAlarmas"))
        self.rec_alarmas = self.addSubModel(Recolector("Rec_alarmas"))
        
        self.connectPorts(self.gen_baja.out_port, self.modulo.in_alarma_baja)
        self.connectPorts(self.gen_media.out_port, self.modulo.in_alarma_media)
        self.connectPorts(self.gen_crit.out_port, self.modulo.in_alarma_critica)
        self.connectPorts(self.gen_conf.out_port, self.modulo.in_conf)
        
        self.connectPorts(self.modulo.out_alarma, self.rec_alarmas.in_port)


def correr_test():
    """
    Test del Módulo de Alarmas (M_a).
    Comportamiento esperado:
    - Las alarmas BAJA y MEDIA se notifican una vez (t=5s, t=10s) y se silencian solas.
    - La alarma CRITICA entra en t=20s. Alerta y queda esperando confirmación.
    - Como a los 30s no hay confirmación, a partir del t=50s comienza el ciclo de repetición cada 10s (t=50s, t=60s, t=70s).
    - En t=75s llega una confirmación del enfermero y el módulo se silencia (no hay más alertas en t=80s).
    """
    modelo = TestModuloAlarmas()
    sim = Simulator(modelo)
    sim.setTerminationTime(90.0)
    sim.simulate()

    eventos = modelo.rec_alarmas.state["eventos"]
    print(f"\n{'='*60}")
    print("TEST: MÓDULO DE ALARMAS (90s)")
    print(f"{'='*60}")
    print("  Escenario:")
    print("    t= 5.0s -> Ingresa Alarma BAJA")
    print("    t=10.0s -> Ingresa Alarma MEDIA")
    print("    t=20.0s -> Ingresa Alarma CRITICA")
    print("    t=75.0s -> Ingresa CONFIRMACIÓN ENFERMERO")
    print("\n  Notificaciones emitidas por el Módulo (por la bocina/pantalla):")
    for e in eventos:
        print(f"    - Tiempo: {e['tiempo']:>7.2f}s | Nivel de Alarma Emitido: {e['valor']}")

if __name__ == "__main__":
    correr_test()
