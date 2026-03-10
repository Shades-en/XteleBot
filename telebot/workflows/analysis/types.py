from dataclasses import dataclass

from pydantic import BaseModel, Field

from telebot.db.schemas import ReplyContextItem


@dataclass(frozen=True)
class RankedReply:
    reply: object
    rank_position: int
    rating_score: float


class ResearchTweetContext(BaseModel):
    post_id: str
    rank_position: int
    text: str = ""
    categories: list[str] = Field(default_factory=list)
    media_urls: list[str] = Field(default_factory=list)
    replies: list[ReplyContextItem] = Field(default_factory=list)
