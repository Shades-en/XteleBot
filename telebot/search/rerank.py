import asyncio
import math

import tiktoken
from openai import AsyncOpenAI

from telebot.common.constants import (
    EMBEDDING_CONCURRENCY,
    OPENAI_EMBEDDING_MODEL,
    WEB_RESEARCH_EXCERPT_TOKEN_BUDGET,
    WEB_RESEARCH_TITLE_PREFILTER_MIN_KEEP,
    WEB_RESEARCH_TITLE_SIMILARITY_FLOOR,
)
from telebot.search.schemas import EvidenceChunk, SearchCandidate

EMBEDDING_SEMAPHORE = asyncio.Semaphore(EMBEDDING_CONCURRENCY)


class EvidenceReranker:
    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def rank_candidates(
        self,
        query_text: str,
        candidates: list[SearchCandidate],
    ) -> list[EvidenceChunk]:
        # Prefilter by title similarity and return sorted by score (highest first)
        filtered_candidates, query_embedding = await self._prefilter_by_title(
            query_text,
            candidates,
        )
        if not filtered_candidates:
            return []
        budgeted_candidates = self._trim_to_excerpt_budget(filtered_candidates)
        excerpt_rows = self._excerpt_rows(budgeted_candidates)
        if not excerpt_rows:
            return self._to_evidence_chunks(budgeted_candidates, {})
        excerpt_embeddings = await self._embedding(
            [row["merged_excerpt_text"] for row in excerpt_rows]
        )
        grouped_scores: dict[str, list[float]] = {}
        for row, embedding in zip(excerpt_rows, excerpt_embeddings, strict=True):
            score = self._cosine_similarity(query_embedding, embedding)
            grouped_scores.setdefault(row["candidate"].url, []).append(score)
        return self._to_evidence_chunks(budgeted_candidates, grouped_scores)

    async def _prefilter_by_title(
        self,
        query_text: str,
        candidates: list[SearchCandidate],
    ) -> tuple[list[SearchCandidate], list[float]]:
        title_rows = self._title_rows(candidates)
        if not title_rows:
            query_embedding = (await self._embedding([query_text]))[0]
            return candidates[:WEB_RESEARCH_TITLE_PREFILTER_MIN_KEEP], query_embedding
        embeddings = await self._embedding([query_text, *[row["title_text"] for row in title_rows]])
        query_embedding = embeddings[0]
        scored_candidates: list[tuple[SearchCandidate, float]] = []
        for row, embedding in zip(title_rows, embeddings[1:], strict=True):
            scored_candidates.append(
                (
                    row["candidate"],
                    self._cosine_similarity(query_embedding, embedding),
                )
            )
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        filtered_candidates = [
            candidate
            for candidate, score in scored_candidates
            if score >= WEB_RESEARCH_TITLE_SIMILARITY_FLOOR
        ]
        if not filtered_candidates:
            filtered_candidates = [
                candidate
                for candidate, _ in scored_candidates[:WEB_RESEARCH_TITLE_PREFILTER_MIN_KEEP]
            ]
        return filtered_candidates, query_embedding

    @staticmethod
    def _title_rows(candidates: list[SearchCandidate]) -> list[dict]:
        rows: list[dict] = []
        for candidate in candidates:
            title_text = (candidate.title or "").strip()
            if not title_text:
                continue
            rows.append({"candidate": candidate, "title_text": title_text})
        return rows

    def _trim_to_excerpt_budget(self, candidates: list[SearchCandidate]) -> list[SearchCandidate]:
        kept = list(candidates)
        while len(kept) > 1 and self._excerpt_token_count(kept) > WEB_RESEARCH_EXCERPT_TOKEN_BUDGET:
            kept.pop()
        return kept

    def _excerpt_token_count(self, candidates: list[SearchCandidate]) -> int:
        return sum(
            len(self.encoding.encode(excerpt))
            for candidate in candidates
            for excerpt in candidate.content_excerpts
            if excerpt
        )

    @staticmethod
    def _excerpt_rows(candidates: list[SearchCandidate]) -> list[dict]:
        rows: list[dict] = []
        for candidate in candidates:
            for excerpt in candidate.content_excerpts:
                if not excerpt:
                    continue
                merged_excerpt_text = " ".join(
                    part for part in (candidate.title, excerpt) if part
                ).strip()
                if not merged_excerpt_text:
                    continue
                rows.append(
                    {
                        "candidate": candidate,
                        "merged_excerpt_text": merged_excerpt_text,
                    }
                )
        return rows

    @staticmethod
    def _to_evidence_chunks(
        candidates: list[SearchCandidate],
        grouped_scores: dict[str, list[float]],
    ) -> list[EvidenceChunk]:
        chunks = [
            EvidenceReranker._build_evidence_chunk(candidate, grouped_scores.get(candidate.url, []))
            for candidate in candidates
        ]
        return sorted(
            chunks,
            key=lambda item: max(item.similarity_scores, default=0.0),
            reverse=True,
        )

    @staticmethod
    def _build_evidence_chunk(candidate: SearchCandidate, scores: list[float]) -> EvidenceChunk:
        valid_pairs = [
            (excerpt, score)
            for excerpt, score in zip(candidate.content_excerpts, scores, strict=True)
            if excerpt and excerpt.strip()
        ]
        ranked_pairs = sorted(valid_pairs, key=lambda item: item[1], reverse=True)
        return EvidenceChunk(
            url=candidate.url,
            original_search_queries=candidate.original_search_queries,
            title=candidate.title,
            source_date=candidate.source_date,
            content_excerpts=[excerpt for excerpt, _ in ranked_pairs],
            source_type=candidate.source_type,
            similarity_scores=[score for _, score in ranked_pairs],
        )

    async def _embedding(self, texts: list[str]) -> list[list[float]]:
        async with EMBEDDING_SEMAPHORE:
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
