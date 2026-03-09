from telebot.common.constants import UNSAFE_CLASSIFICATION_SIGNALS


CLASSIFICATION_SYSTEM_PROMPT = (
    "Classify ranked X posts into the allowed categories only. "
    "Use the post text and any attached images as context. "
    f"Mark unsafe true only for: {', '.join(UNSAFE_CLASSIFICATION_SIGNALS)}. "
    "AI-related content alone is not unsafe. "
    "Always return structured output only."
)
