import asyncio
import logging
import os
from typing import Final

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

TOKEN_ENV_VAR: Final[str] = "TELEGRAM_BOT_TOKEN"
BOT_RUN_MODE_ENV_VAR: Final[str] = "BOT_RUN_MODE"
WEBHOOK_BASE_URL_ENV_VAR: Final[str] = "WEBHOOK_BASE_URL"
RENDER_EXTERNAL_URL_ENV_VAR: Final[str] = "RENDER_EXTERNAL_URL"
WEBHOOK_PATH_ENV_VAR: Final[str] = "WEBHOOK_PATH"
WEBHOOK_SECRET_TOKEN_ENV_VAR: Final[str] = "WEBHOOK_SECRET_TOKEN"
HOST_ENV_VAR: Final[str] = "HOST"
PORT_ENV_VAR: Final[str] = "PORT"

RUN_MODE_POLLING: Final[str] = "polling"
RUN_MODE_WEBHOOK: Final[str] = "webhook"
DEFAULT_WEBHOOK_PATH: Final[str] = "/telegram/webhook"
DEFAULT_HOST: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 10000


async def handle_start(message: Message) -> None:
    await message.answer("Hi. I am alive. Send me any text and I will echo it.")


async def handle_ping(message: Message) -> None:
    await message.answer("pong")


async def handle_echo(message: Message) -> None:
    if message.text:
        await message.answer(f"echo: {message.text}")


def get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


def get_run_mode() -> str:
    mode = get_env(BOT_RUN_MODE_ENV_VAR, RUN_MODE_POLLING).lower()
    if mode not in {RUN_MODE_POLLING, RUN_MODE_WEBHOOK}:
        raise RuntimeError(
            f"Invalid {BOT_RUN_MODE_ENV_VAR}={mode!r}. Use '{RUN_MODE_POLLING}' or '{RUN_MODE_WEBHOOK}'."
        )
    return mode


def get_token() -> str:
    token = os.getenv(TOKEN_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Missing {TOKEN_ENV_VAR}. Add it to .env or your shell environment."
        )
    return token


def get_webhook_path() -> str:
    raw_path = get_env(WEBHOOK_PATH_ENV_VAR, DEFAULT_WEBHOOK_PATH)
    if raw_path.startswith("/"):
        return raw_path
    return f"/{raw_path}"


def get_webhook_base_url() -> str:
    explicit_base_url = os.getenv(WEBHOOK_BASE_URL_ENV_VAR)
    if explicit_base_url and explicit_base_url.strip():
        base_url = explicit_base_url.strip().rstrip("/")
    else:
        render_url = os.getenv(RENDER_EXTERNAL_URL_ENV_VAR)
        if render_url and render_url.strip():
            base_url = render_url.strip().rstrip("/")
        else:
            raise RuntimeError(
                "Webhook mode requires WEBHOOK_BASE_URL or RENDER_EXTERNAL_URL."
            )

    if not base_url.startswith("https://"):
        raise RuntimeError(f"Webhook URL must use https. Got {base_url!r}.")

    return base_url


def get_host() -> str:
    return get_env(HOST_ENV_VAR, DEFAULT_HOST)


def get_port() -> int:
    raw_port = get_env(PORT_ENV_VAR, str(DEFAULT_PORT))
    try:
        return int(raw_port)
    except ValueError as exc:
        raise RuntimeError(f"Invalid {PORT_ENV_VAR}={raw_port!r}. Must be an integer.") from exc


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.message.register(handle_start, CommandStart())
    dp.message.register(handle_ping, Command("ping"))
    dp.message.register(handle_echo, F.text)
    return dp


async def run_polling(token: str) -> None:
    bot = Bot(token=token)
    dp = create_dispatcher()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except TelegramNetworkError as exc:
        logging.error("Network error while reaching Telegram API: %s", exc)
        logging.error(
            "If your local network blocks Telegram, run webhook mode on Render."
        )
        raise
    finally:
        await bot.session.close()


def create_webhook_app(token: str) -> web.Application:
    bot = Bot(token=token)
    dp = create_dispatcher()

    webhook_path = get_webhook_path()
    webhook_base_url = get_webhook_base_url()
    webhook_url = f"{webhook_base_url}{webhook_path}"
    secret_token_raw = os.getenv(WEBHOOK_SECRET_TOKEN_ENV_VAR)
    secret_token = secret_token_raw.strip() if secret_token_raw else None

    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "mode": RUN_MODE_WEBHOOK})

    async def root(_: web.Request) -> web.Response:
        return web.Response(text="Telegram bot webhook is running.")

    app.router.add_get("/", root)
    app.router.add_get("/health", health)

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        handle_in_background=True,
        secret_token=secret_token,
    )
    handler.register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    async def on_startup(_: web.Application) -> None:
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            secret_token=secret_token,
        )
        logging.info("Webhook set to %s", webhook_url)

    app.on_startup.append(on_startup)
    return app


def run() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    token = get_token()
    run_mode = get_run_mode()

    logging.info("Run mode: %s", run_mode)

    if run_mode == RUN_MODE_WEBHOOK:
        app = create_webhook_app(token=token)
        web.run_app(app, host=get_host(), port=get_port())
        return

    asyncio.run(run_polling(token=token))


if __name__ == "__main__":
    run()
