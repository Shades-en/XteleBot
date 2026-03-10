from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.learn import LearningMachine, LearningMode, SessionContextConfig, UserMemoryConfig, UserProfileConfig
from agno.models.openai import OpenAIResponses

from telebot.agents.schemas import PostClassificationBatch, ResearchTweetSynthesisResult
from telebot.common.constants import (
    AGNO_TOOL_CALL_LIMIT,
    OPENAI_CHAT_MODEL,
    PLANNER_NAME,
)
from telebot.config import Settings
from telebot.prompts.classification import CLASSIFICATION_SYSTEM_PROMPT
from telebot.prompts.creator import CREATOR_SYSTEM_PROMPT
from telebot.prompts.research import (
    RESEARCH_PLANNER_PROMPT,
    RESEARCH_SYNTHESIS_AGENT_PROMPT,
)
from telebot.search.schemas import PostResearchPlan


class AgnoFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = AsyncPostgresDb(db_url=settings.agno_postgres_url)

    def _model(self) -> OpenAIResponses:
        return OpenAIResponses(id=OPENAI_CHAT_MODEL)

    def _learning(self) -> LearningMachine:
        return LearningMachine(
            user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
            user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
            session_context=SessionContextConfig(enable_planning=True),
        )

    def build_creator_agent(self) -> Agent:
        return Agent(
            name="Content Creator",
            model=self._model(),
            db=self.db,
            learning=self._learning(),
            instructions=[CREATOR_SYSTEM_PROMPT],
            add_history_to_context=True,
            num_history_runs=4,
            markdown=True,
            tool_call_limit=AGNO_TOOL_CALL_LIMIT,
        )

    def build_search_planner(self) -> Agent:
        return Agent(
            name=PLANNER_NAME,
            model=self._model(),
            instructions=[RESEARCH_PLANNER_PROMPT],
            output_schema=PostResearchPlan,
            markdown=True,
        )

    def build_post_classifier(self) -> Agent:
        return Agent(
            name="Post Classifier",
            model=self._model(),
            db=self.db,
            output_schema=PostClassificationBatch,
            instructions=[CLASSIFICATION_SYSTEM_PROMPT],
            markdown=True,
            tool_call_limit=AGNO_TOOL_CALL_LIMIT,
        )

    def build_research_synthesis_agent(self) -> Agent:
        return Agent(
            name="Research Synthesizer",
            model=self._model(),
            output_schema=ResearchTweetSynthesisResult,
            instructions=[RESEARCH_SYNTHESIS_AGENT_PROMPT],
            markdown=True,
            add_datetime_to_context=True,
            timezone_identifier="Etc/UTC"
        )
