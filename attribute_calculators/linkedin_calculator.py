from models import Signal
from typing import Dict
import re
import requests
import logging

from constants import GOOGLE_CUSTOM_SEARCH_CX, GOOGLE_CUSTOM_SEARCH_KEY
from util import get_urls_from_string

CUSTOM_SEARCH = 'https://customsearch.googleapis.com/customsearch/v1'


def calculate(signal: Signal, attributes: Dict) -> Dict:
    """
    Scrape the user's bio and links for a LinkedIn profile, and
    otherwise make a search on www.linkedin.com for this person's keywords.
    """
    regexp = re.compile(r'(linkedin.[a-z]+/in/[a-zA-Z0-9-.]+)')
    match = regexp.search(signal.bio)
    if match:
        return {
            'linkedin': match.group(0)
        }
    if signal.url:
        match = regexp.search(signal.url)
        if match:
            return {
                'linkedin': match.group(0)
            }
    for url in [signal.url] + get_urls_from_string(signal.bio):
        try:
            text = requests.get(url).text
        except Exception:
            continue
        match = regexp.search(text)
        if match:
            return {
                'linkedin': match.group(0)
            }
    # If we can't scrape a LinkedIn profile, we'll try searching Google
    query = '{0} {1} {2} {3}'.format(
        attributes['best_first'],
        attributes['best_last'],
        attributes['location'],
        attributes['job']
    )
    query = re.sub(r'[^A-Za-z0-9 ]+', '', query).strip()
    logging.info('Executing LinkedIn query: {}'.format(query))
    result = requests.get(
        '{0}?key={1}'.format(CUSTOM_SEARCH, GOOGLE_CUSTOM_SEARCH_KEY),
        {
            'q': query,
            'cx': GOOGLE_CUSTOM_SEARCH_CX
        }
    )
    try:
        return {
            'linkedin': result.json()['items'][0]['link']
        }
    except Exception:
        pass
    return {
        'linkedin': ''
    }
