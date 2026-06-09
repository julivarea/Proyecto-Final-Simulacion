X = {alarmaBaja}            x {In 0}
  ∪ {alarmaMedia}           x {In 1}
  ∪ {alarmaCritica}         x {In 2}
  ∪ {confirmEnfermero}      x {In 3}

Y = {"BAJA", "MEDIA", "CRITICA"} x {Out 0}

S = {"OCIOSO", "NOTIFICAR ALARMA", "ESPERANDO CONFIRMACION", "REPETIR ALARMA"}
  × {"NINGUNA", "BAJA", "MEDIA", "CRITICA"}
  × ℝ⁺∪{∞}
  [fase, alarmaActiva, σ]

ta(fase, alarmaActiva, σ) = σ

δext((fase, alarmaActiva, σ), e, (event, port)) =
    switch (port) {
        // Cada puerto corresponde a un único tipo de alarma; no es necesario leer event
        case 0: ("NOTIFICAR ALARMA", "BAJA",    0)
        case 1: ("NOTIFICAR ALARMA", "MEDIA",   0)
        case 2: ("NOTIFICAR ALARMA", "CRITICA", 0)
        case 3:
            // Confirmación del enfermero
            if (alarmaActiva == "CRITICA") {
                ("OCIOSO", "NINGUNA", ∞)        // silenciar alarma crítica
            }
            else {
                (fase, alarmaActiva, σ - e)     // no hay alarma crítica activa; ignorar
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