from telebot.costs.pricing import (
    BRAVE_REQUEST_COST_USD,
    OPENAI_MODEL_PRICING,
    normalize_openai_model_id,
)
from telebot.costs.schemas import (
    BraveCostBreakdown,
    OpenAICostBreakdown,
    OpenAIModelUsage,
    TwitterCostBreakdown,
    TwitterEndpointUsage,
    WorkflowCostSummary,
)
from telebot.costs.twitter import credits_to_usd, estimate_twitter_credits


class WorkflowCostTracker:
    def __init__(self) -> None:
        self.openai_models: dict[str, OpenAIModelUsage] = {}
        self.openai_unknown_models: dict[str, OpenAIModelUsage] = {}
        self.brave_request_count = 0
        self.twitter_endpoints: dict[str, TwitterEndpointUsage] = {}
        self.warnings: set[str] = set()

    def record_openai_model_usage(
        self,
        model_id: str,
        input_tokens: int = 0,
        cached_input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        normalized_model_id = normalize_openai_model_id(model_id)
        usage = OpenAIModelUsage(
            model_id=normalized_model_id,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            total_cost_usd=0.0,
        )
        if normalized_model_id not in OPENAI_MODEL_PRICING:
            self._accumulate_usage(self.openai_unknown_models, usage)
            self.warnings.add(
                f"Unknown OpenAI model pricing for {normalized_model_id}. OpenAI total is partial."
            )
            return
        pricing = OPENAI_MODEL_PRICING[normalized_model_id]
        uncached_input_tokens = max(0, input_tokens - cached_input_tokens)
        usage.total_cost_usd = (
            (uncached_input_tokens / 1_000_000) * pricing.input_per_million
            + (cached_input_tokens / 1_000_000) * pricing.cached_input_per_million
            + (output_tokens / 1_000_000) * pricing.output_per_million
        )
        self._accumulate_usage(self.openai_models, usage)

    def record_brave_request(self, request_count: int = 1) -> None:
        self.brave_request_count += request_count

    def record_twitter_call(self, endpoint: str, returned_count: int) -> None:
        credits = estimate_twitter_credits(endpoint, returned_count)
        usage = self.twitter_endpoints.get(endpoint)
        if usage is None:
            usage = TwitterEndpointUsage()
            self.twitter_endpoints[endpoint] = usage
        usage.calls += 1
        usage.returned_count += returned_count
        usage.credits += credits
        usage.total_cost_usd += credits_to_usd(credits)

    def summary(self) -> WorkflowCostSummary:
        openai_total = sum(item.total_cost_usd for item in self.openai_models.values())
        brave_total = self.brave_request_count * BRAVE_REQUEST_COST_USD
        twitter_total = sum(item.total_cost_usd for item in self.twitter_endpoints.values())
        return WorkflowCostSummary(
            total_cost_usd=openai_total + brave_total + twitter_total,
            openai=OpenAICostBreakdown(
                total_cost_usd=openai_total,
                models=self.openai_models,
                unknown_models=self.openai_unknown_models,
            ),
            brave=BraveCostBreakdown(
                request_count=self.brave_request_count,
                total_cost_usd=brave_total,
            ),
            twitter=TwitterCostBreakdown(
                total_credits=sum(item.credits for item in self.twitter_endpoints.values()),
                total_cost_usd=twitter_total,
                endpoints=self.twitter_endpoints,
            ),
            warnings=sorted(self.warnings),
        )

    @staticmethod
    def _accumulate_usage(target: dict[str, OpenAIModelUsage], usage: OpenAIModelUsage) -> None:
        existing = target.get(usage.model_id)
        if existing is None:
            target[usage.model_id] = usage
            return
        existing.input_tokens += usage.input_tokens
        existing.cached_input_tokens += usage.cached_input_tokens
        existing.output_tokens += usage.output_tokens
        existing.total_cost_usd += usage.total_cost_usd
