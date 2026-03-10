from pydantic import BaseModel, Field


class OpenAIModelUsage(BaseModel):
    model_id: str
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: float = 0.0


class OpenAICostBreakdown(BaseModel):
    total_cost_usd: float = 0.0
    models: dict[str, OpenAIModelUsage] = Field(default_factory=dict)
    unknown_models: dict[str, OpenAIModelUsage] = Field(default_factory=dict)


class BraveCostBreakdown(BaseModel):
    request_count: int = 0
    total_cost_usd: float = 0.0


class TwitterEndpointUsage(BaseModel):
    calls: int = 0
    returned_count: int = 0
    credits: int = 0
    total_cost_usd: float = 0.0


class TwitterCostBreakdown(BaseModel):
    total_credits: int = 0
    total_cost_usd: float = 0.0
    endpoints: dict[str, TwitterEndpointUsage] = Field(default_factory=dict)
    approximate: bool = True


class WorkflowCostSummary(BaseModel):
    total_cost_usd: float = 0.0
    openai: OpenAICostBreakdown = Field(default_factory=OpenAICostBreakdown)
    brave: BraveCostBreakdown = Field(default_factory=BraveCostBreakdown)
    twitter: TwitterCostBreakdown = Field(default_factory=TwitterCostBreakdown)
    warnings: list[str] = Field(default_factory=list)
