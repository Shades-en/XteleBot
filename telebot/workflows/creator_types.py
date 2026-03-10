from dataclasses import dataclass, field
from typing import Any

from telebot.common.enums import CommandName


@dataclass(frozen=True)
class CreatorStyleExample:
    post_id: str
    text: str
    posted_at: str | None = None


@dataclass(frozen=True)
class CreatorSourcePost:
    post_id: str
    source_url: str | None
    text: str
    purpose: str | None
    media_urls: list[str] = field(default_factory=list)
    reply_context: list[dict[str, Any]] = field(default_factory=list)
    agent_sentiment: list[str] = field(default_factory=list)
    agent_comments: str = ""
    related_sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class CreatorContext:
    command: CommandName
    source_post: CreatorSourcePost
    style_examples: list[CreatorStyleExample]
    refinement: str | None = None
