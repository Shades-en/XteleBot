import logging

from agno.media import Image
from pydantic import ValidationError

from telebot.common.constants import WEB_SEARCH_PLANNER_FAILED_REASON
from telebot.costs.openai import record_run_output
from telebot.costs.tracker import WorkflowCostTracker
from telebot.search.schemas import PostResearchPlan


class WebSearchPlannerService:
    def __init__(self, agno_factory, cost_tracker: WorkflowCostTracker | None = None) -> None:
        self.agno_factory = agno_factory
        self.cost_tracker = cost_tracker

    async def plan(
        self,
        search_input: str,
        user_id: str,
        images: list[Image] | None = None,
    ) -> PostResearchPlan:
        planner = self.agno_factory.build_search_planner()
        try:
            response = await planner.arun(search_input, user_id=user_id, images=images or [])
            record_run_output(self.cost_tracker, response)
            return PostResearchPlan.model_validate(self._content_of(response))
        except (ValidationError, TypeError, ValueError) as exc:
            logging.warning("Web search planner returned invalid content: %s", exc)
            return PostResearchPlan.fallback(WEB_SEARCH_PLANNER_FAILED_REASON)
        except Exception as exc:
            logging.warning("Web search planner failed: %s", exc)
            return PostResearchPlan.fallback(WEB_SEARCH_PLANNER_FAILED_REASON)

    @staticmethod
    def _content_of(response):
        return getattr(response, "content", response)
