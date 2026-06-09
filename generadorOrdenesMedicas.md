X = Vacío

Y = [0,200] x {Out 0} // Caudal entre 0 y 200 ml/h

S = [0,200] x ℝ+ // [caudal, σ]

ta(caudal, σ) = σ

δint((caudal, σ)) = (nuevoCaudal(), nuevoTiempo())

δext = indefinida   // No recibe eventos externos

λ(caudal, σ) = (caudal, Out 0)