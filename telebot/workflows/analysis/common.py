from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from telebot.common.constants import PROGRESS_STAGES
from telebot.costs.tracker import WorkflowCostTracker

ProgressCallback = Callable[[str, str], Awaitable[None]]


@dataclass
class AnalysisContext:
    telegram_user_id: int
    x_username: str
    x_id: str
    progress_callback: ProgressCallback | None = None
    cost_tracker: WorkflowCostTracker | None = None


@dataclass(frozen=True)
class CollectedTweet:
    tweet: object
    source_query: str


async def report_progress(context: AnalysisContext, stage: str) -> None:
    if context.progress_callback is None:
        return
    await context.progress_callback(stage, PROGRESS_STAGES[stage])


def extract_media_urls(extended_entities: dict[str, Any] | None) -> list[str]:
    if not isinstance(extended_entities, dict):
        return []
    media_items = extended_entities.get("media", [])
    if not isinstance(media_items, list):
        return []
    urls: list[str] = []
    for media in media_items:
        if isinstance(media, dict):
            url = media.get("media_url_https") or media.get("media_url")
        elif isinstance(media, str):
            url = media
        else:
            url = None
        if isinstance(url, str) and url:
            urls.append(url)
    return urls


def parse_twitter_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.astimezone(UTC).replace(tzinfo=None)
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC).replace(tzinfo=None)
    return parsed.astimezone(UTC).replace(tzinfo=None)
