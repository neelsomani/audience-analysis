import logging
from typing import Dict, List, Optional

from attribute_calculators.email_calculator import EmailCalculator
from attribute_calculators.job_calculator import JobCalculator
from attribute_calculators import linkedin_calculator
from attribute_calculators.location_calculator import LocationCalculator
from attribute_calculators.name_calculator import NameCalculator
from constants import (
    get_all_api_keys,
    TWITTER_API_CONSUMER_KEY,
    TWITTER_API_CONSUMER_SECRET
)
from models import Signal

import parallel_twitter
import pandas as pd
import twitter


def api_key_list(
        oauth_dicts: List[Dict[str, str]]
) -> parallel_twitter.ParallelTwitterClient:
    """
    Convert a list of dictionary containing OAuth tokens and secrets to a
    ParallelTwitterClient, which will distribute the API requests across the
    API keys.

    Parameters
    ----------
    oauth_dicts : List[Dict[str, str]]
        Each dictionary should have two keys: `oauth_token` and
        `oauth_token_secret`
    """
    return parallel_twitter.ParallelTwitterClient(
        parallel_twitter.oauth_dicts_to_apis(
            oauth_dicts=oauth_dicts,
            api_consumer_key=TWITTER_API_CONSUMER_KEY,
            api_consumer_secret=TWITTER_API_CONSUMER_SECRET
        ))


def workflow(
        user_id: Optional[int] = None,
        screen_name: Optional[str] = None,
        total_followers: int = 100000,
        batch_size: int = 5000,
        output_csv: Optional[str] = None
) -> pd.DataFrame:
    """
    Pull a user's Twitter following and map each follower to a row
    of their identity attributes. Return as a pandas DataFrame.

    Parameters
    ----------
    user_id : Optional[int]
        The Twitter API ID for the user whose followers we should pull
    screen_name : Optional[str]
        Twitter handle for the user whose followers we should pull
    total_followers : int
        The total number of followers that this user has.
        Defaults to 100,000.
    batch_size : int
        How many users should be held in memory at any given time.
        Maximum value of 5000. Defaults to 5000.
    output_csv : Optional[str]
        A file to output the DataFrame of attributes to. If None, do not
        save the DataFrame to disk. Defaults to None.
    """
    client = api_key_list(get_all_api_keys())
    df = pd.DataFrame(client.get_followers(
        user_id=user_id,
        screen_name=screen_name,
        min_count=total_followers,
        batch_size=batch_size,
        streaming_fn=_get_user_attributes
    ))
    df.to_csv(output_csv)
    return df


def _user_to_signal(user: twitter.User) -> Signal:
    """
    Convert a User to an object containing signals that can be used to
    calculate attributes.

    Parameters
    ----------
    user : twitter.User
        The user to convert to signals
    """
    return Signal(
        screen_name=user.screen_name,
        display_name=user.name,
        bio=user.description,
        url=user.url,
        location=user.location
    )


def _get_user_attributes(user: twitter.User) -> Dict:
    """
    Map a `twitter.User` object to their predicted name, location, job, and
    other attributes. Return a dictionary of the predicted attributes.

    Parameters
    ----------
    user : twitter.User
        The user to map to attributes
    """
    signal = _user_to_signal(user)
    current = NameCalculator().calculate(signal)
    email = EmailCalculator().calculate(signal)
    for k in email:
        current[k] = email[k]
    location = LocationCalculator().calculate(signal)
    for k in location:
        current[k] = location[k]
    job = JobCalculator().calculate(signal)
    for k in job:
        current[k] = job[k]
    linkedin = linkedin_calculator.calculate(signal, current)
    for k in linkedin:
        current[k] = linkedin[k]
    current['screen_name'] = signal.screen_name
    current['display_name'] = signal.display_name
    # TODO(@neel): Remove.
    print(current)
    return current


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
