# Configuración del Entorno de Desarrollo

## Creación del entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

## Instalación de dependencias estándar

```bash
pip install numpy matplotlib pandas pytest
```

## Instalación Manual de PythonPDEVS

Dado que PythonPDEVS no se encuentra disponible en los repositorios oficiales de PyPI y los scripts de instalación antiguos dependen del módulo deprecado `distutils`, realiza la instalación moderna desde el código fuente original:

```bash
# 1. Clonar el repositorio fuente de PythonPDEVS
git clone https://github.com/capocchi/PythonPDEVS.git

# 2. Instalar setuptools en el entorno virtual para soporte de empaquetado
pip install setuptools

# 3. Entrar al directorio del código fuente
cd PythonPDEVS/src

# 4. Instalar de manera local y moderna el paquete usando pip
pip install .

# 5. Regresar a la raíz del proyecto y limpiar los archivos temporales de instalación
cd ../..
rm -rf PythonPDEVS/
```

## Congelar las dependencias del proyecto

```bash
pip freeze > requirements.txt
```

## Ejecución de las Pruebas

Las pruebas del proyecto han sido migradas al framework `pytest`. Para ejecutar la suite de pruebas, asegúrate de tener el entorno virtual activado y sitúate en la raíz del proyecto (`bomba_infusion_pdevs/`).

```bash
# 1. Activar el entorno virtual (si no lo has hecho aún)
source venv/bin/activate

# 2. Ejecutar absolutamente TODO (Unitarios + Escenarios)
python3 -m pytest tests/

# Opcional: Ejecutar SOLO los tests unitarios (componentes aislados)
python3 -m pytest tests/unit/

# Opcional: Ejecutar SOLO los escenarios controlados (integración formal)
python3 -m pytest tests/scenarios/controlled/
```

**Tips útiles:**
- Agrega `-s` para habilitar el output de `print()` interno durante las simulaciones: `python3 -m pytest -s tests/`
- Agrega `-v` para obtener un detalle exhaustivo (verbose) de cada caso de prueba: `python3 -m pytest -v tests/`
