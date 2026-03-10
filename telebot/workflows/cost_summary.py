from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.messages import TEXT_COST_PERIOD_TEMPLATE, TEXT_COST_SUMMARY_TEMPLATE
from telebot.costs.schemas import (
    OpenAIModelUsage,
    TwitterEndpointUsage,
    WorkflowCostSummary,
)
from telebot.db.repositories.jobs import JobRepository

TODAY_LABEL = "Today"
MONTH_LABEL = "This month"
YEAR_LABEL = "This year"
OVERALL_LABEL = "All time"


class CostSummaryWorkflowService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def render_cost_summary(self, telegram_user_id: int) -> str:
        async with self.session_factory() as session:
            jobs = await JobRepository(session).list_costed_jobs_for_user(telegram_user_id)
        summaries = [_summary_from_job(job) for job in jobs]
        created_at_values = [job.created_at for job in jobs if isinstance(job.created_at, datetime)]
        now = datetime.utcnow()
        return TEXT_COST_SUMMARY_TEMPLATE.format(
            today_section=_format_period(
                TODAY_LABEL,
                _aggregate_matching(
                    summaries,
                    created_at_values,
                    lambda created_at: created_at.date() == now.date(),
                ),
            ),
            month_section=_format_period(
                MONTH_LABEL,
                _aggregate_matching(
                    summaries,
                    created_at_values,
                    lambda created_at: (
                        created_at.year == now.year and created_at.month == now.month
                    ),
                ),
            ),
            year_section=_format_period(
                YEAR_LABEL,
                _aggregate_matching(
                    summaries,
                    created_at_values,
                    lambda created_at: created_at.year == now.year,
                ),
            ),
            overall_section=_format_period(OVERALL_LABEL, _aggregate_summaries(summaries)),
        )


def _summary_from_job(job) -> WorkflowCostSummary:
    return WorkflowCostSummary.model_validate(
        {
            "total_cost_usd": float(job.total_cost_usd or 0.0),
            **(job.cost_breakdown or {}),
        }
    )


def _aggregate_matching(
    summaries: list[WorkflowCostSummary],
    created_at_values: list[datetime],
    predicate,
) -> WorkflowCostSummary:
    matching = [
        summary
        for summary, created_at in zip(summaries, created_at_values, strict=True)
        if predicate(created_at)
    ]
    return _aggregate_summaries(matching)


def _aggregate_summaries(summaries: list[WorkflowCostSummary]) -> WorkflowCostSummary:
    total = WorkflowCostSummary()
    for summary in summaries:
        total.total_cost_usd += summary.total_cost_usd
        total.openai.total_cost_usd += summary.openai.total_cost_usd
        total.brave.request_count += summary.brave.request_count
        total.brave.total_cost_usd += summary.brave.total_cost_usd
        total.twitter.total_credits += summary.twitter.total_credits
        total.twitter.total_cost_usd += summary.twitter.total_cost_usd
        for model_id, usage in summary.openai.models.items():
            _accumulate_openai_usage(total.openai.models, model_id, usage)
        for model_id, usage in summary.openai.unknown_models.items():
            _accumulate_openai_usage(total.openai.unknown_models, model_id, usage)
        for endpoint, usage in summary.twitter.endpoints.items():
            _accumulate_twitter_usage(total.twitter.endpoints, endpoint, usage)
        total.warnings.extend(
            warning for warning in summary.warnings if warning not in total.warnings
        )
    return total


def _accumulate_openai_usage(
    target: dict[str, OpenAIModelUsage],
    model_id: str,
    usage: OpenAIModelUsage,
) -> None:
    existing = target.get(model_id)
    if existing is None:
        target[model_id] = OpenAIModelUsage.model_validate(usage.model_dump())
        return
    existing.input_tokens += usage.input_tokens
    existing.cached_input_tokens += usage.cached_input_tokens
    existing.output_tokens += usage.output_tokens
    existing.total_cost_usd += usage.total_cost_usd


def _accumulate_twitter_usage(
    target: dict[str, TwitterEndpointUsage],
    endpoint: str,
    usage: TwitterEndpointUsage,
) -> None:
    existing = target.get(endpoint)
    if existing is None:
        target[endpoint] = TwitterEndpointUsage.model_validate(usage.model_dump())
        return
    existing.calls += usage.calls
    existing.returned_count += usage.returned_count
    existing.credits += usage.credits
    existing.total_cost_usd += usage.total_cost_usd


def _format_period(label: str, summary: WorkflowCostSummary) -> str:
    return TEXT_COST_PERIOD_TEMPLATE.format(
        label=label,
        total_cost_usd=summary.total_cost_usd,
        openai_cost_usd=summary.openai.total_cost_usd,
        twitter_cost_usd=summary.twitter.total_cost_usd,
        search_cost_usd=summary.brave.total_cost_usd,
    )
