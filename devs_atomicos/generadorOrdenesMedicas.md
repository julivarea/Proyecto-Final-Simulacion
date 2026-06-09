X = ∅

Y = {ordenMedica: [0, 200]}   // ml/h — Out 0

S = [0, 200]
  × ℝ⁺∪{∞}
  [caudal, σ]

ta(caudal, σ) = σ

δint(caudal, σ) = (nuevoCaudal(), nuevoTiempo())

δext = indefinida   // No recibe eventos externos

λ(caudal, σ) = (caudal, Out 0)


nuevoCaudal() y nuevoTiempo() generan estocásticamente dichos parámetros