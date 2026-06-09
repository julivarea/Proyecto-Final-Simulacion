X = [0, 200] x {In 0} U [0, 200] x {In 1} U {"finBolsa"} x {In 2} U {"confirmacionEnfermero"} x {In 3}
Y = {"ajustarCaudal"} x {Out 0} U {"detenerBomba"} x {Out 1} U {"alarmaBaja"} x {Out 2} U {"alarmaMedia"} x {Out 3} U {"alarmaCritica"} x {Out 4} U {"registrarEvento"} x {Out 5}
S = {"OCIOSO", "NORMAL", "CONTROLAR DESVIO", "ALERTA MEDIA", "BOLSA AGOTADA", "ESTADO CRITICO", "EMITIR SALIDA"} x [0, 200] x [0, 200] x ℝ+ x ℝ+ x ℝ+ x ({"ajustarCaudal", "detenerBomba", "alarmaBaja", "alarmaMedia", "alarmaCritica", "registrarEvento"} x {0, 1, 2, 3, 4, 5}) [fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir]
δext((fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir), elapsedTime, (event, port)) =
    nuevoTiempoBolsa = (tiempoBolsa == infinite) ? infinite : tiempoBolsa - elapsedTime
    switch (port) {
        case 0:
            // Llegó una orden médica. event == caudalObjetivo
            if (event == 0) {
                // Caudal 0. Detenemos la bolsa
                ("EMITIR SALIDA", 0, caudalReal, 0, nuevoTiempoBolsa, 0, ("detenerBomba", 1);
            }
            else {
                // Caudal != 0. Ajustamos el caudal
                ("EMITIR SALIDA", event, caudalReal, 0, nuevoTiempoBolsa, 0, ("ajustarCaudal", 0));
            }
        case 1:
            // Llego una señal del sensor de flujo con el nuevo caudal real medido. event == nuevoCaudal
            bool hayDesvio = (caudalObjetivo > 0) && |event-caudalObjetivo|/caudalObjetivo > 0.10
            
            if (hayDesvio) {
                switch (fase) {
                    case "NORMAL":
                        // Detectamos el desvío por primera vez. Dentro de 5 segundos emitimos alerta media
                        proximoSigma = (nuevoTiempoBolsa < 5) ? nuevoTiempoBolsa : 5
                        ("CONTROLAR DESVIO", caudalObjetivo, event, 0, nuevoTiempoBolsa, proximoSigma, eventoAEmitir);
                    case "CONTROLAR DESVIO":
                        // Seguimos en el estado de control de desvío acumulando el tiempo pasado con desvío
                        ("CONTROLAR DESVIO", caudalObjetivo, event, tiempoConDesvio + elapsedTime, nuevoTiempoBolsa,σ - elapsedTime, eventoAEmitir);
                    case "ALERTA MEDIA":
                        // Estamos en alerta media por haber pasado 5 segundos con desvío. Si pasamos otros 5 segundos, pasamos al estado crítico
                        ("ALERTA MEDIA", caudalObjetivo, event, tiempoConDesvio + elapsedTime, nuevoTiempoBolsa, σ - elapsedTime, eventoAEmitir);
                    case "BOLSA AGOTADA":
                        // Priorizamos controlar el desvío sin perder el reloj de la bolsa
                        proximoSigma = (nuevoTiempoBolsa < 5) ? nuevoTiempoBolsa : 5
                        ("CONTROLAR DESVIO", caudalObjetivo, event, 0, nuevoTiempoBolsa, proximoSigma, eventoAEmitir);
                }
            }
            else {
                switch (fase) {
                    case "CONTROLAR DESVIO":
                    case "ALERTA MEDIA":
                    case "NORMAL":
                    case "BOLSA AGOTADA":
                        // Si el caudal está bien pero la bolsa ya se estaba agotando, nos mantenemos en bolsa agotada
                        if (nuevoTiempoBolsa != infinite) {
                            ("BOLSA AGOTADA", caudalObjetivo, event, 0 , nuevoTiempoBolsa, nuevoTiempoBolsa, eventoAEmitir);
                        }
                        else {
                            // No se estaba agotando la bolsa pues el tiempo restante de la bolsa era infinito
                            ("NORMAL", caudalObjetivo, event, 0, infinite, infinite, eventoAEmitir);
                        }
                    default:
                        (fase, caudalObjetivo, event, tiempoConDesvio, nuevoTiempoBolsa, σ - elapsedtime, eventoAEmitir);
                        
                        
                }
            }
        case 2:
            // Recibimos una señal de fin de bolsa
            if (fase != "ESTADO CRITICO" && fase != "OCIOSO") {
                 ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio, 60.0, 0 ("alarmaBaja", 2));
            }
            else {
                (fase, caudalObjetivo, caudalReal, tiempoConDesvio, nuevoTiempoBolsa, σ - elapsedTime, eventoAEmitir);
            }
        case 3:
            // Recibimos la confirmación del enfermero
            if (fase == "ESTADO CRITICO") {
                // Desbloqueamos la bomba y volvemos al estado ocioso
                ("OCIOSO", 0, 0, 0, nuevoTiempoBolsa, infinite, eventoAEmitir);
            }
            else {
                (fase, caudalObjetivo, caudalReal, tiempoConDesvio, nuevoTiempoBolsa, σ - elapsedTime, eventoAEmitir);
            }
    }
δint((fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir)) =
    switch (fase) {
        case "EMITIR SALIDA":
            switch (eventoAEmitir.puerto) {
                case 0:
                    // Ajustar caudal
                    proximaFase = (tiempoBolsa == infinite) ? "NORMAL" : "BOLSA AGOTADA"
                    proximoSigma = (tiempoBolsa == infinite) ? infinite : tiempoBolsa
                    (proximaFase, caudalObjetivo, caudalReal, 0, tiempoBolsa, proximoSigma, eventoAEmitir)
                case 1:
                    // Detener bomba
                    if (tiempoConDesvio >= 10.0) {
                        ("ESTADO CRITICO", 0, 0, tiempoConDesvio, tiempoBolsa, infinite, eventoAEmitir);
                    }
                    else {
                        ("OCIOSO", 0, 0, 0, tiempoBolsa, infinite, eventoAEmitir);
                    }
                case 2:
                    // alarmaBaja
                    ("BOLSA AGOTADA", caudalObjetivo, caudalReal, 0, tiempoBolsa, tiempoBolsa, eventoAEmitir);
                case 3:
                    // alarmaMedia. Entramos a la etapa de alerta media
                    proximoSigma = (tiempoBolsa < 5.0) ? tiempoBolsa : 5.0
                    ("ALERTA MEDIA", caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, proximoSigma, eventoAEmitir);
                case 4:
                    // alarmaCritica. Encadenamos dos salidas
                    ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, 0, ("detenerBomba", 1))
                default:
                    ("OCIOSO", 0, 0, 0, tiempoBolsa, infinite, eventoAEmitir);
            }
        case "CONTROLAR DESVIO":
            // Si llegamos acá es porque el desvío de 10% persistió 5 segundos.
            ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio + σ, tiempoBolsa, 0, ("alarmaMedia", 3))
        case "ALERTA MEDIA":
            // Si se agota el tiempo acá es porque el desvío persistió 10 segundos y hay que pasar al estado crítico
            ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio + 5.0, tiempoBolsa, 0, ("alarmaCritica", 4))
        case "BOLSA AGOTADA":
            ("EMITIR SALIDA", caudalObjetivo, caudalReal, 0, 0, 0, ("detenerBomba", 1))
        default:
            (fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir)
        
    }
λ(fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, (evento, puerto)) =
    if (fase == "EMITIR SALIDA") {
        (evento, puerto);
    }
    else {
        NADA;
    }
ta(fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir) = σ