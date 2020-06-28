from models import Signal
from typing import Dict
import re
import requests

from attribute_calculators.attribute_calculator import AttributeCalculator
from util import get_urls_from_string


class EmailCalculator(AttributeCalculator):
    """ Search through the user's bio and all links. """
    def calculate(self, signal: Signal) -> Dict:
        regexp = re.compile(
            r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
        match = regexp.search(signal.bio)
        if match:
            return {
                'email': match.group(0)
            }
        for url in [signal.url] + get_urls_from_string(signal.bio):
            try:
                text = requests.get(url).text
                match = regexp.search(text)
                if match:
                    return {
                        'email': match.group(0)
                    }
            except Exception:
                pass
        return {
            'email': ''
        }
