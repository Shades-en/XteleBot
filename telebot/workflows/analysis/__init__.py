from agno.workflow.step import Step
from agno.workflow.workflow import Workflow
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.twitter.client import TwitterApiClient
from telebot.workflows.analysis.classify import ClassifyTopPostsExecutor
from telebot.workflows.analysis.collect import CollectPostsExecutor
from telebot.workflows.analysis.common import AnalysisContext
from telebot.workflows.analysis.rank import RankPostsExecutor
from telebot.workflows.analysis.replies import FetchReplyContextExecutor
from telebot.workflows.analysis.research import ResearchTweetsExecutor


def build_analysis_workflow(
    session_factory: async_sessionmaker[AsyncSession],
    twitter_client: TwitterApiClient,
    agno_factory: AgnoFactory,
) -> Workflow:
    return Workflow(
        name="Analyze Today Workflow",
        steps=[
            Step(
                name="Collect Posts",
                executor=CollectPostsExecutor(session_factory, twitter_client),
            ),
            Step(name="Rank Posts", executor=RankPostsExecutor(session_factory)),
            Step(
                name="Classify Top Posts",
                executor=ClassifyTopPostsExecutor(session_factory, agno_factory),
            ),
            Step(
                name="Fetch Reply Context",
                executor=FetchReplyContextExecutor(session_factory, twitter_client),
            ),
            Step(
                name="Research Tweets",
                executor=ResearchTweetsExecutor(session_factory, agno_factory),
            ),
        ],
    )


__all__ = ["AnalysisContext", "build_analysis_workflow"]
