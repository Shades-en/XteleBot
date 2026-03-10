import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telebot.common.enums import CommandName, PostPurpose
from telebot.costs.tracker import WorkflowCostTracker
from telebot.workflows.creator_generation import run_creator_draft
from telebot.workflows.creator_session import initial_creator_session_state


class FakeAgentResponse:
    def __init__(self, content: str) -> None:
        self.content = content
        self.metrics = None


class FakeAgent:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    async def arun(self, prompt: str, user_id: str, session_id: str, images: list[object]):
        self.calls.append(
            {
                "prompt": prompt,
                "user_id": user_id,
                "session_id": session_id,
                "images": images,
            }
        )
        return FakeAgentResponse(self.responses.pop(0))


class FakeAgnoFactory:
    def __init__(self, creator_responses: list[str], refiner_responses: list[str]) -> None:
        self.creator_agent = FakeAgent(creator_responses)
        self.refiner_agent = FakeAgent(refiner_responses)

    def build_creator_agent(self) -> FakeAgent:
        return self.creator_agent

    def build_creator_refiner_agent(self) -> FakeAgent:
        return self.refiner_agent


def sample_post() -> SimpleNamespace:
    return SimpleNamespace(
        post_id="post-1",
        post_url="https://x.com/example/status/1",
        text="Nvidia may be opening up an agent stack.",
        purpose=PostPurpose.POST.value,
        media_urls=["https://example.com/image.png"],
        reply_context=[{"rank_position": 1, "author_username": "alice", "text": "Big if true"}],
        agent_sentiment=["Curious"],
        agent_comments="Lean into the builder implication.",
        related_sources=[
            {"url": "https://example.com/story-1"},
            {"url": "https://example.com/story-2"},
            {"url": "https://example.com/story-1"},
        ],
    )


class CreatorGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_creator_draft_always_refines_and_returns_source_separately(self) -> None:
        factory = FakeAgnoFactory(
            creator_responses=["Initial draft with ; punctuation"],
            refiner_responses=["Refined draft with cleaner flow"],
        )
        state = initial_creator_session_state(
            CommandName.POST_BY_INSPIRATION,
            PostPurpose.POST,
            ["post-1"],
        )
        with (
            patch("telebot.workflows.creator_generation.load_post_by_id", AsyncMock(return_value=sample_post())),
            patch("telebot.workflows.creator_generation.load_creator_style_examples", AsyncMock(return_value=[])),
            patch("telebot.workflows.creator_generation.complete_creator_job", AsyncMock()),
            patch("telebot.workflows.creator_generation.fail_creator_job", AsyncMock()),
        ):
            result = await run_creator_draft(
                session_factory=None,
                agno_factory=factory,
                telegram_user_id=101,
                session_id="session_1",
                state=state,
                job_id="job_1",
                cost_tracker=WorkflowCostTracker(),
            )

        self.assertEqual(result.body, "Refined draft with cleaner flow")
        self.assertEqual(result.source_url, "https://x.com/example/status/1")
        self.assertEqual(
            result.related_source_urls,
            ["https://example.com/story-1", "https://example.com/story-2"],
        )
        self.assertEqual(len(factory.creator_agent.calls), 1)
        self.assertEqual(len(factory.refiner_agent.calls), 1)
        self.assertEqual(factory.refiner_agent.calls[0]["session_id"], "session_1:refiner")

    async def test_run_creator_draft_passes_validation_feedback_to_refiner(self) -> None:
        factory = FakeAgnoFactory(
            creator_responses=["x" * 610 + " — bad;"],
            refiner_responses=["Cleaner version"],
        )
        state = initial_creator_session_state(
            CommandName.POST_BY_INSPIRATION,
            PostPurpose.POST,
            ["post-1"],
        )
        with (
            patch("telebot.workflows.creator_generation.load_post_by_id", AsyncMock(return_value=sample_post())),
            patch("telebot.workflows.creator_generation.load_creator_style_examples", AsyncMock(return_value=[])),
            patch("telebot.workflows.creator_generation.complete_creator_job", AsyncMock()),
            patch("telebot.workflows.creator_generation.fail_creator_job", AsyncMock()),
        ):
            await run_creator_draft(
                session_factory=None,
                agno_factory=factory,
                telegram_user_id=101,
                session_id="session_1",
                state=state,
                job_id="job_1",
            )

        prompt = factory.refiner_agent.calls[0]["prompt"]
        self.assertIn("Body exceeds 600 characters.", prompt)
        self.assertIn("Body contains banned punctuation: —", prompt)
        self.assertIn("Body contains banned punctuation: ;", prompt)

    async def test_run_creator_draft_without_issues_still_calls_refiner(self) -> None:
        factory = FakeAgnoFactory(
            creator_responses=["Short clean draft"],
            refiner_responses=["Short clean draft"],
        )
        state = initial_creator_session_state(
            CommandName.COMMENT,
            PostPurpose.COMMENT,
            ["post-1"],
        )
        with (
            patch("telebot.workflows.creator_generation.load_post_by_id", AsyncMock(return_value=sample_post())),
            patch("telebot.workflows.creator_generation.load_creator_style_examples", AsyncMock(return_value=[])),
            patch("telebot.workflows.creator_generation.complete_creator_job", AsyncMock()),
            patch("telebot.workflows.creator_generation.fail_creator_job", AsyncMock()),
        ):
            result = await run_creator_draft(
                session_factory=None,
                agno_factory=factory,
                telegram_user_id=101,
                session_id="session_1",
                state=state,
                job_id="job_1",
            )

        self.assertEqual(result.body, "Short clean draft")
        self.assertNotIn("Deterministic validation feedback:", factory.refiner_agent.calls[0]["prompt"])
        self.assertEqual(len(factory.refiner_agent.calls), 1)


if __name__ == "__main__":
    unittest.main()
