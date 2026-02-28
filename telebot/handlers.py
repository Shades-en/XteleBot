from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from telebot.constants import (
    ACTION_COMMANDS,
    BOT_MENU_COMMANDS,
    COMMAND_CONTENT_STYLE_CREATORS,
    COMMAND_HELP,
    COMMAND_PING,
    COMMAND_POST,
    COMMAND_REPLYPOST,
    COMMAND_SCHEDULE,
    COMMAND_TOP10,
    COMMAND_TOP10FAV,
    COMMAND_UPDATEFAV,
    COMMAND_UPDATE_CONTENT_STYLE_CREATORS,
    TEXT_BOILERPLATE_TEMPLATE,
    TEXT_CHOOSE_COMMAND,
    TEXT_PONG,
    TEXT_UNRECOGNIZED_COMMAND,
    TEXT_UNSUPPORTED_ACTION,
)

COMMAND_PREFIX = "/"
CALLBACK_PREFIX = "cmd:"

KNOWN_COMMAND_NAMES = {name for name, _ in ACTION_COMMANDS}


def build_commands_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for name, _ in ACTION_COMMANDS:
        row.append(
            InlineKeyboardButton(
                text=f"{COMMAND_PREFIX}{name}",
                callback_data=f"{CALLBACK_PREFIX}{name}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_commands_panel(message: Message) -> None:
    await message.answer(TEXT_CHOOSE_COMMAND, reply_markup=build_commands_keyboard())


async def send_stub(message: Message, command: str) -> None:
    await message.answer(TEXT_BOILERPLATE_TEMPLATE.format(command=command))


async def handle_start(message: Message) -> None:
    await send_commands_panel(message)


async def handle_help(message: Message) -> None:
    await send_commands_panel(message)


async def handle_ping(message: Message) -> None:
    await message.answer(TEXT_PONG)


async def handle_replypost(message: Message) -> None:
    await send_stub(message, COMMAND_REPLYPOST)


async def handle_post(message: Message) -> None:
    await send_stub(message, COMMAND_POST)


async def handle_schedule(message: Message) -> None:
    await send_stub(message, COMMAND_SCHEDULE)


async def handle_top10(message: Message) -> None:
    await send_stub(message, COMMAND_TOP10)


async def handle_top10fav(message: Message) -> None:
    await send_stub(message, COMMAND_TOP10FAV)


async def handle_updatefav(message: Message) -> None:
    await send_stub(message, COMMAND_UPDATEFAV)


async def handle_content_style_creators(message: Message) -> None:
    await send_stub(message, COMMAND_CONTENT_STYLE_CREATORS)


async def handle_update_content_style_creators(message: Message) -> None:
    await send_stub(message, COMMAND_UPDATE_CONTENT_STYLE_CREATORS)


async def handle_unknown_command(message: Message) -> None:
    await message.answer(TEXT_UNRECOGNIZED_COMMAND)


async def handle_command_button(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer(TEXT_UNSUPPORTED_ACTION, show_alert=False)
        return

    if not callback.data.startswith(CALLBACK_PREFIX):
        await callback.answer(TEXT_UNSUPPORTED_ACTION, show_alert=False)
        return

    prefix_len = len(CALLBACK_PREFIX)
    command = callback.data[prefix_len:]

    if command not in KNOWN_COMMAND_NAMES:
        await callback.answer(TEXT_UNSUPPORTED_ACTION, show_alert=False)
        return

    await callback.answer()
    if command == COMMAND_PING:
        await handle_ping(callback.message)
        return

    await send_stub(callback.message, command)


def build_bot_menu_commands() -> list[tuple[str, str]]:
    return list(BOT_MENU_COMMANDS)


def register_handlers(dispatcher: Dispatcher) -> None:
    dispatcher.message.register(handle_start, CommandStart())
    dispatcher.message.register(handle_help, Command(COMMAND_HELP))
    dispatcher.message.register(handle_ping, Command(COMMAND_PING))
    dispatcher.message.register(handle_replypost, Command(COMMAND_REPLYPOST))
    dispatcher.message.register(handle_post, Command(COMMAND_POST))
    dispatcher.message.register(handle_schedule, Command(COMMAND_SCHEDULE))
    dispatcher.message.register(handle_top10, Command(COMMAND_TOP10))
    dispatcher.message.register(handle_top10fav, Command(COMMAND_TOP10FAV))
    dispatcher.message.register(handle_updatefav, Command(COMMAND_UPDATEFAV))
    dispatcher.message.register(
        handle_content_style_creators,
        Command(COMMAND_CONTENT_STYLE_CREATORS),
    )
    dispatcher.message.register(
        handle_update_content_style_creators,
        Command(COMMAND_UPDATE_CONTENT_STYLE_CREATORS),
    )
    dispatcher.callback_query.register(
        handle_command_button,
        F.data.startswith(CALLBACK_PREFIX),
    )
    dispatcher.message.register(
        handle_unknown_command,
        F.text.startswith(COMMAND_PREFIX),
    )
