from typing import Any

import httpx

from telebot.common.constants import (
    ANALYSIS_QUERY_LIMIT,
    HTTP_TIMEOUT_SECONDS,
    TWITTER_ADVANCED_SEARCH_PATH,
    TWITTER_API_BASE_URL,
    TWITTER_REPLIES_PATH,
    TWITTER_USER_LAST_TWEETS_PATH,
    TWITTER_USER_LOOKUP_PATH,
)
from telebot.twitter.schemas import AdvancedSearchTweet, TwitterUserResult


class TwitterApiClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=TWITTER_API_BASE_URL,
            headers={"X-API-Key": api_key},
            timeout=HTTP_TIMEOUT_SECONDS,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_user_by_username(self, username: str) -> TwitterUserResult | None:
        response = await self.client.get(TWITTER_USER_LOOKUP_PATH, params={"userName": username})
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or payload.get("user") or payload
        if not data or not data.get("id"):
            return None
        return TwitterUserResult(**data, raw=data)

    async def advanced_search(self, query: str) -> list[AdvancedSearchTweet]:
        response = await self.client.get(
            TWITTER_ADVANCED_SEARCH_PATH,
            params={"query": query, "queryType": "Latest", "cursor": "", "count": ANALYSIS_QUERY_LIMIT},
        )
        response.raise_for_status()
        payload = response.json()
        return self._parse_tweets(payload)

    async def get_user_last_tweets(self, user_id: str) -> list[AdvancedSearchTweet]:
        response = await self.client.get(
            TWITTER_USER_LAST_TWEETS_PATH,
            params={"userId": user_id, "count": ANALYSIS_QUERY_LIMIT},
        )
        response.raise_for_status()
        payload = response.json()
        return self._parse_tweets(payload, ("data.tweets", "tweets", "data"))

    async def get_replies(self, post_id: str) -> list[AdvancedSearchTweet]:
        response = await self.client.get(
            TWITTER_REPLIES_PATH,
            params={"tweetId": post_id, "queryType": "Relevance"},
        )
        response.raise_for_status()
        payload = response.json()
        return self._parse_tweets(payload, ("replies", "tweets", "data"))

    @staticmethod
    def _parse_tweets(
        payload: dict[str, Any],
        keys: tuple[str, ...] = ("tweets", "data"),
    ) -> list[AdvancedSearchTweet]:
        tweets: list[Any] | Any = []
        for key in keys:
            tweets = TwitterApiClient._resolve_payload_value(payload, key) or []
            if tweets:
                break
        if not isinstance(tweets, list):
            return []
        parsed: list[AdvancedSearchTweet] = []
        for tweet in tweets:
            if not isinstance(tweet, dict):
                continue
            if not tweet.get("id"):
                continue
            parsed.append(AdvancedSearchTweet(**tweet, raw=tweet))
        return parsed

    @staticmethod
    def _resolve_payload_value(payload: dict[str, Any], key: str) -> Any:
        value: Any = payload
        for part in key.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value
