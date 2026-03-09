import math

from openai import AsyncOpenAI

from telebot.common.constants import OPENAI_EMBEDDING_MODEL, WEB_RESEARCH_MAX_EVIDENCE
from telebot.search.chunking import chunk_text
from telebot.search.schemas import EvidenceChunk, ExtractedDocument


class EvidenceReranker:
    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)

    async def rerank(
        self,
        query_text: str,
        documents: list[ExtractedDocument],
    ) -> list[EvidenceChunk]:
        chunk_rows = self._chunk_rows(documents)
        if not chunk_rows:
            return []
        query_embedding = await self._embedding([query_text])
        chunk_embeddings = await self._embedding([row["content_excerpt"] for row in chunk_rows])
        grouped: dict[str, dict] = {}
        for row, embedding in zip(chunk_rows, chunk_embeddings, strict=True):
            score = self._cosine_similarity(query_embedding[0], embedding)
            group = grouped.setdefault(
                row["url"],
                {
                    "url": row["url"],
                    "original_search_queries": [],
                    "title": row["title"],
                    "description": row["description"],
                    "content_excerpts": [],
                    "source_type": row["source_type"],
                    "similarity_scores": [],
                },
            )
            for query in row["original_search_queries"]:
                if query not in group["original_search_queries"]:
                    group["original_search_queries"].append(query)
            group["content_excerpts"].append(row["content_excerpt"])
            group["similarity_scores"].append(score)
        ranked = sorted(
            grouped.values(),
            key=lambda item: max(item["similarity_scores"], default=0.0),
            reverse=True,
        )[:WEB_RESEARCH_MAX_EVIDENCE]
        return [EvidenceChunk.model_validate(item) for item in ranked]

    @staticmethod
    def _chunk_rows(documents: list[ExtractedDocument]) -> list[dict]:
        rows: list[dict] = []
        for document in documents:
            for excerpt in chunk_text(document.content):
                rows.append(
                    {
                        "url": document.url,
                        "original_search_queries": document.original_search_queries,
                        "title": document.title,
                        "description": document.description,
                        "content_excerpt": excerpt,
                        "source_type": document.source_type,
                    }
                )
        return rows

    async def _embedding(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(first, second, strict=True))
        first_norm = math.sqrt(sum(a * a for a in first))
        second_norm = math.sqrt(sum(b * b for b in second))
        if first_norm == 0 or second_norm == 0:
            return 0.0
        return numerator / (first_norm * second_norm)
