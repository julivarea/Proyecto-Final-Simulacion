import unittest
import sys
import os

# Aseguramos que los experimentos estén en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from experiments.sim_01_normal import ejecutar_escenario_01
from experiments.sim_02_cambio_orden import ejecutar_escenario_02
from experiments.sim_03_detencion import ejecutar_escenario_03
from experiments.sim_04_desvio_leve import ejecutar_escenario_04
from experiments.sim_05_desvio_mayor import ejecutar_escenario_05
from experiments.sim_06_fin_bolsa import ejecutar_escenario_06
from experiments.sim_07_alarma_critica import ejecutar_escenario_07


class TestPropiedadesFormales(unittest.TestCase):
    """
    Verificación Formal de Propiedades (Safety, Liveness, Temporales).
    Evalúa matemáticamente los requerimientos del enunciado sobre las trazas de simulación.
    """

    @classmethod
    def setUpClass(cls):
        # Ejecutamos todos los escenarios y guardamos las trazas
        # Deshabilitamos stdout para no ensuciar
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        
        cls.trazas = {
            "01_normal": ejecutar_escenario_01(),
            "02_cambio": ejecutar_escenario_02(),
            "03_detencion": ejecutar_escenario_03(),
            "04_leve": ejecutar_escenario_04(),
            "05_mayor": ejecutar_escenario_05(),
            "06_bolsa": ejecutar_escenario_06(),
            "07_critica": ejecutar_escenario_07()
        }
        
        sys.stdout.close()
        sys.stdout = original_stdout

    # =========================================================================
    # SAFETY PROPERTIES
    # =========================================================================

    def test_safety_1_caudal_nulo_tras_orden_cero(self):
        """
        Safety 1: La bomba no debe administrar medicacion si la ultima orden medica fue de caudal 0.
        (Evaluado en escenario 03 - Detención)
        """
        tr = self.trazas["03_detencion"]
        
        # Orden de detención se da a los 20s. Evaluamos de 25s en adelante.
        caudales_posteriores = [val for t, val in tr["caudal_real"] if t > 25.0]
        for val in caudales_posteriores:
            # Tolerancia casi cero (no deberia fluir liquido, ni siquiera ruido)
            self.assertAlmostEqual(val, 0.0, delta=0.1, 
                msg=f"Safety Violation: Caudal real es {val} pero la orden era 0.0")

    def test_safety_2_limite_maximo(self):
        """
        Safety 2: El caudal administrado no debe superar el maximo permitido (200 ml/h).
        (Evaluamos en todos los escenarios)
        """
        for nombre_escenario, tr in self.trazas.items():
            for t, val in tr["caudal_real"]:
                self.assertLessEqual(val, 200.0, 
                    f"Safety Violation en {nombre_escenario}: Caudal excedió los 200 ml/h ({val} ml/h a los {t}s)")

    def test_safety_3_bloqueo_alarma_critica(self):
        """
        Safety 3: Luego de una alarma critica, no se debe reanudar la emision hasta recibir 
        una confirmacion o una nueva orden medica.
        (Evaluado en escenario 07 - Alarma crítica sostenida sin confirmación)
        """
        tr = self.trazas["07_critica"]
        
        # En el escenario 7, la alarma critica salta a los ~29s y nunca se confirma.
        # Por lo tanto, desde los 30s en adelante el caudal debe ser estrictamente 0.
        caudales_criticos = [val for t, val in tr["caudal_real"] if t >= 30.0]
        for val in caudales_criticos:
            self.assertAlmostEqual(val, 0.0, delta=0.1,
                msg=f"Safety Violation: Se reanudó infusión ({val} ml/h) estando en ALARMA CRÍTICA no confirmada")

    # =========================================================================
    # LIVENESS PROPERTIES
    # =========================================================================

    def test_liveness_1_orden_produce_accion(self):
        """
        Liveness 1: Toda orden medica debe producir una accion sobre la bomba.
        (Evaluado en escenario 01 - Nueva Orden Normal)
        """
        tr = self.trazas["01_normal"]
        ultimo_caudal = tr["caudal_real"][-1][1]
        
        # La bomba debía llegar a 50 ml/h eventualmente
        # Por la varianza del sensor, puede no ser exactamente 50.0, pero debe ser > 0
        self.assertGreater(ultimo_caudal, 0.0, "Liveness Violation: La orden de 50ml/h nunca inició la bomba")

    def test_liveness_2_repeticion_alarma_critica(self):
        """
        Liveness 2 y Temporal 4: Si la alarma critica no se confirma, se repite periodicamente cada 10s.
        (Evaluado en escenario 07)
        """
        tr = self.trazas["07_critica"]
        alarmas = tr["emisiones_alarma"]
        
        tiempos_criticas = [t for t, tipo in alarmas if tipo == "CRITICA"]
        self.assertGreater(len(tiempos_criticas), 1, "Liveness Violation: La alarma crítica no se repitió")
        
        # Verificamos que la distancia entre alarmas sea correcta (primero 30s, luego 10s)
        for i in range(1, len(tiempos_criticas)):
            diferencia = tiempos_criticas[i] - tiempos_criticas[i-1]
            esperado = 30.0 if i == 1 else 10.0
            self.assertAlmostEqual(diferencia, esperado, delta=1.0, 
                msg=f"Temporal Violation: La repetición {i} tardó {diferencia}s, debió ser {esperado}s")

    def test_liveness_3_fin_bolsa_detiene_infusion(self):
        """
        Liveness 3 y Temporal 3: Luego de detectar fin de bolsa, la bomba se detiene 
        como máximo dentro de 60 segundos.
        """
        tr = self.trazas["06_bolsa"]
        eventos = tr["eventos_logicos"]
        
        t_fin_bolsa = next((evt["tiempo"] for evt in eventos if evt["evento"] == "FIN_BOLSA_DETECTADO"), None)
        t_detencion = next((evt["tiempo"] for evt in eventos if evt["evento"] == "DETENCION_MEDICA"), None)
        
        self.assertIsNotNone(t_fin_bolsa, "No se detectó fin de bolsa")
        self.assertIsNotNone(t_detencion, "Liveness Violation: La bomba nunca se detuvo tras fin de bolsa")
        
        tiempo_transcurrido = t_detencion - t_fin_bolsa
        self.assertLessEqual(tiempo_transcurrido, 60.5, 
            msg=f"Temporal Violation: La bomba tardó {tiempo_transcurrido}s en detenerse tras el fin de bolsa (> 60s)")

    # =========================================================================
    # TEMPORAL PROPERTIES
    # =========================================================================

    def test_temporal_1_inicio_infusion_rapido(self):
        """
        Temporal 1: Toda orden medica de caudal positivo debe comenzar la infusion 
        en menos de 3 segundos.
        (Evaluado en escenario 01: orden a los 2.0s)
        """
        tr = self.trazas["01_normal"]
        
        # Buscamos en las trazas reales cuándo el caudal superó 0.0 (empezó la infusión real)
        t_inicio_real = next((t for t, val in tr["caudal_real"] if val > 0.1), None)
        
        self.assertIsNotNone(t_inicio_real, "La infusión nunca arrancó")
        
        # La orden médica entra a los 2.0s
        demora = t_inicio_real - 2.0
        self.assertLess(demora, 3.0, 
            msg=f"Temporal Violation: La bomba tardó {demora}s en arrancar. Debió ser < 3s")

    def test_temporal_2_alarma_media_5_segundos(self):
        """
        Temporal 2: Si el caudal difiere en mas de 10% respecto al indicado por 5 segundos 
        se emite alarma media.
        """
        tr = self.trazas["05_mayor"]
        
        eventos = tr["eventos_logicos"]
        t_alarma = next((evt["tiempo"] for evt in eventos if evt["evento"] == "ALARMA_MEDIA"), None)
        self.assertIsNotNone(t_alarma, "No se emitió alarma media")
        
        # En el escenario 5, forzamos un desvío a partir de los 20.0s (detectado en el sensor)
        # La alarma debe sonar cerca de los 25s
        self.assertAlmostEqual(t_alarma, 25.0, delta=1.0, 
            msg=f"Temporal Violation: La alarma media sonó a los {t_alarma}s, se esperaba a los 25.0s")


if __name__ == '__main__':
    unittest.main(verbosity=2)
