X = [0,200] x {In 0} U ("detenerBomba") x {In 1}
Y = [0,200] x {Out 0}
S = [0,200] x [0,200] x ℝ+ [caudalReal, caudalAEnviar, σ]
ta((caudalReal, caudalAEnviar, σ)) = σ
δext((caudalReal, caudalAEnviar, σ), elapsedTime, (event, port)) =
        (nuevoCaudal, 0) = (caudalReal, nuevoCaudal, nuevoTiempo())
        ("detenerBomba", 1) = (caudalReal, 0, nuevoTiempo())
λ((caudalReal, caudalAEnviar, σ)) = (caudalActual, 0)
δint((caudalReal, caudalAEnviar, σ)) = 
    (caudalAEnviar, caudalAEnviar, infinito)
