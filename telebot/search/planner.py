from agno.media import Image

from telebot.search.schemas import PostResearchPlan


class WebSearchPlannerService:
    def __init__(self, agno_factory) -> None:
        self.agno_factory = agno_factory

    async def plan(
        self,
        search_input: str,
        user_id: str,
        images: list[Image] | None = None,
    ) -> PostResearchPlan:
        planner = self.agno_factory.build_search_planner()
        response = await planner.arun(search_input, user_id=user_id, images=images or [])
        return PostResearchPlan.model_validate(self._content_of(response))

    @staticmethod
    def _content_of(response):
        return getattr(response, "content", response)
