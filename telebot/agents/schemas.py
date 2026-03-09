from pydantic import BaseModel, Field, field_validator, model_validator

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


class ResearchTweetSynthesisResult(BaseModel):
    related_sources: list[SourceEvidenceItem] = Field(default_factory=list)
    agent_sentiment: list[AgentSentiment] = Field(default_factory=list)
    agent_comments: str
    purpose: PostPurpose
    evidence_sufficient: bool = True
    retry_guidance: str = ""

    @model_validator(mode="after")
    def ensure_sentiment_present(self) -> "ResearchTweetSynthesisResult":
        if not self.agent_sentiment:
            self.agent_sentiment = [AgentSentiment.OTHER]
        return self
