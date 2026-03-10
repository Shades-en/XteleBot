from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.common.enums import CommandName, SessionStatus
from telebot.costs.formatting import format_cost_summary
from telebot.costs.tracker import WorkflowCostTracker
from telebot.common.messages import (
    TEXT_CREATOR_ACK,
    TEXT_CREATOR_ALTERNATIVES_HEADER_TEMPLATE,
    TEXT_CREATOR_SELECTION_HEADER_TEMPLATE,
    TEXT_CREATOR_COST_TEMPLATE,
    TEXT_CREATOR_NO_ALTERNATIVES_TEMPLATE,
    TEXT_CREATOR_PROGRESS,
    TEXT_CREATOR_REFINEMENT_ACK,
    TEXT_RELATED_SOURCES_HEADER,
    TEXT_CREATOR_STALE_SELECTION,
    TEXT_SETUP_REQUIRED,
    TEXT_SOURCE_POST_LINK_TEMPLATE,
)
from telebot.db.repositories.users import UserRepository
from telebot.telegram.menus import (
    build_creator_candidate_menu,
    build_creator_draft_actions,
)
from telebot.workflows.creator_data import (
    active_creator_state,
    creator_state_from_session,
    effective_user_id,
    initialize_creator_state,
    posts_in_order,
    save_creator_state,
    status_for_command,
    store_draft_message_id,
    unavailable_message,
)
from telebot.workflows.creator_generation import run_creator_draft
from telebot.workflows.creator_jobs import start_creator_job
from telebot.workflows.creator_runtime import render_candidate_previews


class CreatorWorkflowService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agno_factory: AgnoFactory,
    ) -> None:
        self.session_factory = session_factory
        self.agno_factory = agno_factory

    async def handle_command(
        self,
        message: Message,
        command: CommandName,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = effective_user_id(message, actor_user_id)
        async with self.session_factory() as session:
            users = UserRepository(session)
            user = await users.ensure_user(telegram_user_id)
            if not user.x_username or not user.x_id:
                await message.answer(TEXT_SETUP_REQUIRED)
                return
            state = await initialize_creator_state(
                self.session_factory,
                telegram_user_id,
                command,
            )
            if state is None:
                await message.answer(unavailable_message(command))
                return
            candidate_ids, state = state.initial_candidate_window()
            preview_posts = await posts_in_order(self.session_factory, candidate_ids)
            await message.answer(TEXT_CREATOR_ACK[command])
            await users.set_status(
                telegram_user_id,
                status_for_command(command),
                command.value,
            )
            await users.set_creator_state(telegram_user_id, state.to_dict())
            await session.commit()
        await message.answer(
            TEXT_CREATOR_SELECTION_HEADER_TEMPLATE.format(
                purpose=state.purpose.value.lower(),
                options=render_candidate_previews(preview_posts),
            ),
            reply_markup=build_creator_candidate_menu(
                candidate_ids,
                include_more_options=state.has_more_candidates(),
            ),
        )

    async def handle_follow_up(self, message: Message) -> bool:
        async with self.session_factory() as session:
            users = UserRepository(session)
            current_session = await users.get_current_session(message.from_user.id)
            user = await users.ensure_user(message.from_user.id)
            if current_session is None or current_session.status not in {
                SessionStatus.GENERATING_POST,
                SessionStatus.GENERATING_QUOTE,
                SessionStatus.GENERATING_COMMENT,
            }:
                return False
            state = await creator_state_from_session(
                self.session_factory,
                message.from_user.id,
                current_session,
            )
            if state is None:
                return False
            if state.awaiting_source_selection or state.draft_message_id is None:
                return False
            await message.answer(TEXT_CREATOR_REFINEMENT_ACK[state.command])
            await message.answer(TEXT_CREATOR_PROGRESS[state.command])
            cost_tracker = WorkflowCostTracker()
            job_id = await start_creator_job(
                self.session_factory,
                message.from_user.id,
                state.command,
                TEXT_CREATOR_PROGRESS[state.command],
            )
            draft_result = await run_creator_draft(
                session_factory=self.session_factory,
                agno_factory=self.agno_factory,
                telegram_user_id=message.from_user.id,
                session_id=user.current_session_id or current_session.session_id,
                state=state,
                job_id=job_id,
                refinement=message.text,
                cost_tracker=cost_tracker,
            )
        sent = await message.answer(draft_result.body, reply_markup=build_creator_draft_actions())
        await self._send_sources(message, draft_result.source_url, draft_result.related_source_urls)
        await message.answer(TEXT_CREATOR_COST_TEMPLATE.format(summary=format_cost_summary(cost_tracker.summary())))
        await store_draft_message_id(self.session_factory, message.from_user.id, sent.message_id)
        return True

    async def handle_show_alternatives(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = effective_user_id(message, actor_user_id)
        state = await active_creator_state(self.session_factory, telegram_user_id)
        if state is None:
            await message.answer(TEXT_CREATOR_STALE_SELECTION)
            return
        if state.draft_message_id is None and state.awaiting_source_selection:
            candidate_ids, next_state = state.next_candidate_window()
            header_template = TEXT_CREATOR_SELECTION_HEADER_TEMPLATE
            include_more_options = next_state.has_more_candidates()
        else:
            candidate_ids, next_state = state.next_alternative_window()
            header_template = TEXT_CREATOR_ALTERNATIVES_HEADER_TEMPLATE
            include_more_options = next_state.has_more_alternatives()
        if not candidate_ids:
            await message.answer(
                TEXT_CREATOR_NO_ALTERNATIVES_TEMPLATE.format(
                    purpose=state.purpose.value.lower(),
                )
            )
            return
        preview_posts = await posts_in_order(self.session_factory, candidate_ids)
        await save_creator_state(self.session_factory, telegram_user_id, next_state)
        await message.answer(
            header_template.format(
                purpose=state.purpose.value.lower(),
                options=render_candidate_previews(preview_posts),
            ),
            reply_markup=build_creator_candidate_menu(
                candidate_ids,
                include_more_options=include_more_options,
            ),
        )

    async def handle_select_source_post(
        self,
        message: Message,
        selected_post_id: str,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = effective_user_id(message, actor_user_id)
        async with self.session_factory() as session:
            users = UserRepository(session)
            current_session = await users.get_current_session(telegram_user_id)
            if current_session is None:
                await message.answer(TEXT_CREATOR_STALE_SELECTION)
                return
            state = await creator_state_from_session(
                self.session_factory,
                telegram_user_id,
                current_session,
            )
            if state is None or selected_post_id not in state.candidate_post_ids:
                await message.answer(TEXT_CREATOR_STALE_SELECTION)
                return
            next_state = state.with_selected_source_post_id(selected_post_id)
            await users.set_creator_state(telegram_user_id, next_state.to_dict())
            await session.commit()
            await message.answer(TEXT_CREATOR_PROGRESS[state.command])
            cost_tracker = WorkflowCostTracker()
            job_id = await start_creator_job(
                self.session_factory,
                telegram_user_id,
                state.command,
                TEXT_CREATOR_PROGRESS[state.command],
            )
            draft_result = await run_creator_draft(
                session_factory=self.session_factory,
                agno_factory=self.agno_factory,
                telegram_user_id=telegram_user_id,
                session_id=current_session.session_id,
                state=next_state,
                job_id=job_id,
                cost_tracker=cost_tracker,
            )
        sent = await message.answer(draft_result.body, reply_markup=build_creator_draft_actions())
        await self._send_sources(message, draft_result.source_url, draft_result.related_source_urls)
        await message.answer(TEXT_CREATOR_COST_TEMPLATE.format(summary=format_cost_summary(cost_tracker.summary())))
        await store_draft_message_id(self.session_factory, telegram_user_id, sent.message_id)

    @staticmethod
    async def _send_sources(
        message: Message,
        source_url: str | None,
        related_source_urls: list[str],
    ) -> None:
        lines: list[str] = []
        if source_url:
            lines.append(TEXT_SOURCE_POST_LINK_TEMPLATE.format(source_url=source_url))
        unique_related_urls = [url for url in related_source_urls if url and url != source_url]
        if unique_related_urls:
            if lines:
                lines.append("")
            lines.append(TEXT_RELATED_SOURCES_HEADER)
            lines.extend(unique_related_urls)
        if lines:
            await message.answer("\n".join(lines))
