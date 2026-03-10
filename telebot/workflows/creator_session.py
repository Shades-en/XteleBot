from __future__ import annotations

from dataclasses import dataclass, replace

from telebot.common.constants import CREATOR_ALTERNATIVE_WINDOW_SIZE
from telebot.common.enums import CommandName, PostPurpose


@dataclass(frozen=True)
class CreatorSessionState:
    command: CommandName
    purpose: PostPurpose
    candidate_post_ids: list[str]
    selected_source_post_id: str
    selection_window_start: int = 0
    awaiting_source_selection: bool = False
    draft_message_id: int | None = None

    @classmethod
    def from_dict(cls, value: dict | None) -> "CreatorSessionState | None":
        if not isinstance(value, dict):
            return None
        try:
            command = CommandName(str(value["command"]))
            purpose = PostPurpose(str(value["purpose"]))
            candidate_post_ids = [str(item) for item in value.get("candidate_post_ids", []) if item]
            selected_source_post_id = str(value["selected_source_post_id"])
        except (KeyError, ValueError, TypeError):
            return None
        if not candidate_post_ids or selected_source_post_id not in candidate_post_ids:
            return None
        draft_message_id = value.get("draft_message_id")
        if not isinstance(draft_message_id, int):
            draft_message_id = None
        return cls(
            command=command,
            purpose=purpose,
            candidate_post_ids=candidate_post_ids,
            selected_source_post_id=selected_source_post_id,
            selection_window_start=int(value.get("selection_window_start", 0) or 0),
            awaiting_source_selection=bool(value.get("awaiting_source_selection", False)),
            draft_message_id=draft_message_id,
        )

    def to_dict(self) -> dict:
        return {
            "command": self.command.value,
            "purpose": self.purpose.value,
            "candidate_post_ids": self.candidate_post_ids,
            "selected_source_post_id": self.selected_source_post_id,
            "selection_window_start": self.selection_window_start,
            "awaiting_source_selection": self.awaiting_source_selection,
            "draft_message_id": self.draft_message_id,
        }

    def with_draft_message_id(self, message_id: int) -> "CreatorSessionState":
        return replace(self, draft_message_id=message_id)

    def with_selected_source_post_id(self, post_id: str) -> "CreatorSessionState":
        return replace(
            self,
            selected_source_post_id=post_id,
            selection_window_start=0,
            awaiting_source_selection=False,
        )

    def initial_candidate_window(
        self,
        window_size: int = CREATOR_ALTERNATIVE_WINDOW_SIZE,
    ) -> tuple[list[str], "CreatorSessionState"]:
        window = self.candidate_post_ids[:window_size]
        return window, replace(
            self,
            selection_window_start=0,
            awaiting_source_selection=True,
            draft_message_id=None,
        )

    def next_alternative_window(
        self,
        window_size: int = CREATOR_ALTERNATIVE_WINDOW_SIZE,
    ) -> tuple[list[str], "CreatorSessionState"]:
        alternative_ids = self._alternative_ids()
        if not alternative_ids:
            return [], self
        start = 0
        if self.awaiting_source_selection:
            start = (self.selection_window_start + window_size) % len(alternative_ids)
        window = alternative_ids[start : start + window_size]
        if len(window) < min(window_size, len(alternative_ids)):
            window.extend(
                alternative_ids[: min(window_size, len(alternative_ids)) - len(window)]
            )
        return window, replace(
            self,
            selection_window_start=start,
            awaiting_source_selection=True,
        )

    def next_candidate_window(
        self,
        window_size: int = CREATOR_ALTERNATIVE_WINDOW_SIZE,
    ) -> tuple[list[str], "CreatorSessionState"]:
        if not self.candidate_post_ids:
            return [], self
        start = (self.selection_window_start + window_size) % len(self.candidate_post_ids)
        window = self.candidate_post_ids[start : start + window_size]
        if len(window) < min(window_size, len(self.candidate_post_ids)):
            window.extend(
                self.candidate_post_ids[
                    : min(window_size, len(self.candidate_post_ids)) - len(window)
                ]
            )
        return window, replace(
            self,
            selection_window_start=start,
            awaiting_source_selection=True,
            draft_message_id=None,
        )

    def has_more_alternatives(
        self,
        window_size: int = CREATOR_ALTERNATIVE_WINDOW_SIZE,
    ) -> bool:
        return len(self._alternative_ids()) > window_size

    def has_more_candidates(
        self,
        window_size: int = CREATOR_ALTERNATIVE_WINDOW_SIZE,
    ) -> bool:
        return len(self.candidate_post_ids) > window_size

    def _alternative_ids(self) -> list[str]:
        if len(self.candidate_post_ids) <= 1:
            return []
        current_index = self.candidate_post_ids.index(self.selected_source_post_id)
        return (
            self.candidate_post_ids[current_index + 1 :]
            + self.candidate_post_ids[:current_index]
        )


def initial_creator_session_state(
    command: CommandName,
    purpose: PostPurpose,
    candidate_post_ids: list[str],
) -> CreatorSessionState:
    if not candidate_post_ids:
        raise ValueError("candidate_post_ids must not be empty")
    return CreatorSessionState(
        command=command,
        purpose=purpose,
        candidate_post_ids=candidate_post_ids,
        selected_source_post_id=candidate_post_ids[0],
    )
