X = [0,200] x {In 0}
Y = [0, 200] x {Out 0}
S = [0,200] x ℝ+
λ(caudal, σ) = caudal
ta = σ
δext((caudalRegistrado, σ), elapsedTime, (nuevoCaudal, 0)) = (nuevoCaudal, σ - elapsedTime)
δint((caudalRegistrado, σ)) = (caudalRegistrado, 1)