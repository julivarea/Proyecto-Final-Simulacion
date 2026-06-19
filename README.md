# Proyecto Final — Simulación

**Facultad de Ciencias Exactas, Físico-Químicas y Naturales**
**Universidad Nacional de Río Cuarto (UNRC)**
**Año:** 2026
**Profesor:** Ariel González

---

## Integrantes

* Alieni, Agustín
* Varea Grosso, Julián Lucas

---

## Descripción

Modelo de simulación de una **bomba de infusión intravenosa** desarrollado con la metodología **DEVS (Discrete Event System Specification)** bajo la herramienta de simulación **PyPDEVS**. Este sistema de lazo cerrado incorpora el comportamiento de controladores lógicos, sensores de flujo con inyección de ruido gaussiano y actuadores mecánicos, permitiendo validar el estricto cumplimiento de propiedades de seguridad (Safety) y vivacidad (Liveness) en un entorno médico crítico.

---

## Arquitectura del Proyecto

```text
Proyecto Final Simulación/
│
├── bomba_infusion_pdevs/  ← Núcleo del modelo y simulaciones
│   ├── src/               ← Código fuente principal
│   │   ├── models/        ← Modelos DEVS atómicos y acoplados globales
│   │   └── utils/         ← Monitores pasivos, métricas y distribuciones estadísticas
│   ├── tests/             ← Suite integral de validación
│   │   ├── unit/          ← Pruebas unitarias de las funciones de transición por componente
│   │   ├── scenarios/     ← Escenarios clínicos controlados y simulaciones estocásticas
│   │   └── helpers/       ← Orquestador (ScenarioRunner) y Property Checkers
│   ├── experiments/       ← Scripts de ejecución directa de los escenarios
│   └── analysis/          ← Scripts para procesar métricas y generar los gráficos finales
│
├── docs/                  ← Enunciado oficial y especificaciones de la cátedra
├── latex/                 ← Código fuente LaTeX del informe técnico escrito
├── pytest.ini             ← Configuración de la suite automatizada de pruebas
└── README.md              ← Este archivo descriptivo
```

### Detalle de los Componentes

* **`src/models/`**: Contiene la implementación formal de los 8 modelos atómicos DEVS y el modelo acoplado que los conecta.
* **`tests/helpers/`**: Aloja el `ScenarioRunner`, que inyecta fallas y órdenes mediante *monkey patching* sin alterar la base formal, y los `PropertyCheckers`, encargados de validar matemática y automáticamente el cumplimiento de los tiempos límite.
* **`latex/`**: Archivos fuente para la redacción del trabajo académico. El archivo final unificado se compila en `latex/main.pdf`.

---

## Guía de Ejecución

A continuación se detallan los comandos necesarios para configurar el entorno y ejecutar las simulaciones, validaciones y compilaciones del proyecto. 

### 1. Entorno de Ejecución (Python)
Para ejecutar este proyecto, es recomendable utilizar la terminal nativa de Linux, **WSL (Windows Subsystem for Linux)** o PowerShell. 

```bash
# Crear el entorno virtual de Python
python -m venv venv

# Activar el entorno virtual (Windows PowerShell)
.\venv\Scripts\activate
# O activar en WSL/Linux:
# source venv/bin/activate

# Instalar todas las dependencias requeridas (PyPDEVS, pytest, matplotlib, etc)
pip install -r requirements.txt
```

### 2. Ejecución de Tests y Escenarios
El proyecto utiliza la herramienta `pytest` para orquestar la suite de pruebas unitarias y los escenarios de integración sistémica.

```bash
# Ejecutar la suite completa de pruebas (unitarias, determinísticas y estocásticas)
pytest

# Ejecutar un escenario específico (por ejemplo, el escenario número 3 de oclusión)
pytest bomba_infusion_pdevs/tests/scenarios/controlled/test_scenario_3_oclusion.py
```

### 3. Ejecución de Análisis y Herramientas Auxiliares
Existen scripts dedicados a la ejecución manual paso a paso de los modelos para su análisis y *debugging*, así como scripts para dibujar los resultados.

```bash
# Ejecutar una simulación manual con salida paso a paso por consola (debugging)
python bomba_infusion_pdevs/run_trace.py

# Generar y guardar los gráficos de la simulación (Caudal vs. Tiempo, Alarmas, etc)
python bomba_infusion_pdevs/analysis/generar_graficos.py
```

### 4. Compilación del Informe en LaTeX
Para construir el documento en PDF a partir de los códigos fuente, es necesario contar con un compilador de LaTeX instalado en el sistema (como TeX Live o MiKTeX).

```bash
# Ingresar al directorio del informe
cd latex

# Ejecutar la compilación del documento principal
pdflatex main.tex
```
