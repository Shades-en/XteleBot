"""Single source of truth for proxy-specific Telegram session behavior."""

from urllib.parse import urlencode

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from telebot.constants import (
    HEADER_PROXY_TARGET,
    PROXY_BOT_PATH_SUFFIX,
    PROXY_FILE_PATH_SUFFIX,
    QUERY_BYPASS_COOKIE_KEY,
    QUERY_BYPASS_COOKIE_VALUE,
    QUERY_BYPASS_TOKEN_KEY,
)


class ProxyTelegramSession(AiohttpSession):
    def __init__(self, api_server: TelegramAPIServer, proxy_target: str) -> None:
        super().__init__(api=api_server)
        self._proxy_target = proxy_target

    async def create_session(self):
        session = await super().create_session()
        session.headers[HEADER_PROXY_TARGET] = self._proxy_target
        return session


def build_api_server(api_base_url: str, vercel_bypass_token: str) -> TelegramAPIServer:
    base = f"{api_base_url}{PROXY_BOT_PATH_SUFFIX}"
    file = f"{api_base_url}{PROXY_FILE_PATH_SUFFIX}"

    if vercel_bypass_token:
        bypass_query = urlencode(
            {
                QUERY_BYPASS_COOKIE_KEY: QUERY_BYPASS_COOKIE_VALUE,
                QUERY_BYPASS_TOKEN_KEY: vercel_bypass_token,
            }
        )
        base = f"{base}?{bypass_query}"
        file = f"{file}?{bypass_query}"

    return TelegramAPIServer(base=base, file=file)


def create_proxy_session(
    api_base_url: str,
    proxy_target: str,
    vercel_bypass_token: str,
) -> ProxyTelegramSession:
    api_server = build_api_server(
        api_base_url=api_base_url,
        vercel_bypass_token=vercel_bypass_token,
    )
    return ProxyTelegramSession(api_server=api_server, proxy_target=proxy_target)
