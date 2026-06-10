X = {ordenMedica:      [0, 200]}  x {In 0}   // del generador de órdenes médicas
  ∪ {sensorFlujo:      [0, 200]}  x {In 1}   // lectura del sensor de flujo
  ∪ {finBolsa:         {⊤}     }  x {In 2}   // señal del entorno
  ∪ {confirmEnfermero: {⊤}     }  x {In 3}   // confirmación del entorno

Y = {ajustarCaudal:   [0, 200]}  x {Out 0}   // → actuador
  ∪ {detenerBomba:    {⊤}     }  x {Out 1}   // → actuador
  ∪ {alarmaBaja:      {⊤}     }  x {Out 2}   // → moduloAlarmas
  ∪ {alarmaMedia:     {⊤}     }  x {Out 3}   // → moduloAlarmas
  ∪ {alarmaCritica:   {⊤}     }  x {Out 4}   // → moduloAlarmas
  ∪ {registrarEvento: {⊤}     }  x {Out 5}   // → ENTORNO

S = {"OCIOSO", "NORMAL", "CONTROLAR DESVIO", "ALERTA MEDIA",
     "BOLSA AGOTADA", "ESTADO CRITICO", "EMITIR SALIDA"}
  × [0, 200]
  × [0, 200]
  × ℝ⁺∪{0}
  × ℝ⁺∪{∞}
  × ℝ⁺∪{∞}
  × ({"ajustarCaudal","detenerBomba","alarmaBaja","alarmaMedia","alarmaCritica","registrarEvento"} × {0,1,2,3,4,5})
  [fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir]

ta(fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir) = σ

δext((fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir), e, (event, port)) =
    tBolsa = (tiempoBolsa == ∞) ? ∞ : tiempoBolsa - e

    switch (port) {
        case 0:
            // Llegó una orden médica con el nuevo caudal objetivo
            if (event == 0) {
                // Caudal 0 → detener la bomba
                ("EMITIR SALIDA", 0, caudalReal, 0, tBolsa, 0, ("detenerBomba", 1))
            }
            else {
                // Caudal positivo → ajustar el caudal
                ("EMITIR SALIDA", event, caudalReal, 0, tBolsa, 0, ("ajustarCaudal", 0))
            }

        case 1:
            // Llegó una lectura del sensor de flujo. event == caudalMedido
            hayDesvio = (caudalObjetivo > 0) && |event - caudalObjetivo| / caudalObjetivo > 0.10

            if (hayDesvio) {
                switch (fase) {
                    case "NORMAL":
                        // Desvío detectado por primera vez → esperar 5 s antes de alarma media
                        proximoSigma = min(tBolsa, 5)
                        ("CONTROLAR DESVIO", caudalObjetivo, event, 0, tBolsa, proximoSigma, eventoAEmitir)
                    case "CONTROLAR DESVIO":
                        // Desvío continúa; acumular tiempo transcurrido
                        ("CONTROLAR DESVIO", caudalObjetivo, event, tiempoConDesvio + e, tBolsa, σ - e, eventoAEmitir)
                    case "ALERTA MEDIA":
                        // En alerta media; acumular tiempo transcurrido
                        ("ALERTA MEDIA", caudalObjetivo, event, tiempoConDesvio + e, tBolsa, σ - e, eventoAEmitir)
                    case "BOLSA AGOTADA":
                        // Desvío mientras la bolsa se agota → priorizar control de desvío
                        proximoSigma = min(tBolsa, 5)
                        ("CONTROLAR DESVIO", caudalObjetivo, event, 0, tBolsa, proximoSigma, eventoAEmitir)
                    default:
                        // OCIOSO, ESTADO CRITICO, EMITIR SALIDA: ignorar lectura del sensor
                        (fase, caudalObjetivo, event, tiempoConDesvio, tBolsa, σ - e, eventoAEmitir)
                }
            }
            else {
                switch (fase) {
                    case "NORMAL":
                    case "CONTROLAR DESVIO":
                    case "ALERTA MEDIA":
                    case "BOLSA AGOTADA":
                        // Desvío resuelto. Determinar fase según estado de la bolsa
                        if (tBolsa != ∞) {
                            ("BOLSA AGOTADA", caudalObjetivo, event, 0, tBolsa, tBolsa, eventoAEmitir)
                        }
                        else {
                            ("NORMAL", caudalObjetivo, event, 0, ∞, ∞, eventoAEmitir)
                        }
                    default:
                        // OCIOSO, ESTADO CRITICO, EMITIR SALIDA: ignorar lectura del sensor
                        (fase, caudalObjetivo, event, tiempoConDesvio, tBolsa, σ - e, eventoAEmitir)
                }
            }

        case 2:
            // Señal de fin de bolsa: queda 1 minuto
            if (fase != "ESTADO CRITICO" && fase != "OCIOSO") {
                ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio, 60.0, 0, ("alarmaBaja", 2))
            }
            else {
                // En estado crítico u ocioso: ignorar
                (fase, caudalObjetivo, caudalReal, tiempoConDesvio, tBolsa, σ - e, eventoAEmitir)
            }

        case 3:
            // Confirmación del enfermero
            if (fase == "ESTADO CRITICO") {
                // Desbloquear la bomba y volver a ocioso
                ("OCIOSO", 0, 0, 0, tBolsa, ∞, eventoAEmitir)
            }
            else {
                // Ignorar en cualquier otro estado
                (fase, caudalObjetivo, caudalReal, tiempoConDesvio, tBolsa, σ - e, eventoAEmitir)
            }
    }

δint(fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir) =
    tiempoBolsaNuevo = (tiempoBolsa == ∞) ? ∞ : tiempoBolsa - σ
    switch (fase) {
        case "EMITIR SALIDA":
            switch (eventoAEmitir.puerto) {
                case 0:
                    // Emitió ajustarCaudal → pasar a estado operativo
                    proximaFase  = (tiempoBolsa < ∞) ? "BOLSA AGOTADA" : "NORMAL"
                    proximoSigma = (tiempoBolsa < ∞) ? tiempoBolsa : ∞
                    (proximaFase, caudalObjetivo, caudalReal, 0, tiempoBolsa, proximoSigma, eventoAEmitir)
                case 1:
                    // Emitió detenerBomba → determinar si fue por desvío crítico o por orden médica
                    if (tiempoConDesvio >= 10.0) {
                        ("ESTADO CRITICO", 0, 0, tiempoConDesvio, tiempoBolsa, ∞, eventoAEmitir)
                    }
                    else {
                        ("OCIOSO", 0, 0, 0, tiempoBolsa, ∞, eventoAEmitir)
                    }
                case 2:
                    // Emitió alarmaBaja → iniciar cuenta regresiva de la bolsa
                    ("BOLSA AGOTADA", caudalObjetivo, caudalReal, 0, tiempoBolsa, tiempoBolsa, eventoAEmitir)
                case 3:
                    // Emitió alarmaMedia → esperar 5 s más para alarma crítica
                    proximoSigma = min(tiempoBolsa, 5.0)
                    ("ALERTA MEDIA", caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, proximoSigma, eventoAEmitir)
                case 4:
                    // Emitió alarmaCritica → encadenar inmediatamente con detenerBomba
                    ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, 0, ("detenerBomba", 1))
                default:
                    ("OCIOSO", 0, 0, 0, tiempoBolsa, ∞, eventoAEmitir)
            }
        case "CONTROLAR DESVIO":
            // El desvío de 10% persistió 5 s → emitir alarma media
            if (tiempoBolsaNuevo == 0) {
                // Se llegó a la transición interna porque la bolsa llegó a 0 antes de los 5 segundos?
                ("EMITIR SALIDA", caudalObjetivo, caudalReal, 0, 0, 0, ("detenerBomba", 1))
            }
            else {
                // Se llegó a la transición por haber pasado los 5 segundos completos.
                ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio + σ, tiempoBolsaNuevo, 0, ("alarmaMedia", 3))
            }
        case "ALERTA MEDIA":
            if (tiempoBolsaNuevo == 0) {
                // Se llegó acá porque se agotó la bolsa
                ("EMITIR SALIDA", caudalObjetivo, caudalReal, 0, 0, 0, ("detenerBomba", 1))
            }
            else {
                // El desvío persistió 10 s en total → emitir alarma crítica
                ("EMITIR SALIDA", caudalObjetivo, caudalReal, tiempoConDesvio + 5.0, tiempoBolsaNuevo, 0, ("alarmaCritica", 4)) 
            }
        case "BOLSA AGOTADA":
            // Se agotó la bolsa → detener la bomba
            ("EMITIR SALIDA", caudalObjetivo, caudalReal, 0, 0, 0, ("detenerBomba", 1))
        default:
            // NORMAL, OCIOSO, ESTADO CRITICO: no tienen transición interna con σ finito
            (fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, eventoAEmitir)
    }

λ(fase, caudalObjetivo, caudalReal, tiempoConDesvio, tiempoBolsa, σ, (evento, puerto)) =
    if (fase == "EMITIR SALIDA") {
        (evento, puerto)
    }
    else {
        ∅
    }