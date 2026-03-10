from agno.media import Image

from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    CREATOR_CANDIDATE_PREVIEW_LENGTH,
    CREATOR_SOURCE_MEDIA_LIMIT,
)
from telebot.common.messages import TEXT_CREATOR_ALTERNATIVE_ITEM_TEMPLATE
from telebot.workflows.creator_types import (
    CreatorContext,
    CreatorSourcePost,
    CreatorStyleExample,
)


def build_creator_context(command, source_post, style_examples, refinement: str | None = None) -> CreatorContext:
    return CreatorContext(
        command=command,
        source_post=creator_source_post(source_post),
        style_examples=[
            CreatorStyleExample(
                post_id=post.post_id,
                text=post.text or "",
                posted_at=post.posted_at.isoformat() if post.posted_at else None,
            )
            for post in style_examples
        ],
        refinement=refinement,
    )


def creator_images(context: CreatorContext) -> list[Image]:
    return [Image(url=url) for url in context.source_post.media_urls]


def render_candidate_previews(posts: list[object]) -> str:
    return "\n\n".join(
        TEXT_CREATOR_ALTERNATIVE_ITEM_TEMPLATE.format(
            index=index,
            rank=getattr(post, "rank_position", "n/a") or "n/a",
            text=_preview_text(getattr(post, "text", None)),
            source_url=getattr(post, "post_url", None) or "n/a",
        )
        for index, post in enumerate(posts, start=1)
    )


def creator_source_post(source_post) -> CreatorSourcePost:
    return CreatorSourcePost(
        post_id=source_post.post_id,
        source_url=source_post.post_url,
        text=source_post.text or "",
        purpose=source_post.purpose,
        media_urls=_valid_media_urls(source_post.media_urls or []),
        reply_context=list(source_post.reply_context or []),
        agent_sentiment=list(source_post.agent_sentiment or []),
        agent_comments=source_post.agent_comments or "",
        related_sources=list(source_post.related_sources or []),
    )


def _valid_media_urls(media_urls: list[str]) -> list[str]:
    return [
        url
        for url in media_urls[:CREATOR_SOURCE_MEDIA_LIMIT]
        if isinstance(url, str) and url.startswith(ALLOWED_URL_PREFIXES)
    ]


def _preview_text(text: str | None) -> str:
    normalized = " ".join((text or "").split()).strip()
    if not normalized:
        return "n/a"
    if len(normalized) <= CREATOR_CANDIDATE_PREVIEW_LENGTH:
        return normalized
    return f"{normalized[: CREATOR_CANDIDATE_PREVIEW_LENGTH - 3].rstrip()}..."
