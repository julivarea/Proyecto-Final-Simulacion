import random

def uniforme(a, b):
    """Genera un valor con distribución uniforme entre a y b."""
    return random.uniform(a, b)

def exponencial(tasa):
    """
    Genera un valor con distribución exponencial.
    Nota: la 'tasa' equivale a lambda (ej. 1/300.0).
    """
    return random.expovariate(tasa)