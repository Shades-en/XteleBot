from agno.media import Image

from telebot.search.schemas import WebSearchWorkflowResult
from telebot.search.workflow import build_web_search_workflow


class WebSearchWorkflowService:
    def __init__(self, settings, agno_factory) -> None:
        self.workflow = build_web_search_workflow(settings, agno_factory)

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
        return WebSearchWorkflowResult.model_validate(content)
