import asyncio
import json
from urllib.parse import urlsplit, urlunsplit

from agno.tools.serper import SerperTools

from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    BLOCKED_SEARCH_DOMAINS,
    PDF_URL_SUFFIX,
    SERPER_LINK_KEY,
    SERPER_ORGANIC_KEY,
    SERPER_SNIPPET_KEY,
    SERPER_TITLE_KEY,
    WEB_RESEARCH_FETCH_CONCURRENCY,
    WEB_RESEARCH_MAX_FETCHED_PAGES,
    WEB_RESEARCH_MAX_URLS_PER_TASK,
)
from telebot.search.extractors import DocumentExtractor
from telebot.search.rerank import EvidenceReranker
from telebot.search.schemas import (
    EvidenceChunk,
    ExtractedDocument,
    PostResearchPlan,
    SearchCandidate,
    SearchTask,
)


class ResearchRetrievalService:
    def __init__(self, settings) -> None:
        self.serper = SerperTools(
            api_key=settings.serper_api_key,
            num_results=WEB_RESEARCH_MAX_URLS_PER_TASK,
            enable_search_news=False,
            enable_search_scholar=False,
            enable_scrape_webpage=False,
        )
        self.extractor = DocumentExtractor()
        self.reranker = EvidenceReranker(settings.openai_api_key)

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
        documents = await asyncio.gather(
            *(self._extract(candidate, semaphore) for candidate in candidates),
        )
        extracted = [document for document in documents if document is not None]
        return await self.reranker.rerank(query_text, extracted)

    async def _search(
        self,
        task: SearchTask,
        semaphore: asyncio.Semaphore,
    ) -> list[SearchCandidate]:
        async with semaphore:
            payload = await asyncio.to_thread(
                self.serper.search_web,
                query=task.query,
                num_results=WEB_RESEARCH_MAX_URLS_PER_TASK,
            )
        parsed = self._safe_json_load(payload)
        candidates: list[SearchCandidate] = []
        for item in parsed.get(SERPER_ORGANIC_KEY, []):
            url = self._canonicalize_url(str(item.get(SERPER_LINK_KEY, "")).strip())
            if not self._is_scrapeable_url(url):
                continue
            candidates.append(
                SearchCandidate(
                    url=url,
                    original_search_queries=[task.query],
                    title=item.get(SERPER_TITLE_KEY),
                    description=item.get(SERPER_SNIPPET_KEY),
                    source_type="pdf" if self._is_pdf(url) else "html",
                )
            )
        return candidates

    async def _extract(
        self,
        candidate: SearchCandidate,
        semaphore: asyncio.Semaphore,
    ) -> ExtractedDocument | None:
        async with semaphore:
            return await self.extractor.extract(candidate)

    @staticmethod
    def _dedupe_candidates(search_results: list[list[SearchCandidate]]) -> list[SearchCandidate]:
        deduped: dict[str, SearchCandidate] = {}
        for result in search_results:
            for candidate in result:
                existing = deduped.get(candidate.url)
                if existing is None:
                    deduped[candidate.url] = candidate
                else:
                    for query in candidate.original_search_queries:
                        if query not in existing.original_search_queries:
                            existing.original_search_queries.append(query)
                if len(deduped) >= WEB_RESEARCH_MAX_FETCHED_PAGES:
                    return list(deduped.values())
        return list(deduped.values())

    @staticmethod
    def _safe_json_load(payload: str) -> dict:
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.query, ""))

    @staticmethod
    def _is_scrapeable_url(url: str) -> bool:
        if not url.startswith(ALLOWED_URL_PREFIXES):
            return False
        hostname = urlsplit(url).hostname or ""
        return hostname.lower() not in BLOCKED_SEARCH_DOMAINS

    @staticmethod
    def _is_pdf(url: str) -> bool:
        return url.lower().split("?", 1)[0].endswith(PDF_URL_SUFFIX)
