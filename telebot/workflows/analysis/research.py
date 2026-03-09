import asyncio

from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.common.constants import (
    ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT,
    ANALYSIS_RESEARCH_TARGET_LIMIT,
    RESEARCH_TWEET_WORKFLOW_CONCURRENCY,
)
from telebot.db.repositories.posts import PostRepository
from telebot.db.schemas import ReplyContextItem
from telebot.workflows.analysis.common import AnalysisContext, report_progress
from telebot.workflows.analysis.research_tweet import build_research_tweet_workflow
from telebot.workflows.analysis.types import ResearchTweetContext


class ResearchTweetsExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agno_factory: AgnoFactory,
    ) -> None:
        self.session_factory = session_factory
        self.workflow = build_research_tweet_workflow(agno_factory.settings, agno_factory)

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        await report_progress(context, "plan_research")
        async with self.session_factory() as session:
            repo = PostRepository(session)
            posts = await repo.top_safe_ranked_posts(
                context.telegram_user_id,
                limit=ANALYSIS_RESEARCH_TARGET_LIMIT,
            )
            tweet_contexts = [self._tweet_context(post) for post in posts]
            results = await self._run_tweet_workflows_in_parallel(tweet_contexts, context.telegram_user_id)
            await repo.bulk_update_research_fields(
                [
                    {
                        "post_id": tweet_context.post_id,
                        "related_sources": [item.model_dump(mode="json") for item in result.related_sources],
                        "agent_sentiment": [item.value for item in result.agent_sentiment],
                        "agent_comments": result.agent_comments,
                        "purpose": result.purpose.value,
                    }
                    for tweet_context, result in zip(tweet_contexts, results, strict=True)
                ]
            )
            await session.commit()
        return StepOutput(content=[result.model_dump(mode="json") for result in results])

    async def _run_tweet_workflows_in_parallel(
        self,
        tweet_contexts: list[ResearchTweetContext],
        telegram_user_id: int,
    ) -> list[ResearchTweetSynthesisResult]:
        semaphore = asyncio.Semaphore(RESEARCH_TWEET_WORKFLOW_CONCURRENCY)
        return await asyncio.gather(
            *(self._run_tweet_workflow(item, telegram_user_id, semaphore) for item in tweet_contexts)
        )

    async def _run_tweet_workflow(
        self,
        tweet_context: ResearchTweetContext,
        telegram_user_id: int,
        semaphore: asyncio.Semaphore,
    ) -> ResearchTweetSynthesisResult:
        async with semaphore:
            result = await self.workflow.arun(
                input={},
                additional_data={
                    "tweet_context": tweet_context.model_dump(mode="json"),
                    "user_id": str(telegram_user_id),
                },
                user_id=str(telegram_user_id),
            )
        return ResearchTweetSynthesisResult.model_validate(getattr(result, "content", result))

    @staticmethod
    def _tweet_context(post) -> ResearchTweetContext:
        replies = [
            ReplyContextItem.model_validate(item)
            for item in (post.reply_context or [])[:ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT]
        ]
        return ResearchTweetContext(
            post_id=post.post_id,
            text=post.text or "",
            categories=[value for value in (post.categories or []) if isinstance(value, str)],
            media_urls=[url for url in (post.media_urls or []) if isinstance(url, str)],
            replies=replies,
        )
