from telebot.common.constants import WEB_RESEARCH_MAX_TASKS

from pydantic import BaseModel, Field, field_validator


class SearchTask(BaseModel):
    query: str = Field(..., description="Web search query")
    rationale: str = Field(..., description="Why this query is useful")


class PostResearchPlan(BaseModel):
    needs_search: bool
    queries: list[SearchTask] = Field(default_factory=list)
    reason: str = ""
    claims_to_verify: list[str] = Field(default_factory=list)
    freshness_required: bool = False

    @field_validator("queries")
    @classmethod
    def cap_queries(cls, value: list[SearchTask]) -> list[SearchTask]:
        return value[:WEB_RESEARCH_MAX_TASKS]

    @classmethod
    def fallback(cls, reason: str) -> "PostResearchPlan":
        return cls(needs_search=False, reason=reason)


class SearchCandidate(BaseModel):
    url: str
    original_search_queries: list[str] = Field(default_factory=list)
    title: str | None = None
    source_date: str | None = None
    source_type: str
    content_excerpts: list[str] = Field(default_factory=list)


class EvidenceChunk(BaseModel):
    url: str
    original_search_queries: list[str] = Field(default_factory=list)
    title: str | None = None
    source_date: str | None = None
    content_excerpts: list[str] = Field(default_factory=list)
    source_type: str
    similarity_scores: list[float] = Field(default_factory=list)


class WebSearchWorkflowResult(BaseModel):
    plan: PostResearchPlan
    evidence: list[EvidenceChunk] = Field(default_factory=list)

    @classmethod
    def fallback(cls, reason: str) -> "WebSearchWorkflowResult":
        return cls(plan=PostResearchPlan.fallback(reason), evidence=[])
