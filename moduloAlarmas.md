X = {"alarmaBaja"} x {In 0} U {"alarmaMedia"} x {In 1}, {"alarmaCrítica"} x {In 2}, {"confirmaciónEnfermero"} x {In 3}
Y = {"BAJA", "MEDIA", "CRÍTICA"} x {Out 0}
S = {"OCIOSO", "NOTIFICAR ALARMA", "ESPERANDO CONFIRMACION", "REPETIR ALARMA"} x {"NINGUNA", "BAJA", "MEDIA", "CRÍTICA"} x ℝ+ [fase, alarmaActiva, σ]
δext((fase, alarmaActiva, σ), elapsedTime, (event, port) =
    if (port == 0 || port == 1 || port == 2) {
        // Llegó una alarma. event es una alarma baja, media o crítica
        switch (event) {
            case "alarmaBaja": ("NOTIFICAR ALARMA", "BAJA", 0);
            case "alarmaMedia": ("NOTIFICAR ALARMA", "MEDIA", 0);
            case "alarmaCritica": ("NOTIFICAR ALARMA", "CRITICA", 0);
            default: ("OCIOSO", "NINGUNA", infinite);
        }
    }
    if (port == 3) {
        // Llegó una confirmación del enfermero
        if (alarmaActiva == "CRITICA") {
            ("OCIOSO", "NINGUNA", infinite);
        }
    }
δint((fase, alarmaActiva, σ)) = 
    switch (alarmaActiva) {
        case "BAJA": ("OCIOSO", "NINGUNA", infinite);
        case "MEDIA": ("OCIOSO", "NINGUNA", infinite);
        case "CRITICA": 
            if (fase == "NOTIFICAR_ALARMA") {
                // Estamos notificando la alarma crítica por primera vez. Esperamos confirmación durante 30 segundos
                ("ESPERANDO CONFIRMACIÓN", "CRITICA", 30);
            }
            else if (fase == "ESPERANDO CONFIRMACION") {
                // Pasaron 30 segundos sin confirmación. Empezamos a repetir la alarma
                ("REPETIR ALARMA", "CRITICA", 10);
            }
            else if (fase == "REPETIR ALARMA") {
                ("REPETIR ALARMA", "CRITICA", 10);
            }
    }
λ((fase, alarmaActiva, σ)) = 
    if (fase == "NOTIFICAR ALARMA" || fase == "REPETIR ALARMA" || fase == "ESPERANDO_CONFIRMACION") {
        // Emitimos la alarma cuando se agota el tiempo en alguna de las etapas de alerta (no ociosas)
        (alarmaActiva, 0) 
    }
    else {
        NADA
    }
ta((fase, alarmaActiva, σ)) = σ