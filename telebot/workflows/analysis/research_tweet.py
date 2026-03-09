from agno.workflow.loop import Loop
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

from telebot.agents.factory import AgnoFactory
from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.common.constants import WEB_RESEARCH_LOOP_MAX_ITERATIONS
from telebot.search.schemas import WebSearchWorkflowResult
from telebot.search.service import WebSearchWorkflowService
from telebot.workflows.analysis.research_support import (
    build_search_input_and_images,
    build_synthesis_prompt_and_images,
    loop_done,
    used_sources,
)
from telebot.workflows.analysis.types import ResearchTweetContext

RESEARCH_TWEET_SEARCH_STEP_NAME = "Run Web Search"
RESEARCH_TWEET_SYNTHESIZE_STEP_NAME = "Synthesize Tweet Research"


class RunWebSearchExecutor:
    def __init__(self, settings, agno_factory: AgnoFactory) -> None:
        self.search_service = WebSearchWorkflowService(settings, agno_factory)

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context = ResearchTweetContext.model_validate(step_input.additional_data["tweet_context"])
        critique = self._retry_guidance(step_input.input)
        search_input, images = build_search_input_and_images(context, critique)
        result = await self.search_service.run(
            search_input=search_input,
            user_id=str(step_input.additional_data["user_id"]),
            images=images,
        )
        return StepOutput(content=result.model_dump(mode="json"))

    @staticmethod
    def _retry_guidance(iteration_input) -> str:
        if not isinstance(iteration_input, dict):
            return ""
        return str(iteration_input.get("retry_guidance") or "").strip()


class SynthesizeTweetResearchExecutor:
    def __init__(self, agno_factory: AgnoFactory) -> None:
        self.agno_factory = agno_factory

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context = ResearchTweetContext.model_validate(step_input.additional_data["tweet_context"])
        search_output = step_input.get_step_output(RESEARCH_TWEET_SEARCH_STEP_NAME)
        web_result = self._web_result(search_output)
        prompt, images = build_synthesis_prompt_and_images(context, web_result)
        team = self.agno_factory.build_research_synthesis_team()
        response = await team.arun(
            prompt,
            user_id=str(step_input.additional_data["user_id"]),
            images=images,
        )
        result = ResearchTweetSynthesisResult.model_validate(self._content_of(response))
        if not result.evidence_sufficient and not result.retry_guidance:
            result.retry_guidance = (
                "Evidence was insufficient. Re-plan the web search to fill the missing context "
                "and target concrete sources for the unresolved claims."
            )
        result.related_sources = used_sources(result, web_result)
        return StepOutput(content=result.model_dump(mode="json"))

    @staticmethod
    def _web_result(step_output) -> WebSearchWorkflowResult:
        if step_output is None:
            return WebSearchWorkflowResult.model_validate({"plan": {"needs_search": False}, "evidence": []})
        return WebSearchWorkflowResult.model_validate(step_output.content)

    @staticmethod
    def _content_of(response):
        return getattr(response, "content", response)


def build_research_tweet_workflow(settings, agno_factory: AgnoFactory) -> Workflow:
    return Workflow(
        name="Research Tweet Workflow",
        steps=[
            Loop(
                name="Research Tweet Loop",
                max_iterations=WEB_RESEARCH_LOOP_MAX_ITERATIONS,
                forward_iteration_output=True,
                end_condition=loop_done,
                steps=[
                    Step(
                        name=RESEARCH_TWEET_SEARCH_STEP_NAME,
                        executor=RunWebSearchExecutor(settings, agno_factory),
                    ),
                    Step(
                        name=RESEARCH_TWEET_SYNTHESIZE_STEP_NAME,
                        executor=SynthesizeTweetResearchExecutor(agno_factory),
                    ),
                ],
            )
        ],
    )
