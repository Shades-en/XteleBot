from telebot.common.constants import (
    CREATOR_COMMENT_MAX_CHARS,
    CREATOR_POST_MAX_CHARS,
    CREATOR_POST_MIN_CHARS,
    CREATOR_QUOTE_MAX_CHARS,
    CREATOR_QUOTE_MIN_CHARS,
    CREATOR_RELATED_SOURCE_LIMIT,
    CREATOR_REPLY_CONTEXT_PROMPT_LIMIT,
)
from telebot.common.enums import CommandName
from telebot.prompts.creator import (
    build_creator_refiner_style_guide,
    build_creator_style_guide,
)
from telebot.workflows.creator_types import CreatorContext, CreatorValidationResult


def build_creator_prompt(context: CreatorContext) -> str:
    return "\n\n".join(
        [
            f"Requested format: {context.command.value}",
            build_creator_style_guide(context.command),
            _source_post_section(context),
            _style_examples_section(context),
            _refinement_section(context),
            _output_rules(context.command),
        ]
    )


def build_creator_refiner_prompt(
    context: CreatorContext,
    draft: str,
    validation: CreatorValidationResult,
) -> str:
    sections = [
        f"Requested format: {context.command.value}",
        "Refine the draft so it matches this writing brief exactly.",
        build_creator_refiner_style_guide(context.command),
        _source_post_section(context),
        _style_examples_section(context),
        _refinement_section(context),
        f"Creator draft to refine:\n{draft}",
        _validation_feedback_section(validation),
        _refiner_output_rules(context.command),
    ]
    return "\n\n".join(section for section in sections if section)


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
            f"Keep it under {CREATOR_COMMENT_MAX_CHARS} characters. "
            "Follow the writing brief above exactly. "
            "Lead with a clear, natural line that feels human and direct. "
            "Do not include analysis notes, labels, bullets, or explanations. "
            "Never use an em dash or a semicolon."
        )
    if command is CommandName.QUOTE:
        return (
            "Return only the quote-post draft. "
            f"Keep it between {CREATOR_QUOTE_MIN_CHARS} and {CREATOR_QUOTE_MAX_CHARS} characters. "
            "Follow the writing brief above exactly. "
            "Make the opening line clear and strong for a reader with no context. "
            "Do not include analysis notes, labels, bullets, or explanations. "
            "Never use an em dash or a semicolon."
        )
    return (
        "Return only the standalone post draft. "
        f"Keep it between {CREATOR_POST_MIN_CHARS} and {CREATOR_POST_MAX_CHARS} characters. "
        "Follow the writing brief above exactly. "
        "Make the opening line strong, specific, and easy to understand cold. "
        "Do not include analysis notes, labels, bullets, or explanations. "
        "Never use an em dash or a semicolon."
    )


def _validation_feedback_section(validation: CreatorValidationResult) -> str:
    if not validation.has_issues:
        return ""
    return (
        "Deterministic validation feedback:\n"
        + "\n".join(f"- {issue}" for issue in validation.issues)
    )


def _refiner_output_rules(command: CommandName) -> str:
    if command is CommandName.COMMENT:
        return (
            "Return only the refined comment body. "
            f"Keep it under {CREATOR_COMMENT_MAX_CHARS} characters. "
            "Match the writing brief above exactly. "
            "Make it human, clean, concise, and naturally phrased. "
            "Never use an em dash or a semicolon."
        )
    if command is CommandName.QUOTE:
        return (
            "Return only the refined quote-post body. "
            f"Keep it between {CREATOR_QUOTE_MIN_CHARS} and {CREATOR_QUOTE_MAX_CHARS} characters. "
            "Match the writing brief above exactly. "
            "Improve narrative flow and spacing without losing the core take. "
            "Never use an em dash or a semicolon."
        )
    return (
        "Return only the refined standalone post body. "
        f"Keep it between {CREATOR_POST_MIN_CHARS} and {CREATOR_POST_MAX_CHARS} characters. "
        "Match the writing brief above exactly. "
        "Improve readability, line breaks, and narrative flow while preserving the core idea. "
        "Never use an em dash or a semicolon."
    )
