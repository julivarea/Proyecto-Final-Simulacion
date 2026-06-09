X = [0,200] x {In 0}

Y = [0,200] x {Out 0}

S = [0,200] x ℝ+ [caudalRegistrado, σ]

// El sensor muestrea periódicamente cada 1 segundo.
// Si el actuador cambia el caudal, actualiza su registro
// pero no adelanta el reporte: espera el próximo tick.

ta(caudalRegistrado, σ) = σ

δext((caudalRegistrado, σ), elapsedTime, (nuevoCaudal, 0)) =
    (nuevoCaudal, σ - elapsedTime)

δint((caudalRegistrado, σ)) = (caudalRegistrado, 1)

λ(caudalRegistrado, σ) = (caudalRegistrado, Out 0)