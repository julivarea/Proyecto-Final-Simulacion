import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_generador_ordenes import correr_test as test_ordenes
from tests.test_generador_conf import correr_test as test_conf
from tests.test_generador_bolsa import correr_test as test_bolsa
from tests.test_sensor_flujo import correr_test as test_sensor
from tests.test_registrador import correr_test as test_registrador
from tests.test_actuador import correr_test as test_actuador
from tests.test_modulo_alarmas import correr_test as test_alarmas

def main():
    print("="*80)
    print("EJECUTANDO SUITE COMPLETA DE TESTS DE COMPONENTES DE LA BOMBA DE INFUSIÓN")
    print("="*80)
    
    test_ordenes()
    test_conf()
    test_bolsa()
    test_sensor()
    test_registrador()
    test_actuador()
    test_alarmas()
    
    print("\n" + "="*80)
    print("TODOS LOS TESTS FINALIZARON CON ÉXITO")
    print("="*80)

if __name__ == "__main__":
    main()
