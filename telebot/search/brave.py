import httpx

from telebot.common.constants import (
    BRAVE_AGE_KEY,
    BRAVE_GENERIC_KEY,
    BRAVE_GROUNDING_KEY,
    BRAVE_LLM_CONTEXT_URL,
    BRAVE_SOURCES_KEY,
    BRAVE_SNIPPETS_KEY,
    BRAVE_TITLE_KEY,
    BRAVE_URL_KEY,
    HTTP_HEADER_ACCEPT,
    HTTP_HEADER_ACCEPT_JSON,
    HTTP_HEADER_SUBSCRIPTION_TOKEN,
    HTTP_TIMEOUT_SECONDS,
    PDF_URL_SUFFIX,
)
from telebot.costs.tracker import WorkflowCostTracker
from telebot.search.schemas import SearchCandidate, SearchTask


class BraveLlmContextClient:
    def __init__(self, api_key: str, cost_tracker: WorkflowCostTracker | None = None) -> None:
        self.api_key = api_key
        self.cost_tracker = cost_tracker

    async def search(self, task: SearchTask) -> list[SearchCandidate]:
        payload = await self._request(task.query)
        return self._parse_candidates(payload, task.query)

    async def _request(self, query: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(
                BRAVE_LLM_CONTEXT_URL,
                params={"q": query},
                headers={
                    HTTP_HEADER_ACCEPT: HTTP_HEADER_ACCEPT_JSON,
                    HTTP_HEADER_SUBSCRIPTION_TOKEN: self.api_key,
                },
            )
            response.raise_for_status()
        loaded = response.json()
        if self.cost_tracker is not None:
            self.cost_tracker.record_brave_request()
        return loaded if isinstance(loaded, dict) else {}

    def _parse_candidates(self, payload: dict, query: str) -> list[SearchCandidate]:
        grounding = payload.get(BRAVE_GROUNDING_KEY, {})
        items = grounding.get(BRAVE_GENERIC_KEY, [])
        sources = payload.get(BRAVE_SOURCES_KEY, {})
        if not isinstance(items, list):
            return []
        if not isinstance(sources, dict):
            sources = {}
        candidates: list[SearchCandidate] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            url = str(item.get(BRAVE_URL_KEY, "")).strip()
            if not url:
                continue
            snippets = item.get(BRAVE_SNIPPETS_KEY, [])
            if not isinstance(snippets, list):
                snippets = []
            content_excerpts = [str(snippet).strip() for snippet in snippets if str(snippet).strip()]
            candidates.append(
                SearchCandidate(
                    url=url,
                    original_search_queries=[query],
                    title=self._optional_text(item.get(BRAVE_TITLE_KEY)),
                    source_date=self._source_date(sources.get(url)),
                    source_type="pdf" if self._is_pdf(url) else "html",
                    content_excerpts=content_excerpts,
                )
            )
        return candidates

    @staticmethod
    def _optional_text(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _source_date(value) -> str | None:
        if not isinstance(value, dict):
            return None
        age = value.get(BRAVE_AGE_KEY)
        if not isinstance(age, list):
            return None
        if len(age) > 1:
            return BraveLlmContextClient._optional_text(age[1])
        if age:
            return BraveLlmContextClient._optional_text(age[0])
        return None

    @staticmethod
    def _is_pdf(url: str) -> bool:
        return url.lower().split("?", 1)[0].endswith(PDF_URL_SUFFIX)
