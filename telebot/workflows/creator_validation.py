from telebot.common.constants import (
    CREATOR_BANNED_PUNCTUATION,
    CREATOR_COMMENT_MAX_CHARS,
    CREATOR_POST_MAX_CHARS,
    CREATOR_QUOTE_MAX_CHARS,
)
from telebot.common.enums import CommandName
from telebot.workflows.creator_types import CreatorValidationResult


def validate_creator_body(command: CommandName, body: str) -> CreatorValidationResult:
    issues: list[str] = []
    normalized = body.strip()
    max_chars = _max_chars(command)
    if len(normalized) > max_chars:
        issues.append(f"Body exceeds {max_chars} characters.")
    for value in CREATOR_BANNED_PUNCTUATION:
        if value in normalized:
            issues.append(f"Body contains banned punctuation: {value}")
    return CreatorValidationResult(issues=issues)


def sanitize_creator_body(body: str) -> str:
    sanitized = body.replace("—", " - ").replace(";", ",")
    sanitized = "\n".join(line.rstrip() for line in sanitized.splitlines())
    sanitized = "\n".join(_collapse_blank_lines(sanitized.splitlines()))
    return sanitized.strip()


def _max_chars(command: CommandName) -> int:
    if command is CommandName.COMMENT:
        return CREATOR_COMMENT_MAX_CHARS
    if command is CommandName.QUOTE:
        return CREATOR_QUOTE_MAX_CHARS
    return CREATOR_POST_MAX_CHARS


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    blank_pending = False
    for line in lines:
        if line.strip():
            collapsed.append(line)
            blank_pending = False
            continue
        if not blank_pending:
            collapsed.append("")
            blank_pending = True
    return collapsed
