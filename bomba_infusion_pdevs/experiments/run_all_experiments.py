import sys
import os

# Agregamos el path raíz para que se puedan importar los módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sim_01_normal
import sim_02_cambio_orden
import sim_03_detencion
import sim_04_desvio_leve
import sim_05_desvio_mayor
import sim_06_fin_bolsa
import sim_07_alarma_critica

def main():
    print("==================================================")
    print("EJECUTANDO TODOS LOS ESCENARIOS DE LA BOMBA DE INFUSIÓN")
    print("==================================================\n")

    escenarios = [
        ("Escenario 1: Funcionamiento normal", sim_01_normal.ejecutar_escenario_01),
        ("Escenario 2: Cambio de orden", sim_02_cambio_orden.ejecutar_escenario_02),
        ("Escenario 3: Detención", sim_03_detencion.ejecutar_escenario_03),
        ("Escenario 4: Desvío leve", sim_04_desvio_leve.ejecutar_escenario_04),
        ("Escenario 5: Desvío mayor", sim_05_desvio_mayor.ejecutar_escenario_05),
        ("Escenario 6: Fin de bolsa", sim_06_fin_bolsa.ejecutar_escenario_06),
        ("Escenario 7: Alarma crítica no confirmada", sim_07_alarma_critica.ejecutar_escenario_07)
    ]

    for nombre, funcion in escenarios:
        print(f"\n>>>>> {nombre} <<<<<")
        print("-" * 50)
        try:
            funcion()
        except Exception as e:
            print(f"Error al ejecutar {nombre}: {e}")
        print("=" * 50)

    print("\nTODOS LOS ESCENARIOS HAN SIDO EJECUTADOS.")

if __name__ == '__main__':
    main()
