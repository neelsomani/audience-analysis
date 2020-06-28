from collections import defaultdict
import json
import logging
import requests
from typing import Dict

from attribute_calculators.attribute_calculator import AttributeCalculator
from models import Signal
from util import get_urls_from_string

from bs4 import BeautifulSoup

with open('datasets/female_first_names.json', 'rb') as f:
    female_first_names = set(json.load(f))


with open('datasets/male_first_names.json', 'rb') as f:
    male_first_names = set(json.load(f))


with open('datasets/last_names.json', 'rb') as f:
    last_names = set(json.load(f))


class NameCalculator(AttributeCalculator):
    """
    Assign scores to common names appearing in the user's display name,
    screen name, and websites. Normalize the result and return the most likely
    name.
    """
    def calculate(self, signal: Signal) -> Dict:
        full_name = signal.display_name.upper().split(' ')
        screen_name = signal.screen_name.upper()
        possible_first = defaultdict(int)
        possible_last = defaultdict(int)
        for f in male_first_names | female_first_names:
            if any(p.upper() == f for p in full_name):
                possible_first[f] += 2
            if f.upper() in screen_name:
                possible_first[f] += 2

        for l in last_names:
            if any(p.upper() == l for p in full_name):
                possible_last[l] += 2
            if l.upper() in screen_name:
                possible_last[l] += 2

        for url in [signal.url] + get_urls_from_string(signal.bio):
            page_signals = _name_signals_from_url(url)
            for f in page_signals['possible_first']:
                possible_first[f] += page_signals['possible_first'][f]
            for l in page_signals['possible_last']:
                possible_last[l] += page_signals['possible_last'][l]

        # Signals from the user's display name are very likely to be correct
        possible_first[full_name[0]] += 4
        if len(full_name) > 1:
            possible_last[' '.join(full_name[1:])] += 4

        best_first, best_last = _get_best_name(possible_first, possible_last)

        return {
            'best_first': best_first,
            'best_last': best_last
        }


def _name_signals_from_url(url: str) -> Dict:
    possible_first = defaultdict(int)
    possible_last = defaultdict(int)
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    except Exception as e:
        if url is not None:
            logging.error(e)
        return {
            'possible_first': {},
            'possible_last': {},
        }
    phrases = soup.findAll(text=True)
    words = []
    for p in phrases:
        words.extend(p.split(' '))
    for f in male_first_names | female_first_names:
        for i, w in enumerate(words):
            # Double count a first + last name if they're next to each other
            if w.upper() == f:
                possible_first[f] += .1
                if len(words) > i + 1:
                    last = words[i + 1].upper()
                    if last in last_names:
                        possible_first[f] += 1
                        possible_last[last] += 1

    for l in last_names:
        for w in words:
            if w.upper() == l:
                possible_last[l] += .1

    return {
        'possible_first': possible_first,
        'possible_last': possible_last
    }


def _get_best_name(possible_first: Dict, possible_last: Dict) -> (str, str):
    if len(possible_first) == 0:
        if len(possible_last) == 0:
            return '', ''
        return '', max(possible_last, key=lambda k: possible_last[k])
    elif len(possible_last) == 0:
        return max(possible_first, key=lambda k: possible_first[k]), ''

    best_first = max(possible_first, key=lambda k: possible_first[k])
    prob_first = possible_first[best_first]
    best_last = max(possible_last, key=lambda k: possible_last[k])
    prob_last = possible_last[best_last]
    if best_first == best_last:
        if prob_first > prob_last:
            best_last = max(
                (k for k in possible_last if k != best_last),
                key=lambda k: possible_last[k])
        else:
            best_first = max(
                (k for k in possible_first if k != best_first),
                key=lambda k: possible_first[k])
    return best_first, best_last
