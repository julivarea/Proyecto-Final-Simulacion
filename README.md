# Proyecto Final — Simulación

**Facultad de Ciencias Exactas, Físico-Químicas y Naturales** **Universidad Nacional de Río Cuarto (UNRC)** **Año: 2026**

---

## Integrantes

| Apellido y Nombre          |
| -------------------------- |
| Alieni, Agustín            |
| Varea Grosso, Julián Lucas |

---

## Descripción

Modelo de simulación de una **bomba de infusión intravenosa** desarrollado con la metodología **DEVS (Discrete Event System Specification)** bajo la formalización **CML-DEVS**.

---

## Arquitectura del proyecto

```
Proyecto Final Simulación/
│
├── README.md              ← Este archivo
├── pytest.ini             ← Archivo de configuracion para pruebas con Pytest
├── bomba_infusion_pdevs/  ← Logica del modelo, experimentos, simulacion y tests│
├── docs/                  ← Enunciado oficial y especificaciones de la catedra
├── latex/                 ← Fuentes del informe escrito
```

### Detalle de los componentes

#### `bomba_infusion_pdevs/`

Es el núcleo de desarrollo del proyecto. Contiene la totalidad de los archivos de código fuente organizados en:

- **Lógica de DEVS:** Implementación del comportamiento y acoplamiento de la bomba de infusión.
- **Experimentos y Simulación:** Escenarios configurados para ejecutar el modelo y evaluar su comportamiento ante diferentes eventos discretos.
- **Tests:** Suite de pruebas encargadas de validar que la lógica de las transiciones y funciones del sistema respondan de acuerdo a la formalización requerida.

#### `docs/`

Contiene la documentación complementaria y el enunciado del proyecto final entregado por el cuerpo docente, el cual detalla los requisitos funcionales mínimos y las pautas de evaluación.

#### `latex/`

Repositorio de los archivos fuente en formato LaTeX para la redacción del trabajo académico. El archivo **`latex/main.pdf`** constituye el informe técnico final listo para la revisión de esta entrega.

---
