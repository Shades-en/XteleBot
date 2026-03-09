from typing import Any

from pydantic import BaseModel, Field


class TwitterUserResult(BaseModel):
    id: str | None = None
    userName: str | None = None
    name: str | None = None
    followers: int | None = None
    isBlueVerified: bool | None = None
    location: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AdvancedSearchAuthor(BaseModel):
    id: str | None = None
    userName: str | None = None
    name: str | None = None
    followers: int | None = None
    isBlueVerified: bool | None = None
    location: str | None = None


class AdvancedSearchMedia(BaseModel):
    media_url_https: str | None = None


class AdvancedSearchTweet(BaseModel):
    id: str
    text: str | None = None
    likeCount: int | None = None
    replyCount: int | None = None
    retweetCount: int | None = None
    viewCount: int | None = None
    createdAt: str | None = None
    author: AdvancedSearchAuthor | None = None
    quoted_tweet: dict[str, Any] | None = None
    extendedEntities: dict[str, Any] | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
