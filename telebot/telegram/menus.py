from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

from telebot.common.commands import ACTION_COMMANDS, BUTTON_LABELS, CALLBACK_PREFIX, MENU_COMMANDS
from telebot.common.commands import COMMAND_DESCRIPTIONS


def build_inline_menu() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []
    for command in ACTION_COMMANDS:
        current_row.append(
            InlineKeyboardButton(
                text=BUTTON_LABELS[command],
                callback_data=f"{CALLBACK_PREFIX}{command.value}",
            )
        )
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_menu_commands() -> list[BotCommand]:
    return [
        BotCommand(command=command.value, description=COMMAND_DESCRIPTIONS[command])
        for command in MENU_COMMANDS
    ]
