import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import ClientDecodeError, TelegramNetworkError
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
from telebot.workflows.creator import CreatorWorkflowService
from telebot.workflows.admin import AdminWorkflowService
from telebot.workflows.job_status import JobStatusWorkflowService
from telebot.workflows.onboarding import OnboardingWorkflowService
from telebot.workflows.schedule import ScheduleWorkflowService
from telebot.workflows.user_details import UserDetailsWorkflowService

VERCEL_AUTH_MARKER = "vercel authentication"
GENERIC_AUTH_REQUIRED_MARKER = "authentication required"
DEVELOPMENT_SCHEMA_RESET_LOG = "Development mode detected. Dropping and recreating app schema."


def create_bot(settings: Settings) -> Bot:
    if settings.bot_env.value == "production":
        return Bot(token=settings.telegram_token)
    return Bot(
        token=settings.telegram_token,
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


def is_vercel_auth_page(content: str) -> bool:
    lowered = content.lower()
    return VERCEL_AUTH_MARKER in lowered or GENERIC_AUTH_REQUIRED_MARKER in lowered


async def run_bot(settings: Settings) -> None:
    engine = create_engine(settings)
    if settings.auto_create_schema:
        await create_schema(
            engine,
            # reset_schema=settings.bot_env.value == "development",
            reset_schema=False,
        )
    session_factory = create_session_factory(engine=engine)
    twitter_client = TwitterApiClient(settings.twitter_api_key)
    agno_factory = AgnoFactory(settings)
    handlers = TelegramHandlers(
        session_factory=session_factory,
        onboarding_service=OnboardingWorkflowService(session_factory, twitter_client),
        creator_service=CreatorWorkflowService(session_factory, agno_factory),
        schedule_service=ScheduleWorkflowService(session_factory),
        user_details_service=UserDetailsWorkflowService(session_factory),
        job_status_service=JobStatusWorkflowService(session_factory),
        admin_service=AdminWorkflowService(settings, engine),
    )
    bot = create_bot(settings)
    dispatcher = create_dispatcher(handlers)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_my_commands(build_menu_commands())
        await dispatcher.start_polling(bot)
    except ClientDecodeError as exc:
        if is_vercel_auth_page(str(exc.data)):
            logging.error("Telegram proxy is behind Vercel auth.")
        raise
    except TelegramNetworkError:
        logging.exception("Telegram network error")
        raise
    finally:
        await twitter_client.close()
        await bot.session.close()
        await engine.dispose()


def run() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_bot(load_settings()))
