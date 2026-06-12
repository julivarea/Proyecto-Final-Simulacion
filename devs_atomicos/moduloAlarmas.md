X = {alarmaBaja}            x {In 0}
  ∪ {alarmaMedia}           x {In 1}
  ∪ {alarmaCritica}         x {In 2}
  ∪ {confirmEnfermero}      x {In 3}

Y = {"BAJA", "MEDIA", "CRITICA"} x {Out 0}

S = {"OCIOSO", "NOTIFICAR ALARMA", "ESPERANDO CONFIRMACION", "REPETIR ALARMA"}
  × {"NINGUNA", "BAJA", "MEDIA", "CRITICA"}
  × ℝ⁺∪{∞}
  [fase, alarmaActiva, σ]

// Variables del estado:
//   fase:         fase actual del módulo
//   alarmaActiva: tipo de alarma que se está gestionando
//   σ:            tiempo hasta la próxima transición interna

// Función auxiliar de prioridad:
//   prio(a): NINGUNA → 0, BAJA → 1, MEDIA → 2, CRITICA → 3

s₀ = ("OCIOSO", "NINGUNA", ∞)

ta(fase, alarmaActiva, σ) = σ

δext((fase, alarmaActiva, σ), e, (event, port)) =
    switch (port) {
        case 0: nuevaAlarma = "BAJA"
        case 1: nuevaAlarma = "MEDIA"
        case 2: nuevaAlarma = "CRITICA"
        case 3:
            // Confirmación del enfermero
            if (alarmaActiva == "CRITICA") {
                ("OCIOSO", "NINGUNA", ∞)        // silenciar alarma crítica
            }
            else {
                (fase, alarmaActiva, σ - e)     // no hay alarma crítica activa; ignorar
            }
    }

    // Para ports 0, 1, 2: aplicar guarda de prioridad
    if (port != 3) {
        if (fase == "OCIOSO" || prio(nuevaAlarma) > prio(alarmaActiva)) {
            ("NOTIFICAR ALARMA", nuevaAlarma, 0)
        }
        else {
            // Alarma de menor o igual prioridad mientras hay una activa: ignorar
            (fase, alarmaActiva, σ - e)
        }
    }

δint(fase, alarmaActiva, σ) =
    switch (fase) {
        case "NOTIFICAR ALARMA":
            switch (alarmaActiva) {
                case "BAJA":
                case "MEDIA":
                    // Alarmas no críticas: se notifican una sola vez y el módulo vuelve a ocioso
                    ("OCIOSO", "NINGUNA", ∞)
                case "CRITICA":
                    // Primera notificación emitida → esperar confirmación del enfermero por 30 s
                    ("ESPERANDO CONFIRMACION", "CRITICA", 30)
            }
        case "ESPERANDO CONFIRMACION":
            // Pasaron 30 s sin confirmación → volver a notificar inmediatamente (σ = 0)
            ("REPETIR ALARMA", "CRITICA", 0)
        case "REPETIR ALARMA":
            // Repetir la notificación cada 10 s hasta recibir confirmación
            ("REPETIR ALARMA", "CRITICA", 10)
    }

λ(fase, alarmaActiva, σ) =
    if (fase == "NOTIFICAR ALARMA" || fase == "REPETIR ALARMA") {
        // En ESPERANDO CONFIRMACION no se emite: solo se aguarda al enfermero
        (alarmaActiva, Out 0)
    }
    else {
        ∅
    }