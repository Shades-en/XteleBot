import asyncio
from datetime import date, datetime

import httpx
from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.constants import (
    ANALYSIS_SEARCH_CONCURRENCY,
    OWN_POST_SOURCE_MARKER,
    X_STATUS_URL_TEMPLATE,
)
from telebot.common.messages import TEXT_ANALYSIS_EMPTY_RESULT, TEXT_ANALYSIS_RATE_LIMITED
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.x_users import XUserRepository
from telebot.twitter.client import TwitterApiClient
from telebot.twitter.queries import build_seed_queries
from telebot.workflows.analysis.common import (
    AnalysisContext,
    CollectedTweet,
    extract_media_urls,
    parse_twitter_created_at,
    report_progress,
)


class CollectPostsExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        twitter_client: TwitterApiClient,
    ) -> None:
        self.session_factory = session_factory
        self.twitter_client = twitter_client

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        async with self.session_factory() as session:
            if await PostRepository(session).has_analysis_for_today(context.telegram_user_id):
                return StepOutput(content="collecting_skipped")
        await report_progress(context, "collecting")
        collected = await self._collect_tweets(context)
        if not collected:
            raise RuntimeError(TEXT_ANALYSIS_EMPTY_RESULT)
        x_user_rows, post_rows = self._build_rows(collected, context)
        async with self.session_factory() as session:
            await XUserRepository(session).bulk_upsert_users(x_user_rows)
            await PostRepository(session).bulk_upsert_posts(post_rows)
            await session.commit()
        return StepOutput(content="collecting")

    async def _collect_tweets(self, context: AnalysisContext) -> list[CollectedTweet]:
        queries = build_seed_queries(context.x_username)
        semaphore = asyncio.Semaphore(ANALYSIS_SEARCH_CONCURRENCY)
        results = await asyncio.gather(
            *(self._fetch_query(query, semaphore) for query in queries),
            self._fetch_own_posts(context, semaphore),
        )
        collected: list[CollectedTweet] = []
        had_rate_limit = False
        for batch, was_rate_limited in results:
            collected.extend(batch)
            had_rate_limit = had_rate_limit or was_rate_limited
        if collected:
            return collected
        if had_rate_limit:
            raise RuntimeError(TEXT_ANALYSIS_RATE_LIMITED)
        return []

    async def _fetch_query(
        self,
        query: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[list[CollectedTweet], bool]:
        async with semaphore:
            try:
                tweets = await self.twitter_client.advanced_search(query)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                    return [], True
                raise
        return [CollectedTweet(tweet=tweet, source_query=query) for tweet in tweets], False

    async def _fetch_own_posts(
        self,
        context: AnalysisContext,
        semaphore: asyncio.Semaphore,
    ) -> tuple[list[CollectedTweet], bool]:
        async with semaphore:
            try:
                tweets = await self.twitter_client.get_user_last_tweets(context.x_id)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                    return [], True
                raise
        return [
            CollectedTweet(tweet=tweet, source_query=OWN_POST_SOURCE_MARKER)
            for tweet in tweets
        ], False

    @staticmethod
    def _build_rows(
        collected: list[CollectedTweet],
        context: AnalysisContext,
    ) -> tuple[list[dict], list[dict]]:
        analysis_date = date.today()
        analysis_timestamp = datetime.utcnow()
        x_user_rows: list[dict] = []
        post_rows: list[dict] = []
        for item in collected:
            tweet = item.tweet
            author_username = tweet.author.userName if tweet.author else None
            if tweet.author and tweet.author.userName and tweet.author.id:
                x_user_rows.append(
                    {
                        "username": tweet.author.userName,
                        "x_id": tweet.author.id,
                        "name": tweet.author.name,
                        "followers": tweet.author.followers,
                        "is_verified": bool(tweet.author.isBlueVerified),
                        "location": tweet.author.location,
                        "is_bot_user": tweet.author.userName == context.x_username,
                        "updated_at": analysis_timestamp,
                    }
                )
            media_urls = extract_media_urls(tweet.extendedEntities)
            post_rows.append(
                {
                    "post_id": tweet.id,
                    "post_url": CollectPostsExecutor._build_post_url(author_username, tweet.id),
                    "posted_at": parse_twitter_created_at(tweet.createdAt),
                    "own_posts": item.source_query == OWN_POST_SOURCE_MARKER,
                    "text": tweet.text,
                    "media_urls": media_urls,
                    "likes_count": tweet.likeCount,
                    "comment_count": tweet.replyCount,
                    "reposts_count": tweet.retweetCount,
                    "view_count": tweet.viewCount,
                    "source_query": [item.source_query],
                    "author_username": author_username,
                    "analysed_for_user_id": context.telegram_user_id,
                    "date_of_analysis": analysis_date,
                    "raw_payload": tweet.raw,
                }
            )
        return x_user_rows, post_rows

    @staticmethod
    def _build_post_url(author_username: str | None, post_id: str) -> str | None:
        if not author_username:
            return None
        return X_STATUS_URL_TEMPLATE.format(author_username=author_username, post_id=post_id)
