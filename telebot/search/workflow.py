import logging

from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

from telebot.common.constants import WEB_SEARCH_RETRIEVAL_FAILED_REASON
from telebot.search.planner import WebSearchPlannerService
from telebot.search.retrieval import ResearchRetrievalService
from telebot.search.schemas import PostResearchPlan, WebSearchWorkflowResult

PLAN_WEB_SEARCH_STEP_NAME = "Plan Web Search"


class PlanWebSearchExecutor:
    def __init__(self, agno_factory) -> None:
        self.planner = WebSearchPlannerService(agno_factory)

    async def __call__(self, step_input: StepInput) -> StepOutput:
        search_input = step_input.get_input_as_string() or ""
        user_id = str(step_input.additional_data.get("user_id", ""))
        images = list(step_input.additional_data.get("images", []))
        plan: PostResearchPlan = await self.planner.plan(search_input, user_id=user_id, images=images)
        return StepOutput(content=plan.model_dump(mode="json"))


class RetrieveWebEvidenceExecutor:
    def __init__(self, settings) -> None:
        self.retrieval = ResearchRetrievalService(settings)

    async def __call__(self, step_input: StepInput) -> StepOutput:
        search_input = step_input.get_input_as_string() or ""
        try:
            plan_output = step_input.get_step_output(PLAN_WEB_SEARCH_STEP_NAME)
            if plan_output is None:
                plan = PostResearchPlan(needs_search=False)
            else:
                plan = PostResearchPlan.model_validate(plan_output.content)
            evidence = await self.retrieval.retrieve(search_input, plan)
            result = WebSearchWorkflowResult(plan=plan, evidence=evidence)
        except Exception as exc:
            logging.warning("Web evidence retrieval failed: %s", exc)
            result = WebSearchWorkflowResult(
                plan=plan if plan.reason else PostResearchPlan.fallback(WEB_SEARCH_RETRIEVAL_FAILED_REASON),
                evidence=[],
            )
        return StepOutput(content=result.model_dump(mode="json"))


def build_web_search_workflow(settings, agno_factory) -> Workflow:
    return Workflow(
        name="Reusable Web Search Workflow",
        steps=[
            Step(name=PLAN_WEB_SEARCH_STEP_NAME, executor=PlanWebSearchExecutor(agno_factory)),
            Step(name="Retrieve Web Evidence", executor=RetrieveWebEvidenceExecutor(settings)),
        ],
    )
