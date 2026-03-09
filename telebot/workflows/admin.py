from sqlalchemy.ext.asyncio import AsyncEngine

from telebot.common.enums import BotEnv
from telebot.common.messages import TEXT_RESET_SCHEMA_DENIED, TEXT_RESET_SCHEMA_DONE
from telebot.config import Settings
from telebot.db.bootstrap import reset_schema


class AdminWorkflowService:
    def __init__(self, settings: Settings, engine: AsyncEngine) -> None:
        self.settings = settings
        self.engine = engine

    async def reset_schema(self) -> str:
        if self.settings.bot_env is not BotEnv.DEVELOPMENT:
            return TEXT_RESET_SCHEMA_DENIED
        await reset_schema(self.engine)
        return TEXT_RESET_SCHEMA_DONE
