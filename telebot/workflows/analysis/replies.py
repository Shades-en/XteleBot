import asyncio
from datetime import datetime

from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.constants import ANALYSIS_REPLY_TARGET_LIMIT, ANALYSIS_SEARCH_CONCURRENCY, REPLY_CONTEXT_LIMIT
from telebot.db.repositories.posts import PostRepository
from telebot.db.schemas import ReplyContextItem
from telebot.db.repositories.users import UserRepository
from telebot.db.repositories.x_users import XUserRepository
from telebot.twitter.client import TwitterApiClient
from telebot.workflows.analysis.common import AnalysisContext, extract_media_urls, report_progress
from telebot.workflows.analysis.scoring import AuthorSignals, ReplyRankScorer
from telebot.workflows.analysis.types import RankedReply


class FetchReplyContextExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        twitter_client: TwitterApiClient,
    ) -> None:
        self.session_factory = session_factory
        self.twitter_client = twitter_client
        self.reply_scorer = ReplyRankScorer()

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        async with self.session_factory() as session:
            repo = PostRepository(session)
            if await repo.has_reply_context_for_today(context.telegram_user_id):
                return StepOutput(content="replies_skipped")
        await report_progress(context, "replies")
        async with self.session_factory() as session:
            repo = PostRepository(session)
            posts = await repo.top_safe_ranked_posts(
                context.telegram_user_id,
                limit=ANALYSIS_REPLY_TARGET_LIMIT,
            )
            if not posts:
                return StepOutput(content="replies")
            semaphore = asyncio.Semaphore(ANALYSIS_SEARCH_CONCURRENCY)
            reply_results = await asyncio.gather(
                *(self._fetch_replies(post.post_id, semaphore) for post in posts)
            )
            connected_usernames, connected_x_ids = await self._connected_x_identities(
                session,
                reply_results,
            )
            x_user_rows = []
            reply_context_rows = []
            for post, replies in zip(posts, reply_results, strict=True):
                reply_context: list[dict] = []
                for ranked_reply in self._ranked_replies(replies):
                    reply = ranked_reply.reply
                    author = reply.author
                    if author and author.userName and author.id:
                        x_user_rows.append(
                            {
                                "username": author.userName,
                                "x_id": author.id,
                                "name": author.name,
                                "followers": author.followers,
                                "is_verified": bool(author.isBlueVerified),
                                "location": author.location,
                                "is_bot_user": (
                                    author.userName in connected_usernames
                                    or author.id in connected_x_ids
                                ),
                                "updated_at": datetime.utcnow(),
                            }
                        )
                    reply_context.append(
                        self._reply_context_row(
                            reply=reply,
                            rank_position=ranked_reply.rank_position,
                            rating_score=ranked_reply.rating_score,
                        )
                    )
                reply_context_rows.append(
                    {
                        "post_id": post.post_id,
                        "reply_context": reply_context,
                    }
                )
            await repo.bulk_update_reply_context(reply_context_rows)
            await XUserRepository(session).bulk_upsert_users(x_user_rows)
            await session.commit()
        return StepOutput(content="replies")

    async def _fetch_replies(self, post_id: str, semaphore: asyncio.Semaphore) -> list[object]:
        async with semaphore:
            return await self.twitter_client.get_replies(post_id)

    async def _connected_x_identities(
        self,
        session: AsyncSession,
        reply_results: list[list[object]],
    ) -> tuple[set[str], set[str]]:
        usernames = []
        x_ids = []
        for replies in reply_results:
            for reply in replies:
                if reply.author and reply.author.userName:
                    usernames.append(reply.author.userName)
                if reply.author and reply.author.id:
                    x_ids.append(reply.author.id)
        return await UserRepository(session).get_connected_x_identities(usernames, x_ids)

    def _ranked_replies(self, replies: list[object]) -> list[RankedReply]:
        authors = {reply.author.userName: reply.author for reply in replies if reply.author and reply.author.userName}
        ranked = sorted(
            replies,
            key=lambda reply: self.reply_scorer.score(
                reply,
                self._author_signals(reply.author.userName if reply.author else None, authors),
            ),
            reverse=True,
        )
        ranked_replies = []
        for index, reply in enumerate(ranked[:REPLY_CONTEXT_LIMIT], start=1):
            score = self.reply_scorer.score(
                reply,
                self._author_signals(reply.author.userName if reply.author else None, authors),
            )
            ranked_replies.append(
                RankedReply(
                    reply=reply,
                    rank_position=index,
                    rating_score=round(score * 10, 2),
                )
            )
        return ranked_replies

    @staticmethod
    def _author_signals(author_username: str | None, authors: dict[str, object]) -> AuthorSignals:
        if author_username is None or author_username not in authors:
            return AuthorSignals()
        author = authors[author_username]
        return AuthorSignals(
            followers=getattr(author, "followers", 0) or 0,
            is_verified=bool(getattr(author, "isBlueVerified", False)),
        )

    @staticmethod
    def _reply_context_row(
        reply,
        rank_position: int,
        rating_score: float,
    ) -> dict:
        return ReplyContextItem(
            post_id=reply.id,
            text=reply.text,
            media_urls=extract_media_urls(reply.extendedEntities),
            likes_count=reply.likeCount,
            comment_count=reply.replyCount,
            reposts_count=reply.retweetCount,
            view_count=reply.viewCount,
            author_username=reply.author.userName if reply.author else None,
            rank_position=rank_position,
            rating_score=rating_score,
        ).model_dump()
