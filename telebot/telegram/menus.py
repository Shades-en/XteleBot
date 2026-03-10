from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

from telebot.common.commands import (
    ACTION_COMMANDS,
    BUTTON_LABELS,
    CALLBACK_PREFIX,
    CREATOR_ALTERNATIVES_CALLBACK_PREFIX,
    CREATOR_PICK_CALLBACK_PREFIX,
    MENU_COMMANDS,
)
from telebot.common.commands import COMMAND_DESCRIPTIONS
from telebot.common.messages import (
    TEXT_CREATOR_DIFFERENT_POST_BUTTON,
    TEXT_CREATOR_MORE_OPTIONS_BUTTON,
    TEXT_CREATOR_PICK_OPTION_TEMPLATE,
)


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


def build_creator_draft_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=TEXT_CREATOR_DIFFERENT_POST_BUTTON,
                    callback_data=CREATOR_ALTERNATIVES_CALLBACK_PREFIX,
                )
            ]
        ]
    )


def build_creator_candidate_menu(
    candidate_post_ids: list[str],
    include_more_options: bool,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=TEXT_CREATOR_PICK_OPTION_TEMPLATE.format(index=index),
                callback_data=f"{CREATOR_PICK_CALLBACK_PREFIX}{post_id}",
            )
        ]
        for index, post_id in enumerate(candidate_post_ids, start=1)
    ]
    if include_more_options:
        rows.append(
            [
                InlineKeyboardButton(
                    text=TEXT_CREATOR_MORE_OPTIONS_BUTTON,
                    callback_data=CREATOR_ALTERNATIVES_CALLBACK_PREFIX,
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
