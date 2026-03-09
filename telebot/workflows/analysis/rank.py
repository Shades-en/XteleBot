from decimal import Decimal

from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.constants import RATING_SCORE_MAX
from telebot.common.messages import TEXT_ANALYSIS_EMPTY_RESULT
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.x_users import XUserRepository
from telebot.workflows.analysis.common import AnalysisContext, report_progress
from telebot.workflows.analysis.scoring import AuthorSignals, PostRankScorer


class RankPostsExecutor:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self.scorer = PostRankScorer()

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        async with self.session_factory() as session:
            post_repo = PostRepository(session)
            if await post_repo.has_ranked_analysis_for_today(context.telegram_user_id):
                return StepOutput(content="ranking_skipped")
        await report_progress(context, "ranking")
        async with self.session_factory() as session:
            post_repo = PostRepository(session)
            posts = await post_repo.candidate_posts_for_today(context.telegram_user_id, limit=200)
            if not posts:
                raise RuntimeError(TEXT_ANALYSIS_EMPTY_RESULT)
            authors = await self._authors_by_username(session, posts)
            scored_posts = [
                (
                    post,
                    self.scorer.score(
                        post,
                        self._author_signals(post.author_username, authors),
                    ),
                )
                for post in posts
            ]
            ranked = sorted(scored_posts, key=lambda item: item[1], reverse=True)
            top_score = ranked[0][1] if ranked else 0.0
            for index, (post, score) in enumerate(ranked, start=1):
                await post_repo.set_rank(
                    post.post_id,
                    index,
                    self._normalized_rating_score(score, top_score),
                )
            await session.commit()
        return StepOutput(content="ranking")

    async def _authors_by_username(self, session: AsyncSession, posts: list[object]) -> dict[str, object]:
        usernames = list({post.author_username for post in posts if post.author_username})
        return await XUserRepository(session).get_by_usernames(usernames)

    @staticmethod
    def _author_signals(author_username: str | None, authors: dict[str, object]) -> AuthorSignals:
        if author_username is None or author_username not in authors:
            return AuthorSignals()
        author = authors[author_username]
        return AuthorSignals(
            followers=getattr(author, "followers", 0) or 0,
            is_verified=bool(getattr(author, "is_verified", False)),
        )

    @staticmethod
    def _normalized_rating_score(score: float, top_score: float) -> Decimal:
        if top_score <= 0:
            return Decimal("0.00")
        normalized = min((score / top_score) * RATING_SCORE_MAX, RATING_SCORE_MAX)
        return Decimal(str(round(normalized, 2)))
