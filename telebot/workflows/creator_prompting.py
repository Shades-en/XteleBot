from telebot.common.constants import (
    CREATOR_RELATED_SOURCE_LIMIT,
    CREATOR_REPLY_CONTEXT_PROMPT_LIMIT,
)
from telebot.common.enums import CommandName
from telebot.prompts.creator import (
    CREATOR_COMMENT_SPEC,
    CREATOR_POST_SPEC,
    CREATOR_QUOTE_SPEC,
    CREATOR_SHARED_GUIDANCE,
)
from telebot.workflows.creator_types import CreatorContext

PROMPT_SPECS = {
    CommandName.POST_BY_INSPIRATION: CREATOR_POST_SPEC,
    CommandName.QUOTE: CREATOR_QUOTE_SPEC,
    CommandName.COMMENT: CREATOR_COMMENT_SPEC,
}


def build_creator_prompt(context: CreatorContext) -> str:
    return "\n\n".join(
        [
            f"Requested format: {context.command.value}",
            PROMPT_SPECS[context.command],
            CREATOR_SHARED_GUIDANCE,
            _source_post_section(context),
            _style_examples_section(context),
            _refinement_section(context),
            _output_rules(context.command),
        ]
    )


def _source_post_section(context: CreatorContext) -> str:
    source = context.source_post
    parts = [
        "Selected source post:",
        f"source_post_id: {source.post_id}",
        f"source_post_link: {source.source_url or 'n/a'}",
        f"source_post_text: {source.text or 'n/a'}",
        f"source_post_media_refs: {', '.join(source.media_urls) or 'none'}",
        f"research_purpose: {source.purpose or 'n/a'}",
        f"research_sentiment: {', '.join(source.agent_sentiment) or 'n/a'}",
        f"research_creator_brief: {source.agent_comments or 'n/a'}",
        "top_reply_context:",
        _reply_context_text(source.reply_context),
        "grounded_sources:",
        _related_sources_text(source.related_sources),
    ]
    return "\n".join(parts)


def _style_examples_section(context: CreatorContext) -> str:
    if not context.style_examples:
        return (
            "Style examples from the user's own posts:\n"
            "none available\n"
            "Fallback: rely on the user's stored memory and keep the voice natural."
        )
    lines = ["Style examples from the user's own posts:"]
    for index, example in enumerate(context.style_examples, start=1):
        posted_at = example.posted_at or "unknown"
        lines.append(
            f"{index}. posted_at={posted_at} post_id={example.post_id} text={example.text}"
        )
    lines.append(
        "Learn the user's tone, pacing, and framing from these examples. "
        "Do not reuse distinctive lines verbatim."
    )
    return "\n".join(lines)


def _refinement_section(context: CreatorContext) -> str:
    request = context.refinement or "Create a strong first draft."
    return f"Draft request:\n{request}"


def _reply_context_text(reply_context: list[dict]) -> str:
    if not reply_context:
        return "none"
    lines: list[str] = []
    for reply in reply_context[:CREATOR_REPLY_CONTEXT_PROMPT_LIMIT]:
        lines.append(
            " | ".join(
                [
                    f"rank={reply.get('rank_position', 'n/a')}",
                    f"author={reply.get('author_username') or 'n/a'}",
                    f"text={reply.get('text') or 'n/a'}",
                ]
            )
        )
    return "\n".join(lines)


def _related_sources_text(related_sources: list[dict]) -> str:
    if not related_sources:
        return "none"
    lines: list[str] = []
    for source in related_sources[:CREATOR_RELATED_SOURCE_LIMIT]:
        excerpt = (source.get("content_excerpt") or "").replace("\n", " ").strip()
        lines.append(
            " | ".join(
                [
                    f"title={source.get('title') or 'n/a'}",
                    f"date={source.get('source_date') or 'n/a'}",
                    f"url={source.get('url') or 'n/a'}",
                    f"excerpt={excerpt or 'n/a'}",
                ]
            )
        )
    return "\n".join(lines)


def _output_rules(command: CommandName) -> str:
    if command is CommandName.COMMENT:
        return (
            "Return only the comment draft. "
            "Keep it compact and do not include analysis notes, labels, bullets, or explanations."
        )
    if command is CommandName.QUOTE:
        return (
            "Return only the quote-post draft. "
            "Do not include analysis notes, labels, bullets, or explanations."
        )
    return (
        "Return only the standalone post draft. "
        "Do not include analysis notes, labels, bullets, or explanations."
    )
