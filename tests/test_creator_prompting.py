import unittest

from telebot.common.enums import CommandName
from telebot.prompts.creator import (
    CREATOR_COMMENT_SPEC,
    CREATOR_POST_SPEC,
    CREATOR_QUOTE_SPEC,
)
from telebot.workflows.creator_prompting import build_creator_prompt
from telebot.workflows.creator_types import (
    CreatorContext,
    CreatorSourcePost,
    CreatorStyleExample,
)


def sample_context(command: CommandName) -> CreatorContext:
    return CreatorContext(
        command=command,
        source_post=CreatorSourcePost(
            post_id="post-1",
            source_url="https://x.com/example/status/1",
            text="Nvidia may be opening up an agent stack.",
            purpose=command.value,
            media_urls=["https://example.com/image.png"],
            reply_context=[{"rank_position": 1, "author_username": "alice", "text": "Big if true"}],
            agent_sentiment=["Curious"],
            agent_comments="Lean into the builder implication instead of sounding like a reporter.",
            related_sources=[
                {
                    "title": "Example Source",
                    "source_date": "2026-03-10",
                    "url": "https://example.com/story",
                    "content_excerpt": "A grounded excerpt about the product direction.",
                }
            ],
        ),
        style_examples=[
            CreatorStyleExample(
                post_id="own-1",
                posted_at="2026-03-09T10:00:00",
                text="Most software gets better when the workflow is simpler, not smarter.",
            )
        ],
        refinement="Make it feel more like a founder with product taste.",
    )


class CreatorPromptingTests(unittest.TestCase):
    def test_post_prompt_uses_only_post_spec(self) -> None:
        prompt = build_creator_prompt(sample_context(CommandName.POST_BY_INSPIRATION))
        self.assertIn(CREATOR_POST_SPEC, prompt)
        self.assertNotIn(CREATOR_QUOTE_SPEC, prompt)
        self.assertNotIn(CREATOR_COMMENT_SPEC, prompt)

    def test_quote_prompt_uses_only_quote_spec(self) -> None:
        prompt = build_creator_prompt(sample_context(CommandName.QUOTE))
        self.assertIn(CREATOR_QUOTE_SPEC, prompt)
        self.assertNotIn(CREATOR_POST_SPEC, prompt)
        self.assertNotIn(CREATOR_COMMENT_SPEC, prompt)

    def test_comment_prompt_uses_only_comment_spec(self) -> None:
        prompt = build_creator_prompt(sample_context(CommandName.COMMENT))
        self.assertIn(CREATOR_COMMENT_SPEC, prompt)
        self.assertNotIn(CREATOR_POST_SPEC, prompt)
        self.assertNotIn(CREATOR_QUOTE_SPEC, prompt)
        self.assertIn("1 to 3 sentences", prompt)

    def test_prompt_includes_style_examples_and_refinement(self) -> None:
        prompt = build_creator_prompt(sample_context(CommandName.POST_BY_INSPIRATION))
        self.assertIn("Style examples from the user's own posts:", prompt)
        self.assertIn("Most software gets better", prompt)
        self.assertIn("Make it feel more like a founder", prompt)
        self.assertIn("source_post_media_refs: https://example.com/image.png", prompt)


if __name__ == "__main__":
    unittest.main()
