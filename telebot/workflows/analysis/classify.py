from agno.media import Image
from agno.workflow.step import StepInput, StepOutput
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.agents.schemas import PostClassificationBatch
from telebot.common.constants import (
    ALLOWED_URL_PREFIXES,
    CLASSIFICATION_MEDIA_PER_POST_LIMIT,
    CLASSIFICATION_TARGET_LIMIT,
)
from telebot.common.enums import PostCategory
from telebot.common.messages import TEXT_ANALYSIS_EMPTY_RESULT
from telebot.db.repositories.posts import PostRepository
from telebot.workflows.analysis.common import AnalysisContext, report_progress


class ClassifyTopPostsExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agno_factory: AgnoFactory,
    ) -> None:
        self.session_factory = session_factory
        self.agno_factory = agno_factory

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context: AnalysisContext = step_input.additional_data["context"]
        async with self.session_factory() as session:
            repo = PostRepository(session)
            if await repo.has_classified_analysis_for_today(context.telegram_user_id):
                return StepOutput(content="classifying_skipped")
        await report_progress(context, "classifying")
        async with self.session_factory() as session:
            repo = PostRepository(session)
            posts = await repo.top_ranked_posts(
                context.telegram_user_id,
                limit=CLASSIFICATION_TARGET_LIMIT,
            )
            if not posts:
                raise RuntimeError(TEXT_ANALYSIS_EMPTY_RESULT)
            batch = await self._classify(posts)
            for item in batch.classifications:
                await repo.apply_classification(
                    item.post_id,
                    {
                        "primary_category": item.primary_category.value,
                        "categories": [category.value for category in item.categories],
                        "unsafe": item.unsafe,
                    },
                )
            await session.commit()
        return StepOutput(content="classifying")

    async def _classify(self, posts: list[object]) -> PostClassificationBatch:
        classifier = self.agno_factory.build_post_classifier()
        prompt, images = self._build_prompt_and_images(posts)
        response = await classifier.arun(prompt, images=images)
        return PostClassificationBatch.model_validate(self._content_of(response))

    @staticmethod
    def _build_prompt_and_images(posts: list[object]) -> tuple[str, list[Image]]:
        allowed_categories = ", ".join(category.value for category in PostCategory)
        lines = [
            f"Allowed categories: {allowed_categories}",
            "Posts:",
            (
                "Attached images are included in the same order as each post's image_refs. "
                "Use the images, not just their URLs, when available."
            ),
        ]
        images: list[Image] = []
        for post in posts:
            image_refs = []
            for media_url in (post.media_urls or [])[:CLASSIFICATION_MEDIA_PER_POST_LIMIT]:
                if not isinstance(media_url, str) or not media_url.startswith(ALLOWED_URL_PREFIXES):
                    continue
                image_refs.append(media_url)
                images.append(Image(url=media_url))
            lines.append(
                "\n".join(
                    [
                        f"post_id: {post.post_id}",
                        f"text: {post.text or ''}",
                        f"image_refs: {', '.join(image_refs) or 'none'}",
                    ]
                )
            )
        return "\n\n".join(lines), images

    @staticmethod
    def _content_of(response):
        return getattr(response, "content", response)
