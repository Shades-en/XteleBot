from telebot.costs.pricing import (
    TWITTER_CREDITS_PER_USD,
    TWITTER_MIN_CALL_CREDITS,
    TWITTER_PROFILE_RESULT_CREDITS,
    TWITTER_TWEET_RESULT_CREDITS,
)

TWITTER_PROFILE_ENDPOINTS = {"user_lookup"}
TWITTER_TWEET_ENDPOINTS = {"advanced_search", "user_last_tweets", "replies"}


def estimate_twitter_credits(endpoint: str, returned_count: int) -> int:
    if endpoint in TWITTER_PROFILE_ENDPOINTS:
        return max(TWITTER_MIN_CALL_CREDITS, TWITTER_PROFILE_RESULT_CREDITS * max(returned_count, 0))
    if endpoint in TWITTER_TWEET_ENDPOINTS:
        return max(TWITTER_MIN_CALL_CREDITS, TWITTER_TWEET_RESULT_CREDITS * max(returned_count, 0))
    return 0


def credits_to_usd(credits: int) -> float:
    return credits / TWITTER_CREDITS_PER_USD
