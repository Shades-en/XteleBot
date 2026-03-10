import unittest

from telebot.common.enums import CommandName, PostPurpose
from telebot.workflows.creator_session import (
    CreatorSessionState,
    initial_creator_session_state,
)


class CreatorSessionStateTests(unittest.TestCase):
    def test_initial_state_selects_top_candidate(self) -> None:
        state = initial_creator_session_state(
            CommandName.POST_BY_INSPIRATION,
            PostPurpose.POST,
            ["p1", "p2", "p3"],
        )

        self.assertEqual(state.selected_source_post_id, "p1")
        self.assertFalse(state.awaiting_source_selection)

    def test_next_alternative_window_excludes_current_and_wraps(self) -> None:
        state = CreatorSessionState(
            command=CommandName.QUOTE,
            purpose=PostPurpose.QUOTE,
            candidate_post_ids=["a", "b", "c", "d"],
            selected_source_post_id="c",
        )

        window, next_state = state.next_alternative_window()

        self.assertEqual(window, ["d", "a", "b"])
        self.assertTrue(next_state.awaiting_source_selection)

    def test_selecting_candidate_resets_window_state(self) -> None:
        state = CreatorSessionState(
            command=CommandName.COMMENT,
            purpose=PostPurpose.COMMENT,
            candidate_post_ids=["a", "b", "c"],
            selected_source_post_id="a",
            selection_window_start=1,
            awaiting_source_selection=True,
        )

        next_state = state.with_selected_source_post_id("c")

        self.assertEqual(next_state.selected_source_post_id, "c")
        self.assertEqual(next_state.selection_window_start, 0)
        self.assertFalse(next_state.awaiting_source_selection)

    def test_round_trip_dict(self) -> None:
        state = CreatorSessionState(
            command=CommandName.POST_BY_INSPIRATION,
            purpose=PostPurpose.POST,
            candidate_post_ids=["p1", "p2"],
            selected_source_post_id="p1",
            draft_message_id=42,
        )

        restored = CreatorSessionState.from_dict(state.to_dict())

        self.assertEqual(restored, state)


if __name__ == "__main__":
    unittest.main()
