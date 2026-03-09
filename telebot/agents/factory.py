from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.learn import LearningMachine, LearningMode, SessionContextConfig, UserMemoryConfig, UserProfileConfig
from agno.models.openai import OpenAIResponses
from agno.team import Team
from agno.team.mode import TeamMode

from telebot.agents.schemas import PostClassificationBatch, ResearchTweetSynthesisResult
from telebot.common.constants import (
    AGNO_MAX_ITERATIONS,
    AGNO_TOOL_CALL_LIMIT,
    EVIDENCE_SYNTHESIZER_NAME,
    OPENAI_CHAT_MODEL,
    PLANNER_NAME,
    RESEARCH_ANALYST_NAME,
    RESEARCH_REVIEWER_NAME,
    SYNTHESIS_TEAM_NAME,
)
from telebot.config import Settings
from telebot.prompts.classification import CLASSIFICATION_SYSTEM_PROMPT
from telebot.prompts.creator import CREATOR_SYSTEM_PROMPT
from telebot.prompts.research import (
    EVIDENCE_SYNTHESIZER_PROMPT,
    RESEARCH_ANALYST_PROMPT,
    RESEARCH_PLANNER_PROMPT,
    RESEARCH_REVIEWER_PROMPT,
)
from telebot.search.schemas import PostResearchPlan



def _load_reasoning_tools():
    try:
        from agno.tools.reasoning import ReasoningTools
        return ReasoningTools
    except ImportError as exc:
        raise RuntimeError(
            "Agno ReasoningTools is unavailable. Check the installed Agno version and environment."
        ) from exc


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
            markdown=True,
            tool_call_limit=AGNO_TOOL_CALL_LIMIT,
        )

    def build_search_planner(self) -> Agent:
        ReasoningTools = _load_reasoning_tools()
        return Agent(
            name=PLANNER_NAME,
            model=self._model(),
            tools=[ReasoningTools(add_instructions=True)],
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

    def build_research_synthesis_team(self) -> Team:
        ReasoningTools = _load_reasoning_tools()
        analyst = Agent(
            name=RESEARCH_ANALYST_NAME,
            model=self._model(),
            instructions=[RESEARCH_ANALYST_PROMPT],
            markdown=True,
        )
        synthesizer = Agent(
            name=EVIDENCE_SYNTHESIZER_NAME,
            model=self._model(),
            instructions=[EVIDENCE_SYNTHESIZER_PROMPT],
            markdown=True,
        )
        reviewer = Agent(
            name=RESEARCH_REVIEWER_NAME,
            model=self._model(),
            instructions=[RESEARCH_REVIEWER_PROMPT],
            markdown=True,
        )
        return Team(
            name=SYNTHESIS_TEAM_NAME,
            mode=TeamMode.tasks,
            model=self._model(),
            members=[analyst, synthesizer, reviewer],
            output_schema=ResearchTweetSynthesisResult,
            tools=[ReasoningTools(add_instructions=True)],
            instructions=[
                "Use the task workflow: analyze, synthesize, review.",
                "Use only grounded evidence supplied by the caller.",
                "Return structured output only.",
            ],
            max_iterations=AGNO_MAX_ITERATIONS,
            markdown=True,
            show_members_responses=True,
        )
