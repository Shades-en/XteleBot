import asyncio
import logging
from contextlib import suppress
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

from telebot.agents.factory import AgnoFactory
from telebot.config import Settings, load_settings
from telebot.db.base import create_engine, create_session_factory
from telebot.db.bootstrap import create_schema
from telebot.telegram.handlers import TelegramHandlers
from telebot.telegram.menus import build_menu_commands
from telebot.telegram.router import register_handlers
from telebot.telegram.session import create_proxy_session
from telebot.twitter.client import TwitterApiClient
from telebot.worker.service import WorkerService
from telebot.workflows.admin import AdminWorkflowService
from telebot.workflows.cost_summary import CostSummaryWorkflowService
from telebot.workflows.creator import CreatorWorkflowService
from telebot.workflows.job_status import JobStatusWorkflowService
from telebot.workflows.onboarding import OnboardingWorkflowService
from telebot.workflows.schedule import ScheduleWorkflowService
from telebot.workflows.user_details import UserDetailsWorkflowService

HEALTHCHECK_PATH = "/healthz"
PORT_ENV_VAR = "PORT"
DEFAULT_PORT = 8000


def create_bot(settings: Settings) -> Bot:
    if settings.bot_env.value == "production":
        return Bot(
            token=settings.telegram_token,
            default=DefaultBotProperties(),
        )
    return Bot(
        token=settings.telegram_token,
        default=DefaultBotProperties(),
        session=create_proxy_session(
            settings.proxy_base_url,
            settings.proxy_target,
            settings.vercel_bypass_token,
        ),
    )


def create_dispatcher(handlers: TelegramHandlers) -> Dispatcher:
    dispatcher = Dispatcher()
    register_handlers(dispatcher, handlers)
    return dispatcher


def webhook_url(settings: Settings) -> str:
    return f"{settings.webhook_base_url}{settings.webhook_path}"


async def run_bot(settings: Settings) -> None:
    engine = create_engine(settings)
    if settings.auto_create_schema:
        await create_schema(engine, reset_schema=False)
    session_factory = create_session_factory(engine=engine)
    twitter_client = TwitterApiClient(settings.twitter_api_key)
    agno_factory = AgnoFactory(settings)
    worker_service = WorkerService(settings, session_factory)
    handlers = TelegramHandlers(
        session_factory=session_factory,
        onboarding_service=OnboardingWorkflowService(session_factory, twitter_client),
        creator_service=CreatorWorkflowService(session_factory, agno_factory),
        schedule_service=ScheduleWorkflowService(session_factory),
        user_details_service=UserDetailsWorkflowService(session_factory),
        cost_summary_service=CostSummaryWorkflowService(session_factory),
        job_status_service=JobStatusWorkflowService(session_factory),
        admin_service=AdminWorkflowService(settings, engine),
    )
    bot = create_bot(settings)
    dispatcher = create_dispatcher(handlers)
    app = web.Application()
    app["worker_task"] = None

    async def healthcheck(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def on_startup(_app: web.Application) -> None:
        await bot.set_my_commands(build_menu_commands())
        await bot.set_webhook(
            url=webhook_url(settings),
            secret_token=settings.webhook_secret_token,
            drop_pending_updates=False,
        )
        app["worker_task"] = asyncio.create_task(
            worker_service.run_forever(),
            name="analysis-background-loop",
        )

    async def on_shutdown(_app: web.Application) -> None:
        worker_task = app.get("worker_task")
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task
        with suppress(TelegramNetworkError):
            await bot.delete_webhook(drop_pending_updates=False)
        await twitter_client.close()
        await bot.session.close()
        await engine.dispose()

    app.router.add_get(HEALTHCHECK_PATH, healthcheck)
    request_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        handle_in_background=True,
        secret_token=settings.webhook_secret_token,
    )
    request_handler.register(app, path=settings.webhook_path)
    setup_application(app, dispatcher, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=int(load_port()),
    )
    try:
        await site.start()
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def load_port() -> str:
    return os.getenv(PORT_ENV_VAR, str(DEFAULT_PORT))


def run() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_bot(load_settings()))
