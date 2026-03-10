import asyncio
from urllib.parse import urlsplit, urlunsplit

from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    BLOCKED_SEARCH_DOMAINS,
    WEB_RESEARCH_FETCH_CONCURRENCY,
)
from telebot.costs.tracker import WorkflowCostTracker
from telebot.search.brave import BraveLlmContextClient
from telebot.search.rerank import EvidenceReranker
from telebot.search.schemas import EvidenceChunk, PostResearchPlan, SearchCandidate, SearchTask


class ResearchRetrievalService:
    def __init__(self, settings, cost_tracker: WorkflowCostTracker | None = None) -> None:
        self.brave = BraveLlmContextClient(settings.brave_search_api_key, cost_tracker=cost_tracker)
        self.reranker = EvidenceReranker(settings.openai_api_key, cost_tracker=cost_tracker)

    async def retrieve(
        self,
        query_text: str,
        plan: PostResearchPlan,
    ) -> list[EvidenceChunk]:
        if not plan.needs_search or not plan.queries:
            return []
        semaphore = asyncio.Semaphore(WEB_RESEARCH_FETCH_CONCURRENCY)
        search_results = await asyncio.gather(
            *(self._search(task, semaphore) for task in plan.queries),
        )
        candidates = self._dedupe_candidates(search_results)
        if not candidates:
            return []
        return await self.reranker.rank_candidates(
            query_text=query_text,
            candidates=candidates,
        )

    async def _search(
        self,
        task: SearchTask,
        semaphore: asyncio.Semaphore,
    ) -> list[SearchCandidate]:
        async with semaphore:
            candidates = await self.brave.search(task)
        return [candidate for candidate in candidates if self._is_allowed(candidate.url)]

    @staticmethod
    def _dedupe_candidates(search_results: list[list[SearchCandidate]]) -> list[SearchCandidate]:
        deduped: dict[str, SearchCandidate] = {}
        for result in search_results:
            for candidate in result:
                canonical_url = ResearchRetrievalService._canonicalize_url(candidate.url)
                existing = deduped.get(canonical_url)
                if existing is None:
                    deduped[canonical_url] = candidate.model_copy(update={"url": canonical_url})
                    continue
                for query in candidate.original_search_queries:
                    if query not in existing.original_search_queries:
                        existing.original_search_queries.append(query)
                for excerpt in candidate.content_excerpts:
                    if excerpt not in existing.content_excerpts:
                        existing.content_excerpts.append(excerpt)
                if not existing.title and candidate.title:
                    existing.title = candidate.title
                if not existing.source_date and candidate.source_date:
                    existing.source_date = candidate.source_date
        return list(deduped.values())

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.query, ""))

    @staticmethod
    def _is_allowed(url: str) -> bool:
        if not url.startswith(ALLOWED_URL_PREFIXES):
            return False
        hostname = (urlsplit(url).hostname or "").lower()
        return hostname not in BLOCKED_SEARCH_DOMAINS
