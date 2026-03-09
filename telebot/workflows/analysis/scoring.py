import math
from dataclasses import dataclass
from datetime import UTC, datetime

from telebot.common.constants import (
    ENGAGEMENT_COMPONENT_WEIGHTS,
    RANK_WEIGHTS,
    RECENCY_DECAY_HOURS,
    VELOCITY_MINUTES_FLOOR,
    VERIFIED_CREDIBILITY_BONUS,
)


@dataclass(frozen=True)
class AuthorSignals:
    followers: int = 0
    is_verified: bool = False


class PostRankScorer:
    def score(self, post, author: AuthorSignals) -> float:
        likes = float(post.likes_count or 0)
        replies = float(post.comment_count or 0)
        reposts = float(post.reposts_count or 0)
        views = float(post.view_count or 0)
        weighted_engagement = self._weighted_engagement(
            likes=likes,
            replies=replies,
            reposts=reposts,
            views=views,
        )
        engagement_strength = math.log1p(weighted_engagement)
        age_minutes = self._age_minutes(post)
        age_hours = max(age_minutes / 60.0, 1.0 / 60.0)
        engagement_velocity = math.log1p(
            weighted_engagement / max(age_minutes, VELOCITY_MINUTES_FLOOR)
        )
        author_reach = math.log1p(max(author.followers, 0))
        author_credibility = (
            VERIFIED_CREDIBILITY_BONUS if author.is_verified else 0.0
        )
        discussion_depth = math.log1p(replies)
        recency = math.exp(-age_hours / RECENCY_DECAY_HOURS)
        media_richness = 1.0 if post.media_urls else 0.0
        return (
            RANK_WEIGHTS["engagement_strength"] * engagement_strength
            + RANK_WEIGHTS["engagement_velocity"] * engagement_velocity
            + RANK_WEIGHTS["author_reach"] * author_reach
            + RANK_WEIGHTS["author_credibility"] * author_credibility
            + RANK_WEIGHTS["discussion_depth"] * discussion_depth
            + RANK_WEIGHTS["recency"] * recency
            + RANK_WEIGHTS["media_richness"] * media_richness
        )

    @staticmethod
    def _weighted_engagement(
        likes: float,
        replies: float,
        reposts: float,
        views: float,
    ) -> float:
        return (
            likes * ENGAGEMENT_COMPONENT_WEIGHTS["likes"]
            + replies * ENGAGEMENT_COMPONENT_WEIGHTS["replies"]
            + reposts * ENGAGEMENT_COMPONENT_WEIGHTS["reposts"]
            + views * ENGAGEMENT_COMPONENT_WEIGHTS["views"]
        )

    def _age_minutes(self, post) -> float:
        created_at = self._created_at(post)
        now = datetime.now(UTC)
        age_seconds = max((now - created_at).total_seconds(), 0.0)
        return max(age_seconds / 60.0, VELOCITY_MINUTES_FLOOR)

    def _created_at(self, post) -> datetime:
        if getattr(post, "posted_at", None) is not None:
            return post.posted_at.replace(tzinfo=UTC)
        raw_payload = post.raw_payload or {}
        created_at_raw = raw_payload.get("createdAt")
        if isinstance(created_at_raw, str):
            parsed = self._parse_datetime(created_at_raw)
            if parsed is not None:
                return parsed
        return post.created_at.replace(tzinfo=UTC)

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)


class ReplyRankScorer:
    def score(self, reply, author: AuthorSignals) -> float:
        likes = float(reply.likeCount or 0)
        replies = float(reply.replyCount or 0)
        reposts = float(reply.retweetCount or 0)
        views = float(reply.viewCount or 0)
        engagement = PostRankScorer._weighted_engagement(
            likes=likes,
            replies=replies,
            reposts=reposts,
            views=views,
        )
        reach = math.log1p(max(author.followers, 0))
        credibility = VERIFIED_CREDIBILITY_BONUS if author.is_verified else 0.0
        return math.log1p(engagement) + reach + credibility
