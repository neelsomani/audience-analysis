""" Signal object to represent what we extracted directly from the user. """
from collections import namedtuple

Signal = namedtuple(
    'Signal',
    ['screen_name', 'display_name', 'bio', 'url', 'location']
)
