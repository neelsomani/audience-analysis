# Twitter Audience Analysis

## 1-Sentence Summary

**This tool streams a user's Twitter followers (by parallelizing the Twitter API requests across API keys) and infers various attributes about each individual follower, including their email address and LinkedIn profile.**

Update (8/25/2020): This project was awarded a finalist bounty for @balajis's [Twitter followers export challenge](https://github.com/balajis/twitter-export).

You can skip straight to the [approach](#approach) if you'd like, which describes why this solution wins over others. Directly below I provide the motivation to demonstrate that this solution solves multiple related problems aside from the [one described by @balajis](https://github.com/balajis/twitter-export/blob/master/README.md#problem-exporting-followers-from-twitter).

## Motivation

Social media accounts (like Twitter, Facebook, and LinkedIn profiles) are typically unverified and sometimes pseudonymous. This poses a number of challenges.

For example, a company analyzing its social media audience (e.g., its Twitter following) cannot directly access its followers' demographic information, interests, or identities, which is valuable information for product development.

Another challenge is in detecting "fake news" -- deliberate misinformation typically propagated to promote a political agenda. Since there is no way to determine whether the original poster of an article represents a legitimate person, it's easy to create bots that contribute propaganda to conversations on social media.

Yet another challenge is for social media influencers (Balaji's use case). A social media influencer might not want to risk a platform like Twitter kicking them off, since they would lose their entire audience. Therefore they would want a list of their audience's other social media profiles.

To solve these problems, I propose deriving a set of useful attributes for each user that relate to their identity.

## Approach

The existing responses to Balaji's problem will not scale for users with large followings. Problems with other responses:
* Sending an automated direct message to all followers, which [violates Twitter's TOS](https://github.com/balajis/twitter-export/issues/4) and will result in a ban
* Attempting to store all user data in memory rather than streaming, which could run out of memory for users with millions of followers
* Requiring a process to run for months or years, which is unreliable and error prone

**My solution:** Given a profile on Twitter, the model should use the Twitter API directly and efficiently infer the following attributes for each follower:
* Name
* Location
* Occupation
* Email
* LinkedIn profile

To scale the API requests, we can distribute the requests across multiple API keys:

<img src="https://i.imgur.com/8JPRslP.jpg" width="500" alt="Architecture Diagram"/>

Future inferred attributes might include:
* Age
* Gender (solved problem: https://www.proporti.onl/)
* Interests
* Political views
* Religious beliefs
* Friends + family
* ALL of a follower's social media profiles

Below is the [methodology](#methodology) for deriving each attribute from a Twitter profile. I also include other signals that could be used for future improvements. The general nature of this solution makes it easy to iterate on. I found that I could infer about 20% of my followers' emails, and about 50% of the LinkedIn profiles were accurate.

If you are interested in running the project, you'll need to complete the steps included in the Setup section below.

## Setup

Requirements:
* python3
* Multiple Twitter API OAuth keys to parallelize the Twitter API requests (optional, recommended)
  * If this were to be run as a service, then having multiple users on the platform would allow you to parallelize the requests across all users’ keys
  * I used a set of keys from a related Twitter service that I had previously built
* macOS or Linux

Installation:
* Install the requirements with `pip3 install -r requirements.txt`
* Create a Twitter API app to get a API consumer key and secret: https://developer.twitter.com/en/apps
* Create a Google Custom Search API for www.linkedin.com to get the `cx` variable and API key: https://cse.google.com/cse/all
* Set the appropriate configuration variables in the `constants.py` file.

Run with `python3 -i main.py` and call `workflow(screen_name='neeljsomani', output_csv='neeljsomani_output.csv')` to get a pandas DataFrame of inferred attributes. The results will be saved to disk.

## Methodology

In this section, we outline how various attributes are inferred. Discussion of the efficiency of this solution is left to the [Appendix](#appendix).

### Name

To infer a user's name, each time we see a word that could possibly be a user's name, we assign that word some number of points. At the end, we normalize the points to give a probability that each word is the user's name.

Signals used:
* Check if a user's listed name is in the 1000 [most common first + last names](https://namecensus.com/most_common_surnames.htm)
* For all websites linked in bio, check all words against a list of the 1000 most common first + last names.
* Assume the first word in the user's listed name is their first name, and the remainder is their last name.

Signals for future improvements:
* Names that other users use to refer to this user
* Reverse image search profile picture and see what names come up
* WHOIS for websites linked
* Infer this user's friends, then check their friends' profiles on another network for names

### Location

Use the user's listed location if present.

Signals for future improvements:
* Location data in tweets
* Listed location mapped to an actual city via some API
* Estimated location of the people who the user is following
* Encoded locations in photos that are posted
* Languages and dialects

I am particularly interested in using the estimated locations of the people who the user is following. We might recursively define each user's location as something like:

```$Pr[L(user_{k}) = city] = z * I_{listed location = city} + (1 - z) / |following| * sum_{i ∈ following} Pr[L(user_{i}) = city]$```

where `L` is a function that maps a user to a city, `z` is some value between 0 and 1, `I` is an indicator variable, and `following` is the set of users that this user is following.

### Occupation

To infer the user's occupation, we check the user's bio for words in the list of [most common occupations](https://github.com/dariusk/corpora/blob/master/data/humans/occupations.json).

We pick the maximum length match. If there is no occupation in the user's bio, we check all linked websites for words in the list of most common occupations.

### Email

We check the user's bio for email addresses (Regex format: `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`)

If no email is found in the user's bio, we check all linked sites.

A possible improvement might use the user's name and company to guess their email using their company's email format.

### LinkedIn Profile

If we had access to the LinkedIn API (in the approval process), we would use the LinkedIn [People Search API](https://developer.linkedin.com/docs/v1/people/people-search-api) to search for a user with our predicted name, occupation, and location.

In the meantime, we click on all non-Twitter links in the bio and scrape for LinkedIn profile links. If there's nothing found, we use the Google Custom Search API to query `www.linkedin.com` up to 10,000 profiles a day, but it costs $5 for every 1000 requests. I select the first LinkedIn profile for a search query of the form "{guessed_name} {location} {occupation}" where location and/or occupation might not be present.

## Appendix

One limiting factor is how quickly we can pull and hydrate a user's Twitter followers. Each API key allows for 15 requests to the followers list API every 15 minutes, and each request gives about 5000 users. That's about 5000 users per minute.

The users hydration endpoint allows for 900 requests every 15 minutes (60 requests a minute) for 100 users per request. That's 6000 users per minute.

So the throughput of the Twitter API is the lesser of the two (5000 users per minute). So with `K` API keys, for a user with `F` followers, it will take about `F / (5000 * K)` minutes to pull and hydrate the users.

There is additional overhead for scraping links and calculating attributes. I would estimate there are about three HTTP requests per user (at 300ms each) and it probably takes another second to calculate attributes. So the additional overhead is about 2 seconds per user. Since each user's attributes are not dependent on any other user's, we could parallelize this computation across `T` threads, to cut the time to about `2 / T` seconds per user. For a user with 100,000 followers, you would need about three threads to cut the full computation down to a single day.

Without LinkedIn API access, the Google Custom Search API is the final bottleneck. It only allows for 10,000 searches per day, but we only search for a user's LinkedIn profile if we were not able to scrape it. In the worst case, for a user with 100,000 followers, this would take 10 days.

You might consider removing the Google Custom Search API dependency. Instead, if you are not able to extract a user's email or LinkedIn profile, then you can send them a direct message using one of the existing methods.
