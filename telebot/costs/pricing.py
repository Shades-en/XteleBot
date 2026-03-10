from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIModelPricing:
    input_per_million: float
    cached_input_per_million: float
    output_per_million: float


OPENAI_MODEL_PRICING = {
    "gpt-5-mini": OpenAIModelPricing(0.25, 0.025, 2.00),
    "gpt-5.2": OpenAIModelPricing(1.75, 0.175, 14.00),
    "gpt-4.1": OpenAIModelPricing(2.00, 0.50, 8.00),
    "text-embedding-3-small": OpenAIModelPricing(0.02, 0.0, 0.0),
}

OPENAI_MODEL_PREFIXES = tuple(OPENAI_MODEL_PRICING.keys())
BRAVE_REQUEST_COST_USD = 5.0 / 1000.0
TWITTER_CREDITS_PER_USD = 100000
TWITTER_MIN_CALL_CREDITS = 15
TWITTER_TWEET_RESULT_CREDITS = 15
TWITTER_PROFILE_RESULT_CREDITS = 18


def normalize_openai_model_id(model_id: str) -> str:
    raw = model_id.strip()
    for prefix in OPENAI_MODEL_PREFIXES:
        if raw == prefix or raw.startswith(f"{prefix}-"):
            return prefix
    return raw
