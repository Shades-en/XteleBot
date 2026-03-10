from telebot.common.constants import (
    CREATOR_COMMENT_MAX_CHARS,
    CREATOR_PARAGRAPH_MAX_SENTENCES,
    CREATOR_PARAGRAPH_MIN_SENTENCES,
    CREATOR_POST_MAX_CHARS,
    CREATOR_POST_MIN_CHARS,
    CREATOR_QUOTE_MAX_CHARS,
    CREATOR_QUOTE_MIN_CHARS,
    CREATOR_THREAD_STYLE_MAX_PARAGRAPHS,
    CREATOR_THREAD_STYLE_MIN_PARAGRAPHS,
)
from telebot.common.enums import CommandName

CREATOR_SYSTEM_PROMPT = (
    "You write grounded X/Twitter drafts from a structured brief. "
    "Follow the style guide in the task prompt exactly, use the provided source context and style examples, "
    "and return only the requested draft body."
)

CREATOR_REFINER_SYSTEM_PROMPT = (
    "You refine grounded X/Twitter drafts from a structured brief. "
    "Preserve the core idea, follow the style guide in the task prompt exactly, "
    "make the writing sound more natural and less robotic, and return only the refined draft body."
)

_TONE_GUIDELINES = (
    "Sound like a thoughtful engineer or builder sharing an observation.",
    "Slightly opinionated and conversational.",
    "Laid-back and natural. Avoid sounding like marketing or AI-generated text.",
)

_WRITING_RULES = (
    "Use simple everyday language.",
    "Avoid buzzwords, hype, and corporate phrasing.",
    "Do NOT use dashes like -- or —.",
    "Do NOT use semicolons.",
    "Do NOT sound instructional or preachy.",
    "Do NOT give advice unless explicitly asked.",
    "Avoid phrases like \"it's important to\", \"remember to\", and \"make sure to\".",
    "Avoid labels like \"Opinion:\", \"Hot take:\", \"Take:\", or \"Why this matters:\".",
    "Avoid section-heading labels inside the post unless the user explicitly asks for them.",
    "Focus on an observation or shift in technology.",
)

_VOICE_GUIDELINES = (
    "Write as if noticing something interesting about how technology is evolving.",
    "Prefer phrases like \"feels like\", \"what's interesting is\", and \"starting to feel like\" when they fit naturally.",
    "Keep it reflective rather than authoritative.",
    "Sound like someone who builds products and has skin in the game, not a neutral reporter.",
)

_POST_STRUCTURE_LINES = (
    f"{CREATOR_THREAD_STYLE_MIN_PARAGRAPHS} to {CREATOR_THREAD_STYLE_MAX_PARAGRAPHS} short paragraphs.",
    f"Each paragraph should be {CREATOR_PARAGRAPH_MIN_SENTENCES} to {CREATOR_PARAGRAPH_MAX_SENTENCES} sentences.",
    "Leave a blank line between paragraphs.",
    "The post should read like a small thread-style thought, not a list.",
)

_QUOTE_STRUCTURE_LINES = (
    "Use short paragraphs when the idea has enough room.",
    f"Keep each paragraph to {CREATOR_PARAGRAPH_MIN_SENTENCES} to {CREATOR_PARAGRAPH_MAX_SENTENCES} sentences.",
    "Leave a blank line between paragraphs when you use more than one paragraph.",
    "The quote tweet should feel like a compact thread-style thought, not a list or slogan.",
)

_COMMENT_STRUCTURE_LINES = (
    "Keep it to one short paragraph.",
    "Usually make it one short sentence, or two if needed.",
    "Keep it as a quick natural reaction, not a list or mini-essay.",
)

_GOAL_LINES = {
    CommandName.POST_BY_INSPIRATION: (
        "Turn the topic into a thoughtful observation about how technology is changing the "
        "way people work."
    ),
    CommandName.QUOTE: (
        "Turn the source post into a thoughtful observation about how technology is changing "
        "the way people work."
    ),
    CommandName.COMMENT: (
        "Turn the source post into a short thoughtful observation that adds something natural "
        "to the conversation."
    ),
}

_INTRO_LINES = {
    CommandName.POST_BY_INSPIRATION: "You are writing tweets about AI, technology, and product trends.",
    CommandName.QUOTE: "You are writing quote tweets about AI, technology, and product trends.",
    CommandName.COMMENT: "You are writing short replies about AI, technology, and product trends.",
}


def build_creator_style_guide(command: CommandName) -> str:
    return _build_style_guide(command)


def build_creator_refiner_style_guide(command: CommandName) -> str:
    return _build_style_guide(command)


def _build_style_guide(command: CommandName) -> str:
    return "\n\n".join(
        [
            _INTRO_LINES[command],
            "Style guidelines:",
            _bullet_section("Tone", _TONE_GUIDELINES),
            _bullet_section("Structure", _structure_lines(command)),
            _bullet_section("Writing rules", _WRITING_RULES),
            _bullet_section("Voice", _VOICE_GUIDELINES),
            _plain_section("Length", _length_line(command)),
            _plain_section("Goal", _GOAL_LINES[command]),
        ]
    )


def _structure_lines(command: CommandName) -> tuple[str, ...]:
    if command is CommandName.QUOTE:
        return _QUOTE_STRUCTURE_LINES
    if command is CommandName.COMMENT:
        return _COMMENT_STRUCTURE_LINES
    return _POST_STRUCTURE_LINES


def _length_line(command: CommandName) -> str:
    if command is CommandName.QUOTE:
        return f"Around {CREATOR_QUOTE_MIN_CHARS} to {CREATOR_QUOTE_MAX_CHARS} characters total."
    if command is CommandName.COMMENT:
        return f"Under {CREATOR_COMMENT_MAX_CHARS} characters total."
    return f"Around {CREATOR_POST_MIN_CHARS} to {CREATOR_POST_MAX_CHARS} characters total."


def _bullet_section(title: str, items: tuple[str, ...]) -> str:
    return f"{title}:\n\n" + "\n".join(f"* {item}" for item in items)


def _plain_section(title: str, body: str) -> str:
    return f"{title}:\n\n{body}"
