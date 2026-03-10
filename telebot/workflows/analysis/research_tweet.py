from telebot.agents.factory import AgnoFactory
from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.costs.openai import record_run_output
from telebot.costs.tracker import WorkflowCostTracker
from telebot.search.schemas import WebSearchWorkflowResult
from telebot.search.service import WebSearchWorkflowService
from telebot.workflows.analysis.research_support import (
    build_search_input_and_images,
    build_synthesis_prompt_and_images,
    used_sources,
)
from telebot.workflows.analysis.types import ResearchTweetContext


async def run_tweet_web_search(
    search_service: WebSearchWorkflowService,
    tweet_context: ResearchTweetContext,
    user_id: str,
    critique: str = "",
) -> WebSearchWorkflowResult:
    search_input, images = build_search_input_and_images(tweet_context, critique)
    return await search_service.run(
        search_input=search_input,
        user_id=user_id,
        images=images,
    )


async def synthesize_tweet_research(
    agno_factory: AgnoFactory,
    tweet_context: ResearchTweetContext,
    web_result: WebSearchWorkflowResult,
    user_id: str,
    cost_tracker: WorkflowCostTracker | None = None,
) -> ResearchTweetSynthesisResult:
    prompt, images = build_synthesis_prompt_and_images(tweet_context, web_result)
    agent = agno_factory.build_research_synthesis_agent()
    response = await agent.arun(prompt, user_id=user_id, images=images)
    record_run_output(cost_tracker, response)
    result = ResearchTweetSynthesisResult.model_validate(_content_of(response))
    if not result.evidence_sufficient and not result.retry_guidance:
        result.retry_guidance = (
            "Evidence was insufficient. Re-plan the web search to fill the missing context "
            "and target concrete sources for the unresolved claims."
        )
    result.related_sources = used_sources(result, web_result)
    return result


def _content_of(response):
    return getattr(response, "content", response)
