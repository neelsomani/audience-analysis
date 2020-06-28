from abc import ABC
from models import Signal
from typing import Dict


class AttributeCalculator(ABC):
    """ Calculate an arbitrary attribute from a set of signals. """
    def calculate(self, signal: Signal) -> Dict:
        raise NotImplementedError
