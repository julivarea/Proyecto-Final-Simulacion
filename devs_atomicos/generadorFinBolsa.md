X = {caudalMedido:  [0, 200]}   x {In 0}   // del Sensor de Flujo
  ∪ {rellenarBolsa: {⊤}}       x {In 1}   // señal de relleno (del Controlador u otro)

Y = {finBolsa: {⊤}}            x {Out 0}  // → al Controlador de Bomba

S = {"MONITOREANDO", "ESPERANDO RELLENO"}
  × ℝ⁺∪{0}           // volRest: volumen restante de líquido en la bolsa (ml)
  × [0, 200]          // q: último caudal medido informado por el sensor (ml/h)
  × ℝ⁺∪{∞}           // σ: tiempo hasta la próxima transición interna
  [fase, volRest, q, σ]

// Constantes:
//   VOL_INICIAL    = 500.0 ml  (capacidad de la bolsa, parametrizable)
//   UMBRAL_ALERTA  = 60.0 s    (anticipación de la señal)

s₀ = ("MONITOREANDO", VOL_INICIAL, 0.0, ∞)

ta(fase, volRest, q, σ) = σ

// Funciones auxiliares:
//   vol'(volRest, q, e): descuenta el volumen consumido durante 'e' segundos al caudal q
//       = max(volRest - q * (e / 3600), 0)
//
//   σ̂(v, q): calcula cuánto falta para emitir la alerta dado un volumen y un caudal
//       si q == 0 → ∞
//       si v / (q / 3600) ≤ UMBRAL_ALERTA → 0
//       sino → v / (q / 3600) - UMBRAL_ALERTA

δext((fase, volRest, q, σ), e, (Xv, port)) =
    v' = vol'(volRest, q, e)

    switch (port) {
        case 0:  // caudalMedido del Sensor de Flujo
            if (fase == "ESPERANDO RELLENO") {
                ("ESPERANDO RELLENO", v', Xv, ∞)
            }
            else {
                ("MONITOREANDO", v', Xv, σ̂(v', Xv))
            }

        case 1:  // rellenarBolsa
            ("MONITOREANDO", VOL_INICIAL, q, σ̂(VOL_INICIAL, q))
    }

δint(fase, volRest, q, σ) =
    // λ acaba de emitir finBolsa. Pasamos a esperar el relleno.
    ("ESPERANDO RELLENO", volRest, q, ∞)

λ(fase, volRest, q, σ) =
    if (fase == "MONITOREANDO") {
        (⊤, Out 0)     // finBolsa
    }
    else {
        ∅
    }
