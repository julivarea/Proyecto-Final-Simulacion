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

def normal(media, varianza):
    """
    Genera un valor con distribución Normal(media, varianza).
    La varianza es sigma^2, por lo que internamente se usa sqrt(varianza) como desvío estándar.
    """
    import math
    desvio_estandar = math.sqrt(varianza)
    return random.gauss(media, desvio_estandar)