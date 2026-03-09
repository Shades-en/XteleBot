import asyncio

from agno.tools.trafilatura import TrafilaturaTools

from telebot.common.constants import PDF_URL_SUFFIX, SEARCH_EXTRACTION_ERROR_PREFIX
from telebot.search.pdf import extract_pdf_text
from telebot.search.schemas import ExtractedDocument, SearchCandidate


class DocumentExtractor:
    def __init__(self) -> None:
        self.trafilatura = TrafilaturaTools(
            output_format="txt",
            with_metadata=False,
            include_comments=False,
            include_tables=False,
            enable_extract_metadata_only=False,
            enable_html_to_text=False,
            enable_extract_batch=False,
            enable_crawl_website=False,
        )

    async def extract(self, candidate: SearchCandidate) -> ExtractedDocument | None:
        if self._is_pdf(candidate.url):
            content = await extract_pdf_text(candidate.url)
        else:
            content = await asyncio.to_thread(
                self.trafilatura.extract_text,
                url=candidate.url,
                output_format="txt",
            )
        if not content or content.startswith(SEARCH_EXTRACTION_ERROR_PREFIX):
            return None
        return ExtractedDocument(
            url=candidate.url,
            original_search_queries=candidate.original_search_queries,
            title=candidate.title,
            description=candidate.description,
            content=content,
            source_type=candidate.source_type,
        )

    @staticmethod
    def _is_pdf(url: str) -> bool:
        return url.lower().split("?", 1)[0].endswith(PDF_URL_SUFFIX)
