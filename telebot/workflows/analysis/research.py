import asyncio
from collections import Counter

from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.common.constants import (
    ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT,
    ANALYSIS_RESEARCH_TARGET_LIMIT,
    PURPOSE_REBALANCE_BORDERLINE_DELTA,
    PURPOSE_REBALANCE_DOMINANCE_THRESHOLD,
    RESEARCH_TWEET_WORKFLOW_CONCURRENCY,
)
from telebot.common.enums import PostPurpose
from telebot.db.repositories.posts import PostRepository
from telebot.db.schemas import ReplyContextItem
from telebot.search.schemas import WebSearchWorkflowResult
from telebot.search.service import WebSearchWorkflowService
from telebot.workflows.analysis.common import AnalysisContext, report_progress
from telebot.workflows.analysis.research_tweet import (
    run_tweet_web_search,
    synthesize_tweet_research,
)
from telebot.workflows.analysis.types import ResearchTweetContext


class ResearchTweetsExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agno_factory: AgnoFactory,
    ) -> None:
        self.session_factory = session_factory
        self.agno_factory = agno_factory

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        async with self.session_factory() as session:
            repo = PostRepository(session)
            if await repo.has_research_for_today(context.telegram_user_id):
                return StepOutput(content="research_skipped")
            await report_progress(context, "plan_research")
            posts = await repo.top_safe_ranked_posts(
                context.telegram_user_id,
                limit=ANALYSIS_RESEARCH_TARGET_LIMIT,
            )
            tweet_contexts = [self._tweet_context(post) for post in posts]
            search_service = WebSearchWorkflowService(
                self.agno_factory.settings,
                self.agno_factory,
                cost_tracker=context.cost_tracker,
            )
            await report_progress(context, "retrieve_research")
            web_results = await self._run_web_searches_in_parallel(
                search_service,
                tweet_contexts,
                context.telegram_user_id,
            )
            await report_progress(context, "compile_research")
            await report_progress(context, "synthesize_research")
            results = await self._run_syntheses_in_parallel(
                tweet_contexts,
                web_results,
                context.telegram_user_id,
                context,
            )
            rebalanced_results = self._rebalance_purposes(tweet_contexts, results)
            await repo.bulk_update_research_fields(
                [
                    {
                        "post_id": tweet_context.post_id,
                        "related_sources": [item.model_dump(mode="json") for item in result.related_sources],
                        "agent_sentiment": [item.value for item in result.agent_sentiment],
                        "agent_comments": result.agent_comments,
                        "purpose": result.purpose.value,
                    }
                    for tweet_context, result in zip(tweet_contexts, rebalanced_results, strict=True)
                ]
            )
            await session.commit()
            # results = []
        return StepOutput(content=[result.model_dump(mode="json") for result in rebalanced_results])

    async def _run_web_searches_in_parallel(
        self,
        search_service: WebSearchWorkflowService,
        tweet_contexts: list[ResearchTweetContext],
        telegram_user_id: int,
    ) -> list[WebSearchWorkflowResult]:
        semaphore = asyncio.Semaphore(RESEARCH_TWEET_WORKFLOW_CONCURRENCY)
        return await asyncio.gather(
            *(
                self._run_web_search(search_service, item, telegram_user_id, semaphore)
                for item in tweet_contexts
            )
        )

    async def _run_web_search(
        self,
        search_service: WebSearchWorkflowService,
        tweet_context: ResearchTweetContext,
        telegram_user_id: int,
        semaphore: asyncio.Semaphore,
    ) -> WebSearchWorkflowResult:
        async with semaphore:
            return await run_tweet_web_search(
                search_service,
                tweet_context,
                str(telegram_user_id),
            )

    async def _run_syntheses_in_parallel(
        self,
        tweet_contexts: list[ResearchTweetContext],
        web_results: list[WebSearchWorkflowResult],
        telegram_user_id: int,
        context: AnalysisContext,
    ) -> list[ResearchTweetSynthesisResult]:
        semaphore = asyncio.Semaphore(RESEARCH_TWEET_WORKFLOW_CONCURRENCY)
        return await asyncio.gather(
            *(
                self._run_synthesis(
                    tweet_context,
                    web_result,
                    telegram_user_id,
                    semaphore,
                    context,
                )
                for tweet_context, web_result in zip(tweet_contexts, web_results, strict=True)
            )
        )

    async def _run_synthesis(
        self,
        tweet_context: ResearchTweetContext,
        web_result: WebSearchWorkflowResult,
        telegram_user_id: int,
        semaphore: asyncio.Semaphore,
        context: AnalysisContext,
    ) -> ResearchTweetSynthesisResult:
        async with semaphore:
            return await synthesize_tweet_research(
                self.agno_factory,
                tweet_context,
                web_result,
                str(telegram_user_id),
                cost_tracker=context.cost_tracker,
            )

    @staticmethod
    def _tweet_context(post) -> ResearchTweetContext:
        replies = [
            ReplyContextItem.model_validate(item)
            for item in (post.reply_context or [])[:ANALYSIS_REPLY_CONTEXT_TO_RESEARCH_LIMIT]
        ]
        return ResearchTweetContext(
            post_id=post.post_id,
            rank_position=post.rank_position or 0,
            text=post.text or "",
            categories=[value for value in (post.categories or []) if isinstance(value, str)],
            media_urls=[url for url in (post.media_urls or []) if isinstance(url, str)],
            replies=replies,
        )

    @staticmethod
    def _rebalance_purposes(
        tweet_contexts: list[ResearchTweetContext],
        results: list[ResearchTweetSynthesisResult],
    ) -> list[ResearchTweetSynthesisResult]:
        if not results:
            return results
        counts = Counter(result.purpose for result in results)
        dominant_purpose, dominant_count = counts.most_common(1)[0]
        if dominant_count / len(results) < PURPOSE_REBALANCE_DOMINANCE_THRESHOLD:
            return results
        missing_purposes = [
            purpose
            for purpose in (PostPurpose.QUOTE, PostPurpose.COMMENT)
            if counts[purpose] == 0
        ]
        if not missing_purposes:
            return results
        rebalanced = list(results)
        used_indexes: set[int] = set()
        for target_purpose in missing_purposes:
            candidate_index = ResearchTweetsExecutor._best_borderline_candidate(
                tweet_contexts,
                rebalanced,
                dominant_purpose,
                target_purpose,
                used_indexes,
            )
            if candidate_index is None:
                continue
            used_indexes.add(candidate_index)
            rebalanced[candidate_index] = ResearchTweetsExecutor._with_rebalanced_purpose(
                rebalanced[candidate_index],
                target_purpose,
            )
        return rebalanced

    @staticmethod
    def _best_borderline_candidate(
        tweet_contexts: list[ResearchTweetContext],
        results: list[ResearchTweetSynthesisResult],
        dominant_purpose: PostPurpose,
        target_purpose: PostPurpose,
        used_indexes: set[int],
    ) -> int | None:
        options: list[tuple[float, int, int]] = []
        for index, (tweet_context, result) in enumerate(zip(tweet_contexts, results, strict=True)):
            if index in used_indexes or result.purpose != dominant_purpose:
                continue
            dominant_score = result.purpose_scores.for_purpose(dominant_purpose)
            alternate_score = result.purpose_scores.for_purpose(target_purpose)
            margin = dominant_score - alternate_score
            if margin > PURPOSE_REBALANCE_BORDERLINE_DELTA:
                continue
            options.append((margin, -tweet_context.rank_position, index))
        if not options:
            return None
        options.sort()
        return options[0][2]

    @staticmethod
    def _with_rebalanced_purpose(
        result: ResearchTweetSynthesisResult,
        target_purpose: PostPurpose,
    ) -> ResearchTweetSynthesisResult:
        return result.model_copy(
            update={
                "purpose": target_purpose,
                "purpose_rationale": (
                    f"{result.purpose_rationale} Rebalanced to {target_purpose.value} because this was a "
                    "borderline fit and the batch was over-concentrated in one purpose."
                ).strip()
            }
        )
