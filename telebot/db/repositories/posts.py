from datetime import date
from decimal import Decimal

from sqlalchemy import Select, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from telebot.common.constants import (
    ANALYSIS_REPLY_TARGET_LIMIT,
    ANALYSIS_TOP_RANKED_LIMIT,
    CREATOR_STYLE_EXAMPLE_FETCH_LIMIT,
    CREATOR_STYLE_EXAMPLE_LIMIT,
    CREATOR_STYLE_EXCLUDED_PREFIXES,
    CREATOR_STYLE_MIN_TEXT_LENGTH,
)
from telebot.common.enums import PostPurpose
from telebot.db.social_models import Post

class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_post(self, post_id: str) -> Post | None:
        result = await self.session.execute(select(Post).where(Post.post_id == post_id))
        return result.scalar_one_or_none()

    async def get_posts(self, post_ids: list[str]) -> dict[str, Post]:
        if not post_ids:
            return {}
        result = await self.session.execute(select(Post).where(Post.post_id.in_(post_ids)))
        return {post.post_id: post for post in result.scalars().all()}

    async def bulk_upsert_posts(self, rows: list[dict]) -> None:
        normalized_rows = await self._normalized_rows(rows)
        if not normalized_rows:
            return
        statement = insert(Post).values(normalized_rows)
        update_columns = {
            "post_url": statement.excluded.post_url,
            "posted_at": statement.excluded.posted_at,
            "own_posts": statement.excluded.own_posts,
            "text": statement.excluded.text,
            "media_urls": statement.excluded.media_urls,
            "likes_count": statement.excluded.likes_count,
            "comment_count": statement.excluded.comment_count,
            "reposts_count": statement.excluded.reposts_count,
            "view_count": statement.excluded.view_count,
            "source_query": statement.excluded.source_query,
            "author_username": statement.excluded.author_username,
            "date_of_analysis": statement.excluded.date_of_analysis,
            "analysed_for_user_id": statement.excluded.analysed_for_user_id,
            "raw_payload": statement.excluded.raw_payload,
        }
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[Post.post_id],
                set_=update_columns,
            )
        )

    async def has_analysis_for_today(self, telegram_user_id: int) -> bool:
        result = await self.session.execute(
            select(Post.post_id)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .limit(1)
        )
        return result.first() is not None

    async def delete_posts_for_today_by_user(self, telegram_user_id: int) -> None:
        await self.session.execute(delete(Post).where(Post.date_of_analysis == date.today()).where(Post.analysed_for_user_id == telegram_user_id))

    async def has_ranked_analysis_for_today(self, telegram_user_id: int) -> bool:
        result = await self.session.execute(
            select(Post.post_id)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.rank_position.is_not(None))
            .limit(1)
        )
        return result.first() is not None

    async def has_classified_analysis_for_today(self, telegram_user_id: int) -> bool:
        top_safe_rank = self._top_safe_rank_subquery(telegram_user_id)
        result = await self.session.execute(
            select(Post.post_id)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.unsafe.is_(False))
            .where(Post.rank_position == top_safe_rank)
            .where(Post.primary_category.is_not(None))
            .limit(1)
        )
        return result.first() is not None

    async def has_reply_context_for_today(self, telegram_user_id: int) -> bool:
        top_safe_rank = self._top_safe_rank_subquery(telegram_user_id)
        result = await self.session.execute(
            select(Post.post_id)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.unsafe.is_(False))
            .where(Post.rank_position == top_safe_rank)
            .where(Post.reply_context.is_not(None))
            .limit(1)
        )
        return result.first() is not None

    async def has_research_for_today(self, telegram_user_id: int) -> bool:
        top_safe_rank = self._top_safe_rank_subquery(telegram_user_id)
        result = await self.session.execute(
            select(Post.post_id)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.unsafe.is_(False))
            .where(Post.rank_position == top_safe_rank)
            .where(Post.purpose.is_not(None))
            .limit(1)
        )
        return result.first() is not None

    async def candidate_posts_for_today(self, telegram_user_id: int, limit: int = ANALYSIS_TOP_RANKED_LIMIT) -> list[Post]:
        stmt: Select[tuple[Post]] = (
            select(Post)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def top_ranked_posts(self, telegram_user_id: int, limit: int = ANALYSIS_TOP_RANKED_LIMIT) -> list[Post]:
        stmt: Select[tuple[Post]] = (
            select(Post)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.rank_position.is_not(None))
            .order_by(Post.rank_position.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def top_safe_ranked_posts(self, telegram_user_id: int, limit: int = ANALYSIS_REPLY_TARGET_LIMIT) -> list[Post]:
        stmt: Select[tuple[Post]] = (
            select(Post)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.rank_position.is_not(None))
            .where(Post.unsafe.is_(False))
            .order_by(Post.rank_position.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def best_researched_post_for_creator(
        self,
        telegram_user_id: int,
        purpose: PostPurpose,
    ) -> Post | None:
        result = await self.session.execute(
            self._creator_source_post_stmt(telegram_user_id, purpose)
        )
        return result.scalar_one_or_none()

    async def recent_own_posts_for_creator_style(
        self,
        telegram_user_id: int,
        limit: int = CREATOR_STYLE_EXAMPLE_LIMIT,
    ) -> list[Post]:
        result = await self.session.execute(
            self._creator_style_examples_stmt(
                telegram_user_id,
                CREATOR_STYLE_EXAMPLE_FETCH_LIMIT,
            )
        )
        posts = result.scalars().all()
        return [post for post in posts if self._is_usable_style_example(post)][:limit]

    async def set_rank(self, post_id: str, rank_position: int, rating_score: Decimal) -> None:
        post = await self.get_post(post_id)
        if post is None:
            return
        post.rank_position = rank_position
        post.rating_score = rating_score
        await self.session.flush()

    async def apply_classification(self, post_id: str, values: dict) -> None:
        post = await self.get_post(post_id)
        if post is None:
            return
        post.primary_category = values["primary_category"]
        post.categories = values["categories"]
        post.unsafe = values["unsafe"]
        await self.session.flush()

    async def update_reply_context(self, post_id: str, reply_context: list[dict]) -> None:
        post = await self.get_post(post_id)
        if post is None:
            return
        post.reply_context = reply_context
        await self.session.flush()

    async def bulk_update_reply_context(self, rows: list[dict]) -> None:
        if not rows:
            return
        await self.session.execute(update(Post), rows)

    async def update_related_sources(self, post_id: str, related_sources: list[dict]) -> None:
        post = await self.get_post(post_id)
        if post is None:
            return
        post.related_sources = related_sources
        await self.session.flush()

    async def bulk_update_research_fields(self, rows: list[dict]) -> None:
        if not rows:
            return
        await self.session.execute(update(Post), rows)

    async def _normalized_rows(self, rows: list[dict]) -> list[dict]:
        deduped_rows: dict[str, dict] = {}
        existing_posts = await self.get_posts(
            [row["post_id"] for row in rows if row.get("post_id")]
        )
        for row in rows:
            post_id = row.get("post_id")
            if not post_id:
                continue
            merged_row = dict(row)
            source_query = self._merge_source_queries(
                deduped_rows.get(post_id, {}).get("source_query"),
                merged_row.get("source_query"),
            )
            source_query = self._merge_source_queries(
                existing_posts.get(post_id).source_query if post_id in existing_posts else None,
                source_query,
            )
            merged_row["source_query"] = source_query
            deduped_rows[post_id] = merged_row
        return list(deduped_rows.values())

    @staticmethod
    def _top_safe_rank_subquery(telegram_user_id: int):
        return (
            select(Post.rank_position)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.rank_position.is_not(None))
            .where(Post.unsafe.is_(False))
            .order_by(Post.rank_position.asc())
            .limit(1)
            .scalar_subquery()
        )

    @staticmethod
    def _creator_source_post_stmt(
        telegram_user_id: int,
        purpose: PostPurpose,
    ) -> Select[tuple[Post]]:
        return (
            select(Post)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.date_of_analysis == date.today())
            .where(Post.own_posts.is_(False))
            .where(Post.rank_position.is_not(None))
            .where(Post.unsafe.is_(False))
            .where(Post.purpose == purpose.value)
            .order_by(Post.rank_position.asc())
            .limit(1)
        )

    @staticmethod
    def _creator_style_examples_stmt(
        telegram_user_id: int,
        limit: int,
    ) -> Select[tuple[Post]]:
        return (
            select(Post)
            .where(Post.analysed_for_user_id == telegram_user_id)
            .where(Post.own_posts.is_(True))
            .where(Post.posted_at.is_not(None))
            .where(Post.text.is_not(None))
            .order_by(Post.posted_at.desc())
            .limit(limit)
        )

    @staticmethod
    def _is_usable_style_example(post: Post) -> bool:
        text = (post.text or "").strip()
        if len(text) < CREATOR_STYLE_MIN_TEXT_LENGTH:
            return False
        return not text.startswith(CREATOR_STYLE_EXCLUDED_PREFIXES)

    @staticmethod
    def _merge_source_queries(
        existing_queries: list[str] | None,
        new_queries: list[str] | None,
    ) -> list[str]:
        merged: list[str] = []
        for value in (existing_queries or []) + (new_queries or []):
            if value and value not in merged:
                merged.append(value)
        return merged
