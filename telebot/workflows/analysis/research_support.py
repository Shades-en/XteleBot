from agno.media import Image

from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT,
    RESEARCH_POST_MEDIA_LIMIT,
    RESEARCH_REPLY_MEDIA_LIMIT,
    SYNTHESIS_EXCERPTS_PER_URL,
    SYNTHESIS_MAX_URLS,
    SYNTHESIS_REPLY_MEDIA_LIMIT,
)
from telebot.db.schemas import SourceEvidenceItem
from telebot.search.schemas import WebSearchWorkflowResult
from telebot.workflows.analysis.types import ResearchTweetContext


def build_search_input_and_images(
    context: ResearchTweetContext,
    critique: str,
) -> tuple[str, list[Image]]:
    images = _context_images(context)
    reply_lines = _reply_lines(context, "reply_media_refs")
    parts = [
        f"post_text: {context.text}",
        f"post_media_refs: {', '.join(context.media_urls) or 'none'}",
        f"categories: {', '.join(context.categories) or 'none'}",
        "top_ranked_replies:",
        "\n\n".join(reply_lines) or "none",
    ]
    if critique:
        parts.extend(["retry_guidance:", critique])
    return "\n\n".join(parts), images


def build_synthesis_prompt_and_images(
    context: ResearchTweetContext,
    web_result: WebSearchWorkflowResult,
) -> tuple[str, list[Image]]:
    images = [Image(url=url) for url in _valid_urls(context.media_urls, RESEARCH_POST_MEDIA_LIMIT)]
    reply_lines = _reply_lines(context, "reply_image_refs")
    evidence_lines = _evidence_lines(web_result)
    prompt = "\n\n".join(
        [
            f"post_text: {context.text}",
            f"categories: {', '.join(context.categories) or 'none'}",
            "top_ranked_replies:",
            "\n\n".join(reply_lines) or "none",
            f"web_search_needed: {web_result.plan.needs_search}",
            f"planner_reason: {web_result.plan.reason}",
            f"claims_to_verify: {'; '.join(web_result.plan.claims_to_verify) or 'none'}",
            "grounded_evidence:",
            "\n\n".join(evidence_lines) or "none",
        ]
    )
    return prompt, images


def used_sources(
    result: ResearchTweetSynthesisResult,
    web_result: WebSearchWorkflowResult,
) -> list[SourceEvidenceItem]:
    evidence_by_url = {item.url: item for item in web_result.evidence}
    sources: list[SourceEvidenceItem] = []
    for source in result.related_sources:
        evidence = evidence_by_url.get(source.url)
        if evidence is None:
            continue
        sources.append(
            SourceEvidenceItem(
                url=evidence.url,
                title=evidence.title,
                source_date=evidence.source_date,
                content_excerpt="\n\n".join(evidence.content_excerpts[:2]),
                source_type=evidence.source_type,
            )
        )
    return sources
def _context_images(context: ResearchTweetContext) -> list[Image]:
    images = [Image(url=url) for url in _valid_urls(context.media_urls, RESEARCH_POST_MEDIA_LIMIT)]
    for reply in context.replies:
        reply_images = _valid_urls(reply.media_urls, RESEARCH_REPLY_MEDIA_LIMIT)
        images.extend(Image(url=url) for url in reply_images)
    return images


def _reply_lines(context: ResearchTweetContext, media_label: str) -> list[str]:
    lines: list[str] = []
    limit = RESEARCH_REPLY_MEDIA_LIMIT if media_label == "reply_media_refs" else SYNTHESIS_REPLY_MEDIA_LIMIT
    for reply in context.replies:
        reply_images = _valid_urls(reply.media_urls, limit)
        lines.append(
            "\n".join(
                [
                    f"reply_rank: {reply.rank_position}",
                    f"reply_text: {reply.text or ''}",
                    f"{media_label}: {', '.join(reply_images) or 'none'}",
                ]
            )
        )
    return lines


def _evidence_lines(web_result: WebSearchWorkflowResult) -> list[str]:
    lines: list[str] = []
    for item in web_result.evidence[:SYNTHESIS_MAX_URLS]:
        excerpts = [
            excerpt[:RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT]
            for excerpt in item.content_excerpts[:SYNTHESIS_EXCERPTS_PER_URL]
        ]
        lines.append(
            "\n".join(
                [
                    f"title: {item.title or ''}",
                    f"source_date: {item.source_date or ''}",
                    f"content_excerpts: {' || '.join(excerpts) or 'none'}",
                ]
            )
        )
    return lines


def _valid_urls(urls: list[str], limit: int) -> list[str]:
    return [url for url in urls[:limit] if isinstance(url, str) and url.startswith(ALLOWED_URL_PREFIXES)]
