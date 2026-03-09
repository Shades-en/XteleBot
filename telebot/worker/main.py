import asyncio
import logging

from dotenv import load_dotenv

from telebot.config import load_settings
from telebot.db.base import create_engine, create_session_factory
from telebot.db.bootstrap import create_schema
from telebot.worker.service import WorkerService


def run() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    engine = create_engine(settings)

    async def _main() -> None:
        if settings.auto_create_schema:
            await create_schema(engine)
        logging.info("Worker started")
        service = WorkerService(settings, create_session_factory(engine=engine))
        await service.run_forever()

    asyncio.run(_main())
