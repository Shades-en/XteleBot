from pydantic import BaseModel


class ReplyContextItem(BaseModel):
    post_id: str
    text: str | None = None
    media_urls: list[str]
    likes_count: int | None = None
    comment_count: int | None = None
    reposts_count: int | None = None
    view_count: int | None = None
    author_username: str | None = None
    rank_position: int
    rating_score: float


class SourceEvidenceItem(BaseModel):
    url: str
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    content_excerpt: str | None = None
    source_type: str | None = None
