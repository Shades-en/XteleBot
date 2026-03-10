import os
from dataclasses import dataclass

from telebot.common.constants import DEFAULT_PROXY_BASE_URL, DEFAULT_PROXY_TARGET
from telebot.common.enums import BotEnv

TOKEN_ENV_VAR = "TELEGRAM_BOT_TOKEN"
BOT_ENV_ENV_VAR = "BOT_ENV"
PROXY_BASE_URL_ENV_VAR = "TELEGRAM_API_BASE_URL"
PROXY_TARGET_ENV_VAR = "TELEGRAM_PROXY_TARGET"
VERCEL_BYPASS_ENV_VAR = "VERCEL_BYPASS_TOKEN"
POSTGRES_USER_ENV_VAR = "POSTGRES_USER"
POSTGRES_PASSWORD_ENV_VAR = "POSTGRES_PASSWORD"
POSTGRES_HOST_ENV_VAR = "POSTGRES_HOST"
POSTGRES_PORT_ENV_VAR = "POSTGRES_PORT"
POSTGRES_DBNAME_ENV_VAR = "POSTGRES_DBNAME"
POSTGRES_SSLMODE_ENV_VAR = "POSTGRES_SSLMODE"
TWITTER_API_KEY_ENV_VAR = "TWITTER_API_KEY"
BRAVE_SEARCH_API_KEY_ENV_VAR = "BRAVE_SEARCH_API_KEY"
OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"
WORKER_CHAT_ID_ENV_VAR = "WORKER_CHAT_ID"
AUTO_CREATE_SCHEMA_ENV_VAR = "AUTO_CREATE_SCHEMA"


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    bot_env: BotEnv
    proxy_base_url: str | None
    proxy_target: str | None
    vercel_bypass_token: str
    postgres_url: str
    agno_postgres_url: str
    twitter_api_key: str
    brave_search_api_key: str
    openai_api_key: str
    auto_create_schema: bool


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name}. Set it in .env or the shell environment.")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _load_env() -> BotEnv:
    raw = _optional(BOT_ENV_ENV_VAR, BotEnv.PRODUCTION.value).lower()
    try:
        return BotEnv(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid {BOT_ENV_ENV_VAR}={raw!r}. Use development or production."
        ) from exc


def _build_postgres_url(driver_name: str) -> str:
    user = _required(POSTGRES_USER_ENV_VAR)
    password = _required(POSTGRES_PASSWORD_ENV_VAR)
    host = _required(POSTGRES_HOST_ENV_VAR)
    port = _required(POSTGRES_PORT_ENV_VAR)
    dbname = _required(POSTGRES_DBNAME_ENV_VAR)
    sslmode = _optional(POSTGRES_SSLMODE_ENV_VAR, "require")
    return (
        f"postgresql+{driver_name}://{user}:{password}@{host}:{port}/{dbname}"
        f"?sslmode={sslmode}"
    )


def load_settings() -> Settings:
    bot_env = _load_env()
    proxy_base_url = None
    proxy_target = None
    if bot_env is BotEnv.DEVELOPMENT:
        proxy_base_url = _optional(PROXY_BASE_URL_ENV_VAR, DEFAULT_PROXY_BASE_URL)
        proxy_target = _optional(PROXY_TARGET_ENV_VAR, DEFAULT_PROXY_TARGET)

    return Settings(
        telegram_token=_required(TOKEN_ENV_VAR),
        bot_env=bot_env,
        proxy_base_url=proxy_base_url,
        proxy_target=proxy_target,
        vercel_bypass_token=_optional(VERCEL_BYPASS_ENV_VAR),
        postgres_url=_build_postgres_url("psycopg_async"),
        agno_postgres_url=_build_postgres_url("psycopg_async"),
        twitter_api_key=_required(TWITTER_API_KEY_ENV_VAR),
        brave_search_api_key=_required(BRAVE_SEARCH_API_KEY_ENV_VAR),
        openai_api_key=_required(OPENAI_API_KEY_ENV_VAR),
        auto_create_schema=_optional(AUTO_CREATE_SCHEMA_ENV_VAR, "true").lower()
        == "true",
    )
