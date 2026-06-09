X = {ajustarCaudal: [0, 200]}   x {In 0}
  ∪ {detenerBomba}              x {In 1}

Y = {caudalActual:  [0, 200]}   x {Out 0}

S = [0, 200]
  × [0, 200]
  × ℝ⁺∪{∞}
  [caudalReal, caudalAEnviar, σ]

// Latencia física del actuador: nuevoTiempo() ∈ [0, 0.5] s

ta(caudalReal, caudalAEnviar, σ) = σ

δext((caudalReal, caudalAEnviar, σ), e, (event, port)) =
    switch (port) {
        case 0: (caudalReal, event, nuevoTiempo())   // ajustarCaudal
        case 1: (caudalReal, 0,     nuevoTiempo())   // detenerBomba
    }

δint(caudalReal, caudalAEnviar, σ) =
    // Aplica el caudal pendiente; queda pasivo hasta la próxima orden
    (caudalAEnviar, caudalAEnviar, ∞)

λ(caudalReal, caudalAEnviar, σ) = (caudalAEnviar, Out 0)
