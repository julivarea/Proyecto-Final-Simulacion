X = [0,200] x {In 0} U {"detenerBomba"} x {In 1}

Y = [0,200] x {Out 0}

S = [0,200] x [0,200] x ℝ+ [caudalReal, caudalAEnviar, σ]

ta((caudalReal, caudalAEnviar, σ)) = σ

δext((caudalReal, caudalAEnviar, σ), elapsedTime, (event, port)) =
    switch (port) {
        // Latencia física del actuador: nuevoTiempo() ∈ [0, 0.5] s
        case 0:
            // Llegó un nuevo caudal objetivo (ajustarCaudal)
            (caudalReal, event, nuevoTiempo())
        case 1:
            // Llegó una señal de detención (detenerBomba)
            (caudalReal, 0, nuevoTiempo())
    }

δint((caudalReal, caudalAEnviar, σ)) =
    // Aplica el caudal pendiente; queda pasivo hasta la próxima orden
    (caudalAEnviar, caudalAEnviar, ∞)

λ((caudalReal, caudalAEnviar, σ)) = (caudalAEnviar, Out 0)
