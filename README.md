# Proyecto Final — Simulación

**Facultad de Ciencias Exactas, Físico-Químicas y Naturales**
**Universidad Nacional de Río Cuarto (UNRC)**
**Año: 2026**

---

## Integrantes

| Apellido y Nombre          |
|---------------------------|
| Alieni, Agustín           |
| Varea Grosso, Julián Lucas |

---

## Descripción

Modelo de simulación de una **bomba de infusión intravenosa** desarrollado con la metodología **DEVS (Discrete Event System Specification)** bajo la formalización **CML-DEVS**.

---

## Diagrama del sistema

> [!IMPORTANT]
> [Ver diagrama en Miro](https://miro.com/app/board/uXjVHIbDhYc=/?share_link_id=995767639722)

---

## Arquitectura del proyecto

```
Proyecto Final Simulación/
│
├── README.md                        ← Este archivo
│
├── docs/                            ← Documentación y referencias
│   ├── Proyecto_Bomba_Infusion_Promocionar.pdf
│   └── Tesis_HollmannDiego_137813910453.pdf
│
└── devs_atomicos/                   ← Especificaciones de los modelos atómicos DEVS
    ├── sensorFlujo.md
    ├── controladorBomba.md
    ├── moduloAlarmas.md
    ├── actuador.md
    └── generadorOrdenesMedicas.md
```

### `docs/`

Contiene la documentación de referencia del proyecto:

- **`Proyecto_Bomba_Infusion_Promocionar.pdf`** — Enunciado y requisitos funcionales del sistema a modelar.
- **`Tesis_HollmannDiego_137813910453.pdf`** — Tesis de referencia para la formalización CML-DEVS utilizada en el modelo.

### `devs_atomicos/`

Contiene la especificación formal de cada modelo atómico del sistema, siguiendo la notación CML-DEVS. Cada archivo describe el estado, puertos, funciones de transición y salida del componente correspondiente:

| Archivo                       | Componente                  |
|------------------------------|-----------------------------|
| `sensorFlujo.md`             | Sensor de flujo             |
| `controladorBomba.md`        | Controlador de la bomba     |
| `moduloAlarmas.md`           | Módulo de alarmas           |
| `actuador.md`                | Actuador                    |
| `generadorOrdenesMedicas.md` | Generador de órdenes médicas|

---

## Referencias

- Hollmann, D. — *Tesis doctoral sobre CML-DEVS* (ver `docs/`)
- Enunciado del proyecto final (ver `docs/`)
