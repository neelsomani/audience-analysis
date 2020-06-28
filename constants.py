""" Constants that must be set to run the tool. """
from typing import Dict, List

TWITTER_API_CONSUMER_KEY = None
TWITTER_API_CONSUMER_SECRET = None
GOOGLE_CUSTOM_SEARCH_CX = None
GOOGLE_CUSTOM_SEARCH_KEY = None

KEYS_ERROR = 'You must add some dictionaries with Twitter OAuth keys to the ' \
             'get_all_api_keys function '


def get_all_api_keys() -> List[Dict[str, str]]:
    """
    Return a list of dictionaries containing Twitter API OAuth keys.
    Each dictionary should have two keys:
    `oauth_token` and `oauth_token_secret`
    """
    raise NotImplementedError(KEYS_ERROR)
