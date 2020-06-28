""" General purpose functions """
from typing import Dict, List


def to_probability(d: Dict[str, float]) -> Dict[str, float]:
    """
    Scale a dictionary that maps keys to proportions so the sum of the
    proportions equals 1.

    Parameters
    ----------
    d : Dict[str, int]
        Dictionary mapping keys to values (proportions)
    """
    s = 0
    for k in d:
        s += d[k]
    for k in d:
        d[k] = d[k] / s
    return d


def get_urls_from_string(s: str) -> List[str]:
    """
    Extract all URLs from a string.

    Parameters
    ----------
    s : str
        String to extract URLs from
    """
    tokens = s.split(' ')
    urls = []
    for t in tokens:
        if t[:4] == 'http':
            urls.append(t)
    return urls
