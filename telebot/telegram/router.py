from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery

from telebot.common.commands import (
    CALLBACK_PREFIX,
    CREATOR_ALTERNATIVES_CALLBACK_PREFIX,
    CREATOR_PICK_CALLBACK_PREFIX,
)
from telebot.common.enums import CommandName
from telebot.common.messages import TEXT_UNSUPPORTED_ACTION
from telebot.telegram.handlers import TelegramHandlers


async def handle_callback(callback: CallbackQuery, handlers: TelegramHandlers) -> None:
    if callback.data is None or callback.message is None:
        await callback.answer(TEXT_UNSUPPORTED_ACTION)
        return
    actor_user_id = callback.from_user.id
    actor_display_name = callback.from_user.full_name
    if callback.data == CREATOR_ALTERNATIVES_CALLBACK_PREFIX:
        await callback.answer()
        await handlers.handle_creator_alternatives(
            callback.message,
            actor_user_id=actor_user_id,
        )
        return
    if callback.data.startswith(CREATOR_PICK_CALLBACK_PREFIX):
        await callback.answer()
        await handlers.handle_creator_pick(
            callback.message,
            selected_post_id=callback.data[len(CREATOR_PICK_CALLBACK_PREFIX) :],
            actor_user_id=actor_user_id,
        )
        return
    if not callback.data.startswith(CALLBACK_PREFIX):
        await callback.answer(TEXT_UNSUPPORTED_ACTION)
        return
    command_name = callback.data[len(CALLBACK_PREFIX) :]
    try:
        command = CommandName(command_name)
    except ValueError:
        await callback.answer(TEXT_UNSUPPORTED_ACTION)
        return
    await callback.answer()
    if command is CommandName.CURRENT_USER:
        await handlers.handle_currentuser(
            callback.message,
            actor_user_id=actor_user_id,
            actor_display_name=actor_display_name,
        )
        return
    if command is CommandName.SCHEDULE:
        await handlers.handle_schedule(callback.message, actor_user_id=actor_user_id)
        return
    if command is CommandName.JOB_STATUS:
        await handlers.handle_jobstatus(callback.message, actor_user_id=actor_user_id)
        return
    if command is CommandName.PING_WORKER:
        await handlers.handle_pingworker(callback.message, actor_user_id=actor_user_id)
        return
    if command is CommandName.ANALYZE_TODAY:
        await handlers.handle_analysetoday(callback.message, actor_user_id=actor_user_id)
        return
    if command is CommandName.REANALYZE_FOR_TODAY:
        await handlers.handle_reanalysefortoday(
            callback.message,
            actor_user_id=actor_user_id,
        )
        return
    if command is CommandName.POST_BY_INSPIRATION:
        await handlers.handle_postbyinspiration(
            callback.message,
            actor_user_id=actor_user_id,
        )
        return
    if command is CommandName.QUOTE:
        await handlers.handle_quote(callback.message, actor_user_id=actor_user_id)
        return
    if command is CommandName.COMMENT:
        await handlers.handle_comment(callback.message, actor_user_id=actor_user_id)
        return
    await handlers.handle_help(callback.message)


def register_handlers(dispatcher: Dispatcher, handlers: TelegramHandlers) -> None:
    async def callback_handler(callback: CallbackQuery) -> None:
        await handle_callback(callback, handlers)

    dispatcher.message.register(handlers.handle_start, CommandStart())
    dispatcher.message.register(handlers.handle_help, Command(CommandName.HELP.value))
    dispatcher.message.register(handlers.handle_ping, Command(CommandName.PING.value))
    dispatcher.message.register(
        handlers.handle_pingworker,
        Command(CommandName.PING_WORKER.value),
    )
    dispatcher.message.register(
        handlers.handle_resetschema,
        Command(CommandName.RESET_SCHEMA.value),
    )
    dispatcher.message.register(
        handlers.handle_currentuser,
        Command(CommandName.CURRENT_USER.value),
    )
    dispatcher.message.register(
        handlers.handle_jobstatus,
        Command(CommandName.JOB_STATUS.value),
    )
    dispatcher.message.register(handlers.handle_schedule, Command(CommandName.SCHEDULE.value))
    dispatcher.message.register(
        handlers.handle_analysetoday,
        Command(CommandName.ANALYZE_TODAY.value),
    )
    dispatcher.message.register(
        handlers.handle_reanalysefortoday,
        Command(CommandName.REANALYZE_FOR_TODAY.value),
    )
    dispatcher.message.register(
        handlers.handle_postbyinspiration,
        Command(CommandName.POST_BY_INSPIRATION.value),
    )
    dispatcher.message.register(handlers.handle_quote, Command(CommandName.QUOTE.value))
    dispatcher.message.register(handlers.handle_comment, Command(CommandName.COMMENT.value))
    dispatcher.callback_query.register(callback_handler)
    dispatcher.message.register(handlers.handle_text, F.text)
