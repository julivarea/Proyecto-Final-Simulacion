import pytest
import sys
import os
import random
import pypdevs

sys.path.append(os.path.dirname(pypdevs.__file__))

from pypdevs.minimal import AtomicDEVS
if not hasattr(AtomicDEVS, "__lt__"):
    AtomicDEVS.__lt__ = lambda self, other: id(self) < id(other)

# Aseguramos que los imports desde src funcionen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import src.models.atomic.sensor_flujo as sf
from src.models.coupled.bomba_acoplada import BombaAcoplada

@pytest.fixture(autouse=True)
def reset_globals():
    """
    Resetea el estado global antes de cada test para asegurar aislamiento.
    """
    random.seed(42)
    sf.PORCENTAJE_RUIDO_SENSOR = 0.20

@pytest.fixture
def bomba_model():
    """Retorna una instancia limpia del modelo acoplado de la bomba."""
    return BombaAcoplada(name="Bomba_Test")

@pytest.fixture
def simulation_runner():
    """Retorna la clase ScenarioRunner para configurar simulaciones."""
    from tests.helpers.scenario_runner import ScenarioRunner
    return ScenarioRunner

@pytest.fixture
def property_checker():
    """Retorna el módulo de property checkers para ser usado en los tests."""
    import tests.helpers.property_checkers as checkers
    return checkers
