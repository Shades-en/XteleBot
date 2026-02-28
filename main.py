import asyncio
import logging
import os
import ssl

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

TOKEN_ENV_VAR = "TELEGRAM_BOT_TOKEN"
DISABLE_SSL_VERIFY_ENV_VAR = "TELEGRAM_DISABLE_SSL_VERIFY"
PROXY_ENV_VAR = "TELEGRAM_PROXY"
BOT_ENV_VAR = "BOT_ENV"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_bot_env() -> str:
    env_value = os.getenv(BOT_ENV_VAR, "development").strip().lower()
    return env_value or "development"


def build_session(bot_env: str) -> AiohttpSession:
    proxy_raw = os.getenv(PROXY_ENV_VAR)
    proxy = proxy_raw.strip() if proxy_raw else None
    disable_ssl_verify = env_bool(DISABLE_SSL_VERIFY_ENV_VAR)

    if disable_ssl_verify and bot_env != "development":
        raise RuntimeError(
            f"{DISABLE_SSL_VERIFY_ENV_VAR}=true is allowed only when {BOT_ENV_VAR}=development."
        )

    session = AiohttpSession(proxy=proxy)
    if disable_ssl_verify:
        insecure_ssl_context = ssl.create_default_context()
        insecure_ssl_context.check_hostname = False
        insecure_ssl_context.verify_mode = ssl.CERT_NONE
        # aiogram does not expose this via public params; connector config is internal.
        session._connector_init["ssl"] = insecure_ssl_context
        logging.warning(
            "SSL certificate verification is disabled via %s=true",
            DISABLE_SSL_VERIFY_ENV_VAR,
        )

    return session


async def handle_start(message: Message) -> None:
    await message.answer("Hi. I am alive. Send me any text and I will echo it.")


async def handle_ping(message: Message) -> None:
    await message.answer("pong")


async def handle_echo(message: Message) -> None:
    if message.text:
        await message.answer(f"echo: {message.text}")


async def main() -> None:
    load_dotenv()
    token = os.getenv(TOKEN_ENV_VAR)
    bot_env = get_bot_env()

    if not token:
        raise RuntimeError(
            f"Missing {TOKEN_ENV_VAR}. Add it to .env or your shell environment."
        )

    logging.info("Bot mode: %s", bot_env)
    bot = Bot(token=token, session=build_session(bot_env))
    dp = Dispatcher()

    dp.message.register(handle_start, CommandStart())
    dp.message.register(handle_ping, Command("ping"))
    dp.message.register(handle_echo, F.text)

    try:
        await dp.start_polling(bot)
    except TelegramNetworkError as exc:
        logging.error("Network error while reaching Telegram API: %s", exc)
        logging.error(
            "If local network blocks Telegram, deploy remotely or configure TELEGRAM_PROXY."
        )
        raise


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


if __name__ == "__main__":
    run()
