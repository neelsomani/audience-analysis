from models import Signal
from typing import Dict

from attribute_calculators.attribute_calculator import AttributeCalculator


class LocationCalculator(AttributeCalculator):
    """ Return the provided location. """
    def calculate(self, signal: Signal) -> Dict:
        return {
            'location': signal.location
        }
