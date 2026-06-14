# Configuración del Entorno de Desarrollo

## Creación del entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

## Instalación de dependencias estándar

```bash
pip install numpy matplotlib pandas
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
