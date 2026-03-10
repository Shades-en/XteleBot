from pydantic import BaseModel, Field, field_validator, model_validator

from telebot.common.constants import PURPOSE_SCORE_MAX, PURPOSE_SCORE_MIN
from telebot.common.enums import AgentSentiment, PostCategory, PostPurpose
from telebot.db.schemas import SourceEvidenceItem


class PostClassification(BaseModel):
    post_id: str
    primary_category: PostCategory
    categories: list[PostCategory]
    unsafe: bool

    @field_validator("categories")
    @classmethod
    def categories_must_not_be_empty(cls, value: list[PostCategory]) -> list[PostCategory]:
        if not value:
            raise ValueError("categories must contain at least one category")
        return value

    @model_validator(mode="after")
    def primary_must_be_present(self) -> "PostClassification":
        if self.primary_category not in self.categories:
            self.categories = [self.primary_category, *self.categories]
        return self


class PostClassificationBatch(BaseModel):
    classifications: list[PostClassification]


class PurposeScores(BaseModel):
    post: float
    quote: float
    comment: float

    @field_validator("post", "quote", "comment")
    @classmethod
    def score_must_be_bounded(cls, value: float) -> float:
        if value < PURPOSE_SCORE_MIN or value > PURPOSE_SCORE_MAX:
            raise ValueError(
                f"purpose scores must be between {PURPOSE_SCORE_MIN} and {PURPOSE_SCORE_MAX}"
            )
        return value

    def for_purpose(self, purpose: PostPurpose) -> float:
        if purpose == PostPurpose.POST:
            return self.post
        if purpose == PostPurpose.QUOTE:
            return self.quote
        return self.comment


class ResearchTweetSynthesisResult(BaseModel):
    related_sources: list[SourceEvidenceItem] = Field(default_factory=list)
    agent_sentiment: list[AgentSentiment] = Field(default_factory=list)
    agent_comments: str
    purpose: PostPurpose
    purpose_rationale: str
    purpose_scores: PurposeScores
    evidence_sufficient: bool = True
    retry_guidance: str = ""

    @model_validator(mode="after")
    def ensure_sentiment_present(self) -> "ResearchTweetSynthesisResult":
        if not self.agent_sentiment:
            self.agent_sentiment = [AgentSentiment.OTHER]
        return self
