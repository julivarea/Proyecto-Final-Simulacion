import pytest
from pypdevs.minimal import CoupledDEVS, Simulator
from src.models.atomic.modulo_alarmas import ModuloAlarmas, TiposAlarma
from tests.helpers.testing_utils import GeneradorManual, Recolector

class MockModuloAlarmasModel(CoupledDEVS):
    def __init__(self, name="MockAlarmas"):
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


def test_modulo_alarmas():
    """
    Test del Módulo de Alarmas (M_a).
    Comportamiento esperado:
    - Las alarmas BAJA y MEDIA se notifican una vez (t=5s, t=10s) y se silencian solas.
    - La alarma CRITICA entra en t=20s. Alerta y queda esperando confirmación.
    - Como a los 30s no hay confirmación, a partir del t=50s comienza el ciclo de repetición cada 10s (t=50s, t=60s, t=70s).
    - En t=75s llega una confirmación del enfermero y el módulo se silencia (no hay más alertas en t=80s).
    """
    modelo = MockModuloAlarmasModel()
    sim = Simulator(modelo)
    sim.setTerminationTime(90.0)
    sim.simulate()

    eventos = modelo.rec_alarmas.state["eventos"]

    tiempos = [e['tiempo'] for e in eventos]
    valores = [e['valor'] for e in eventos]
    
    assert tiempos[0] == 5.0 and valores[0] == TiposAlarma.BAJA, "Falla en alarma baja t=5"
    assert tiempos[1] == 10.0 and valores[1] == TiposAlarma.MEDIA, "Falla en alarma media t=10"
    
    # Critica
    assert tiempos[2] == 20.0 and valores[2] == TiposAlarma.CRITICA, "Falla en alarma critica inicial t=20"
    
    # Repeticiones
    assert tiempos[3] == 50.0 and valores[3] == TiposAlarma.CRITICA, "Falla en repetición 1 (después de 30s) t=50"
    assert tiempos[4] == 60.0 and valores[4] == TiposAlarma.CRITICA, "Falla en repetición 2 (10s después) t=60"
    assert tiempos[5] == 70.0 and valores[5] == TiposAlarma.CRITICA, "Falla en repetición 3 (10s después) t=70"
    
    # Después de confirmación en t=75, no debería haber eventos en t=80
    assert len(eventos) == 6, "No deberían emitirse más alarmas después de la confirmación"
