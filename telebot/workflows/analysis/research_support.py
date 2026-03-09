from agno.media import Image
from agno.workflow.step import StepOutput

from telebot.agents.schemas import ResearchTweetSynthesisResult
from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT,
    RESEARCH_EVIDENCE_EXCERPTS_PER_SOURCE,
    RESEARCH_POST_MEDIA_LIMIT,
    RESEARCH_REPLY_MEDIA_LIMIT,
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
    images = _context_images(context)
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
                summary=evidence.description,
                description=evidence.description,
                content_excerpt="\n\n".join(evidence.content_excerpts[:2]),
                source_type=evidence.source_type,
            )
        )
    return sources


def loop_done(iteration_outputs: list[StepOutput]) -> bool:
    if not iteration_outputs:
        return False
    last_output = iteration_outputs[-1].content
    if not isinstance(last_output, dict):
        return False
    return bool(last_output.get("evidence_sufficient"))


def _context_images(context: ResearchTweetContext) -> list[Image]:
    images = [Image(url=url) for url in _valid_urls(context.media_urls, RESEARCH_POST_MEDIA_LIMIT)]
    for reply in context.replies:
        reply_images = _valid_urls(reply.media_urls, RESEARCH_REPLY_MEDIA_LIMIT)
        images.extend(Image(url=url) for url in reply_images)
    return images


def _reply_lines(context: ResearchTweetContext, media_label: str) -> list[str]:
    lines: list[str] = []
    for reply in context.replies:
        reply_images = _valid_urls(reply.media_urls, RESEARCH_REPLY_MEDIA_LIMIT)
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
    for item in web_result.evidence:
        excerpts = [
            excerpt[:RESEARCH_EVIDENCE_EXCERPT_CHAR_LIMIT]
            for excerpt in item.content_excerpts[:RESEARCH_EVIDENCE_EXCERPTS_PER_SOURCE]
        ]
        lines.append(
            "\n".join(
                [
                    f"url: {item.url}",
                    f"queries: {', '.join(item.original_search_queries)}",
                    f"title: {item.title or ''}",
                    f"description: {item.description or ''}",
                    f"content_excerpts: {' || '.join(excerpts) or 'none'}",
                ]
            )
        )
    return lines


def _valid_urls(urls: list[str], limit: int) -> list[str]:
    return [url for url in urls[:limit] if isinstance(url, str) and url.startswith(ALLOWED_URL_PREFIXES)]
