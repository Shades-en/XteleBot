import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import ClientDecodeError, TelegramNetworkError
from aiogram.types import BotCommand
from dotenv import load_dotenv

from telebot.config import Settings, load_settings
from telebot.constants import (
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ERR_DEV_PROXY_REQUIRED,
    GENERIC_AUTH_REQUIRED_MARKER,
    LOG_BOT_ENV,
    LOG_DIRECT_API_MODE,
    LOG_NETWORK_ERROR_DIRECT,
    LOG_NETWORK_ERROR_WITH_PROXY,
    LOG_POLLING_MODE_ENABLED,
    LOG_PROXY_AUTH_PROTECTED,
    LOG_PROXY_TARGET,
    LOG_TELEGRAM_API_BASE_URL,
    LOG_VERCEL_BYPASS_NOT_SET,
    LOG_VERCEL_BYPASS_SET,
    LOG_VERCEL_BYPASS_TOKEN_STATUS,
    VERCEL_AUTH_MARKER,
)
from telebot.handlers import build_bot_menu_commands, register_handlers
from telebot.session import create_proxy_session


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    register_handlers(dispatcher)
    return dispatcher


def create_bot(settings: Settings) -> Bot:
    if settings.bot_env == ENV_PRODUCTION:
        return Bot(token=settings.token)

    if settings.api_base_url is None or settings.proxy_target is None:
        raise RuntimeError(ERR_DEV_PROXY_REQUIRED)

    session = create_proxy_session(
        api_base_url=settings.api_base_url,
        proxy_target=settings.proxy_target,
        vercel_bypass_token=settings.vercel_bypass_token,
    )
    return Bot(token=settings.token, session=session)


def is_vercel_auth_page(content: str) -> bool:
    lowered = content.lower()
    return VERCEL_AUTH_MARKER in lowered or GENERIC_AUTH_REQUIRED_MARKER in lowered


def build_bot_commands() -> list[BotCommand]:
    return [
        BotCommand(command=name, description=description)
        for name, description in build_bot_menu_commands()
    ]


async def run_polling(settings: Settings) -> None:
    bot = create_bot(settings)
    dispatcher = create_dispatcher()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_my_commands(build_bot_commands())
        await dispatcher.start_polling(bot)
    except ClientDecodeError as exc:
        content = str(exc.data)
        if is_vercel_auth_page(content):
            logging.error(LOG_PROXY_AUTH_PROTECTED)
        raise
    except TelegramNetworkError as exc:
        if settings.bot_env == ENV_DEVELOPMENT:
            logging.error(LOG_NETWORK_ERROR_WITH_PROXY, settings.api_base_url, exc)
        else:
            logging.error(LOG_NETWORK_ERROR_DIRECT, exc)
        raise
    finally:
        await bot.session.close()


def run() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    logging.info(LOG_POLLING_MODE_ENABLED)
    logging.info(LOG_BOT_ENV, settings.bot_env)
    if settings.bot_env == ENV_DEVELOPMENT:
        logging.info(LOG_TELEGRAM_API_BASE_URL, settings.api_base_url)
        logging.info(LOG_PROXY_TARGET, settings.proxy_target)
        token_status = (
            LOG_VERCEL_BYPASS_SET
            if settings.vercel_bypass_token
            else LOG_VERCEL_BYPASS_NOT_SET
        )
        logging.info(LOG_VERCEL_BYPASS_TOKEN_STATUS, token_status)
    else:
        logging.info(LOG_DIRECT_API_MODE)

    asyncio.run(run_polling(settings=settings))
