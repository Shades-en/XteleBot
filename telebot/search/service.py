import logging

from agno.media import Image
from pydantic import ValidationError

from telebot.common.constants import WEB_SEARCH_WORKFLOW_FAILED_REASON
from telebot.costs.tracker import WorkflowCostTracker
from telebot.search.schemas import WebSearchWorkflowResult
from telebot.search.workflow import build_web_search_workflow


class WebSearchWorkflowService:
    def __init__(
        self,
        settings,
        agno_factory,
        cost_tracker: WorkflowCostTracker | None = None,
    ) -> None:
        self.workflow = build_web_search_workflow(
            settings,
            agno_factory,
            cost_tracker=cost_tracker,
        )

    async def run(
        self,
        search_input: str,
        user_id: str,
        images: list[Image] | None = None,
    ) -> WebSearchWorkflowResult:
        result = await self.workflow.arun(
            input=search_input,
            additional_data={"user_id": user_id, "images": images or []},
            user_id=user_id,
        )
        content = getattr(result, "content", result)
        try:
            return WebSearchWorkflowResult.model_validate(content)
        except (ValidationError, TypeError, ValueError) as exc:
            logging.warning("Web search workflow returned invalid content: %s", exc)
            return WebSearchWorkflowResult.fallback(WEB_SEARCH_WORKFLOW_FAILED_REASON)
