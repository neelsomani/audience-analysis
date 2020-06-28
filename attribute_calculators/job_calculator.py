import json
import logging
from models import Signal
import requests
from typing import Dict, List

from attribute_calculators.attribute_calculator import AttributeCalculator
from util import get_urls_from_string

from bs4 import BeautifulSoup


with open('datasets/occupations.json', 'rb') as f:
    occupations = set([o.upper() for o in json.load(f)['occupations']])


class JobCalculator(AttributeCalculator):
    """ Search for job titles in the bio and links. """
    def calculate(self, signal: Signal) -> Dict:
        possible_jobs = []
        bio = signal.bio.upper()
        for o in occupations:
            if o in bio:
                possible_jobs.append(o)
        for url in [signal.url] + get_urls_from_string(signal.bio):
            possible_jobs.extend(_jobs_from_url(url))
        if len(possible_jobs) == 0:
            return {
                'job': ''
            }
        return {
            'job': max(possible_jobs, key=lambda k: len(k))
        }


def _jobs_from_url(url) -> List[str]:
    jobs = []
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    except Exception as e:
        if url is not None:
            logging.error(e)
        return []
    phrases = soup.findAll(text=True)
    full_text = ' '.join(phrases).upper()
    for o in occupations:
        if o in full_text:
            jobs.append(o)
    return jobs

