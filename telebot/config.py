import os
from dataclasses import dataclass

from telebot.constants import (
    ALLOWED_URL_PREFIXES,
    API_BASE_URL_ENV_VAR,
    BOT_ENV_VAR,
    DEFAULT_API_BASE_URL,
    DEFAULT_PROXY_TARGET,
    EMPTY_STRING,
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ERR_INVALID_BOT_ENV_TEMPLATE,
    ERR_INVALID_URL_TEMPLATE,
    ERR_MISSING_ENV_ADD_TEMPLATE,
    ERR_MISSING_ENV_SET_TEMPLATE,
    PROXY_TARGET_ENV_VAR,
    TOKEN_ENV_VAR,
    VERCEL_BYPASS_TOKEN_ENV_VAR,
    BotEnv,
)

URL_SEPARATOR = "/"


@dataclass(frozen=True)
class Settings:
    token: str
    bot_env: BotEnv
    api_base_url: str | None
    proxy_target: str | None
    vercel_bypass_token: str


def _require_non_empty(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(ERR_MISSING_ENV_ADD_TEMPLATE.format(name=name))
    return value.strip()


def _validate_http_url(name: str, value: str) -> str:
    normalized = value.strip().rstrip(URL_SEPARATOR)
    if not normalized:
        raise RuntimeError(ERR_MISSING_ENV_SET_TEMPLATE.format(name=name))
    if not normalized.startswith(ALLOWED_URL_PREFIXES):
        raise RuntimeError(ERR_INVALID_URL_TEMPLATE.format(name=name, value=normalized))
    return normalized


def load_settings() -> Settings:
    token = _require_non_empty(TOKEN_ENV_VAR)

    raw_env = os.getenv(BOT_ENV_VAR, ENV_PRODUCTION).strip().lower()
    if raw_env not in {ENV_DEVELOPMENT, ENV_PRODUCTION}:
        raise RuntimeError(
            ERR_INVALID_BOT_ENV_TEMPLATE.format(
                name=BOT_ENV_VAR,
                value=raw_env,
                development=ENV_DEVELOPMENT,
                production=ENV_PRODUCTION,
            )
        )

    bot_env: BotEnv
    if raw_env == ENV_DEVELOPMENT:
        bot_env = ENV_DEVELOPMENT
    else:
        bot_env = ENV_PRODUCTION

    if bot_env == ENV_PRODUCTION:
        return Settings(
            token=token,
            bot_env=bot_env,
            api_base_url=None,
            proxy_target=None,
            vercel_bypass_token=EMPTY_STRING,
        )

    api_base_url = _validate_http_url(
        API_BASE_URL_ENV_VAR,
        os.getenv(API_BASE_URL_ENV_VAR, DEFAULT_API_BASE_URL),
    )
    proxy_target = _validate_http_url(
        PROXY_TARGET_ENV_VAR,
        os.getenv(PROXY_TARGET_ENV_VAR, DEFAULT_PROXY_TARGET),
    )
    vercel_bypass_token = os.getenv(VERCEL_BYPASS_TOKEN_ENV_VAR, EMPTY_STRING).strip()

    return Settings(
        token=token,
        bot_env=bot_env,
        api_base_url=api_base_url,
        proxy_target=proxy_target,
        vercel_bypass_token=vercel_bypass_token,
    )
