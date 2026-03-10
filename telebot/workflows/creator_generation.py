from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.common.messages import TEXT_GENERIC_WORKFLOW_FAILURE
from telebot.costs.openai import record_run_output
from telebot.costs.tracker import WorkflowCostTracker
from telebot.workflows.creator_data import load_creator_style_examples, load_post_by_id
from telebot.workflows.creator_jobs import complete_creator_job, fail_creator_job
from telebot.workflows.creator_prompting import (
    build_creator_prompt,
    build_creator_refiner_prompt,
)
from telebot.workflows.creator_runtime import build_creator_context, creator_images
from telebot.workflows.creator_session import CreatorSessionState
from telebot.workflows.creator_types import CreatorDraftResult, CreatorValidationResult
from telebot.workflows.creator_validation import sanitize_creator_body, validate_creator_body

CREATE_DRAFT_STEP = "Create Draft"
VALIDATE_DRAFT_STEP = "Validate Draft"


class CreateDraftExecutor:
    def __init__(self, agno_factory: AgnoFactory, cost_tracker: WorkflowCostTracker | None) -> None:
        self.agno_factory = agno_factory
        self.cost_tracker = cost_tracker

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context = step_input.additional_data["context"]
        response = await self.agno_factory.build_creator_agent().arun(
            build_creator_prompt(context),
            user_id=str(step_input.additional_data["telegram_user_id"]),
            session_id=step_input.additional_data["creator_session_id"],
            images=step_input.additional_data["images"],
        )
        record_run_output(self.cost_tracker, response)
        return StepOutput(content={"draft": str(response.content)})


class ValidateDraftExecutor:
    async def __call__(self, step_input: StepInput) -> StepOutput:
        context = step_input.additional_data["context"]
        draft_output = step_input.get_step_output(CREATE_DRAFT_STEP)
        draft = str(getattr(draft_output, "content", {}).get("draft", ""))
        validation = validate_creator_body(context.command, draft)
        return StepOutput(content={"draft": draft, "issues": validation.issues})


class RefineDraftExecutor:
    def __init__(self, agno_factory: AgnoFactory, cost_tracker: WorkflowCostTracker | None) -> None:
        self.agno_factory = agno_factory
        self.cost_tracker = cost_tracker

    async def __call__(self, step_input: StepInput) -> StepOutput:
        context = step_input.additional_data["context"]
        validation_output = step_input.get_step_output(VALIDATE_DRAFT_STEP)
        content = getattr(validation_output, "content", {})
        draft = str(content.get("draft", ""))
        validation = CreatorValidationResult(
            issues=[str(item) for item in content.get("issues", []) if item]
        )
        response = await self.agno_factory.build_creator_refiner_agent().arun(
            build_creator_refiner_prompt(context, draft, validation),
            user_id=str(step_input.additional_data["telegram_user_id"]),
            session_id=step_input.additional_data["refiner_session_id"],
            images=step_input.additional_data["images"],
        )
        record_run_output(self.cost_tracker, response)
        return StepOutput(
            content={
                "body": sanitize_creator_body(str(response.content)),
                "source_url": context.source_post.source_url,
                "related_source_urls": _related_source_urls(context.source_post.related_sources),
            }
        )


async def run_creator_draft(
    session_factory: async_sessionmaker[AsyncSession],
    agno_factory: AgnoFactory,
    telegram_user_id: int,
    session_id: str,
    state: CreatorSessionState,
    job_id: str,
    refinement: str | None = None,
    cost_tracker: WorkflowCostTracker | None = None,
) -> CreatorDraftResult:
    try:
        result = await _run_creator_workflow(
            session_factory,
            agno_factory,
            telegram_user_id,
            session_id,
            state,
            refinement,
            cost_tracker,
        )
    except Exception as exc:
        await fail_creator_job(
            session_factory,
            job_id,
            str(exc) or TEXT_GENERIC_WORKFLOW_FAILURE,
            (cost_tracker or WorkflowCostTracker()).summary(),
        )
        raise
    await complete_creator_job(
        session_factory,
        job_id,
        (cost_tracker or WorkflowCostTracker()).summary(),
    )
    return result


async def _run_creator_workflow(
    session_factory: async_sessionmaker[AsyncSession],
    agno_factory: AgnoFactory,
    telegram_user_id: int,
    session_id: str,
    state: CreatorSessionState,
    refinement: str | None,
    cost_tracker: WorkflowCostTracker | None,
) -> CreatorDraftResult:
    source_post = await load_post_by_id(session_factory, state.selected_source_post_id)
    if source_post is None:
        raise RuntimeError("Selected creator source post not found.")
    context = build_creator_context(
        state.command,
        source_post,
        await load_creator_style_examples(session_factory, telegram_user_id),
        refinement=refinement,
    )
    workflow = Workflow(
        name="Creator Workflow",
        steps=[
            Step(
                name=CREATE_DRAFT_STEP,
                executor=CreateDraftExecutor(agno_factory, cost_tracker),
            ),
            Step(name=VALIDATE_DRAFT_STEP, executor=ValidateDraftExecutor()),
            Step(
                name="Refine Draft",
                executor=RefineDraftExecutor(agno_factory, cost_tracker),
            ),
        ],
    )
    result = await workflow.arun(
        input="Generate creator draft",
        additional_data={
            "context": context,
            "telegram_user_id": telegram_user_id,
            "creator_session_id": session_id,
            "refiner_session_id": f"{session_id}:refiner",
            "images": creator_images(context),
        },
        user_id=str(telegram_user_id),
    )
    content = getattr(result, "content", result)
    body = sanitize_creator_body(str(content.get("body", "")))
    return CreatorDraftResult(
        body=body,
        source_url=content.get("source_url"),
        related_source_urls=[
            str(item) for item in content.get("related_source_urls", []) if item
        ],
    )


def _related_source_urls(related_sources: list[dict]) -> list[str]:
    urls: list[str] = []
    for source in related_sources:
        url = source.get("url") if isinstance(source, dict) else None
        if not isinstance(url, str) or not url or url in urls:
            continue
        urls.append(url)
    return urls
