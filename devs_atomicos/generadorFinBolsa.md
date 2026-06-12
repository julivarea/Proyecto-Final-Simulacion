X = {caudalMedido:  [0, 200]}   x {In 0}   // del Sensor de Flujo
  ∪ {rellenarBolsa: {⊤}}       x {In 1}   // señal de relleno (del Controlador u otro)

Y = {finBolsa: {⊤}}            x {Out 0}  // → al Controlador de Bomba

S = {"MONITOREANDO", "ESPERANDO RELLENO"}
  × ℝ⁺∪{0}           // volumenRestante (ml)
  × [0, 200]          // ultimoCaudal (ml/h)
  × ℝ⁺∪{∞}           // σ
  [fase, volumenRestante, ultimoCaudal, σ]

// Constantes:
//   VOL_INICIAL    = 500.0 ml  (capacidad de la bolsa, parametrizable)
//   UMBRAL_ALERTA  = 60.0 s    (anticipación de la señal)

s₀ = ("MONITOREANDO", VOL_INICIAL, 0.0, ∞)

ta(fase, volumenRestante, ultimoCaudal, σ) = σ

// Funciones auxiliares:
//   descuento(vol, caudal, e) = max(vol - caudal * (e / 3600), 0)
//   calcularSigma(vol, caudal) =
//       si caudal == 0 → ∞
//       si vol / (caudal / 3600) ≤ UMBRAL_ALERTA → 0
//       sino → vol / (caudal / 3600) - UMBRAL_ALERTA

δext((fase, volumenRestante, ultimoCaudal, σ), e, (event, port)) =
    volActual = descuento(volumenRestante, ultimoCaudal, e)

    switch (port) {
        case 0:  // caudalMedido del Sensor de Flujo
            if (fase == "ESPERANDO RELLENO") {
                // Ya emitimos finBolsa; solo actualizamos caudal, σ queda ∞
                ("ESPERANDO RELLENO", volActual, event, ∞)
            }
            else {
                // fase == "MONITOREANDO"
                ("MONITOREANDO", volActual, event, calcularSigma(volActual, event))
            }

        case 1:  // rellenarBolsa
            ("MONITOREANDO", VOL_INICIAL, ultimoCaudal,
             calcularSigma(VOL_INICIAL, ultimoCaudal))
    }

δint(fase, volumenRestante, ultimoCaudal, σ) =
    // λ acaba de emitir finBolsa. Pasamos a esperar el relleno.
    ("ESPERANDO RELLENO", volumenRestante, ultimoCaudal, ∞)

λ(fase, volumenRestante, ultimoCaudal, σ) =
    if (fase == "MONITOREANDO") {
        (⊤, Out 0)     // finBolsa
    }
    else {
        ∅
    }
