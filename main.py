from auth_utils import PKCEManager, twitter_auth, twitter_token, refresh_access_token
from api_utils import post_tweet
import time
import random

#Initializing Authentications
pkce = PKCEManager()
pkce.generate_pkce()
twitter_auth(pkce)
ACCESS_TOKEN, REFRESH_TOKEN = twitter_token(pkce)

max_tweets_per_day = 1
tweets_posted_today = 0

first_tweet_time = None

while tweets_posted_today < max_tweets_per_day:
    if tweets_posted_today == 0:
        first_tweet_time = time.time()

    expiration_time = 6000
    time_since_last_refresh = time.time() - first_tweet_time  # Track when the token was refreshed

    if time_since_last_refresh >= expiration_time:
        print("Access token has expired or is about to expire. Refreshing...")
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(REFRESH_TOKEN)
        if not ACCESS_TOKEN:
            print("Failed to refresh access token. Exiting...")
            break
        first_tweet_time = time.time()  # Reset the time to the new token's refresh time

    post_tweet(ACCESS_TOKEN)
    tweets_posted_today += 1

    if tweets_posted_today < max_tweets_per_day:
        time_since_first_tweet = time.time() - first_tweet_time

        if time_since_first_tweet >= 86400:
            print("⏰ 24 hours have passed since the first tweet. Resetting the count...")
            tweets_posted_today = 0
            first_tweet_time = None
            continue

        random_sleep_time = random.randint(600, 4920)  # Random sleep time between 10 minutes (600s) and 82 minutes (4920s)
        print(f"⏳ Waiting for {random_sleep_time} seconds before the next tweet...")
        time.sleep(random_sleep_time)

    if tweets_posted_today >= max_tweets_per_day:
        print("⏰ 17 tweets posted today. Waiting for the next day...")
        time.sleep(24 * 60 * 60)  # Sleep for 24 hours before starting again
        tweets_posted_today = 0  # Reset count for the next day
        first_tweet_time = None  # Reset first tweet time