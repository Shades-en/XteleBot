from typing import Final, Literal

BotEnv = Literal["development", "production"]

EMPTY_STRING: Final[str] = ""

# Environment keys
TOKEN_ENV_VAR: Final[str] = "TELEGRAM_BOT_TOKEN"
BOT_ENV_VAR: Final[str] = "BOT_ENV"
API_BASE_URL_ENV_VAR: Final[str] = "TELEGRAM_API_BASE_URL"
PROXY_TARGET_ENV_VAR: Final[str] = "TELEGRAM_PROXY_TARGET"
VERCEL_BYPASS_TOKEN_ENV_VAR: Final[str] = "VERCEL_BYPASS_TOKEN"

# Environment values/defaults
ENV_DEVELOPMENT: Final[BotEnv] = "development"
ENV_PRODUCTION: Final[BotEnv] = "production"
DEFAULT_API_BASE_URL: Final[str] = (
    "https://portfolio-git-proxy-owais-iqbals-projects-ae6a6135.vercel.app/proxy"
)
DEFAULT_PROXY_TARGET: Final[str] = "https://api.telegram.org"
ALLOWED_URL_PREFIXES: Final[tuple[str, str]] = ("http://", "https://")

# Commands
COMMAND_START: Final[str] = "start"
COMMAND_HELP: Final[str] = "help"
COMMAND_PING: Final[str] = "ping"
COMMAND_REPLYPOST: Final[str] = "replypost"
COMMAND_POST: Final[str] = "post"
COMMAND_SCHEDULE: Final[str] = "schedule"
COMMAND_TOP10: Final[str] = "top10"
COMMAND_TOP10FAV: Final[str] = "top10fav"
COMMAND_UPDATEFAV: Final[str] = "updatefav"
COMMAND_CONTENT_STYLE_CREATORS: Final[str] = "contentStyleCreators"
COMMAND_UPDATE_CONTENT_STYLE_CREATORS: Final[str] = "updateContentStyleCreators"

ACTION_COMMANDS: Final[list[tuple[str, str]]] = [
    (COMMAND_REPLYPOST, "Reply to a post (boilerplate)"),
    (COMMAND_POST, "Create a post (boilerplate)"),
    (COMMAND_SCHEDULE, "Schedule content (boilerplate)"),
    (COMMAND_TOP10, "Show top 10 (boilerplate)"),
    (COMMAND_TOP10FAV, "Show top 10 favorites (boilerplate)"),
    (COMMAND_UPDATEFAV, "Update favorites (boilerplate)"),
    (COMMAND_CONTENT_STYLE_CREATORS, "List content style creators (boilerplate)"),
    (
        COMMAND_UPDATE_CONTENT_STYLE_CREATORS,
        "Update content style creators (boilerplate)",
    ),
    (COMMAND_PING, "Ping bot"),
]

BOT_MENU_COMMANDS: Final[list[tuple[str, str]]] = [
    (COMMAND_START, "Show command panel"),
    (COMMAND_HELP, "Show command panel"),
    *ACTION_COMMANDS,
]

# User-facing text
TEXT_CHOOSE_COMMAND: Final[str] = "Choose a command:"
TEXT_PONG: Final[str] = "pong"
TEXT_UNRECOGNIZED_COMMAND: Final[str] = "Unrecognized command. Use /help."
TEXT_UNSUPPORTED_ACTION: Final[str] = "Unsupported action. Use /help."
TEXT_BOILERPLATE_TEMPLATE: Final[str] = "Boilerplate: /{command} not implemented yet."

# Logging text
LOG_POLLING_MODE_ENABLED: Final[str] = "Polling mode enabled"
LOG_BOT_ENV: Final[str] = "Bot env: %s"
LOG_TELEGRAM_API_BASE_URL: Final[str] = "Telegram API base URL: %s"
LOG_PROXY_TARGET: Final[str] = "Proxy target: %s"
LOG_VERCEL_BYPASS_TOKEN_STATUS: Final[str] = "Vercel bypass token: %s"
LOG_VERCEL_BYPASS_SET: Final[str] = "set"
LOG_VERCEL_BYPASS_NOT_SET: Final[str] = "not set"
LOG_DIRECT_API_MODE: Final[str] = "Using direct Telegram API (proxy disabled)"
LOG_PROXY_AUTH_PROTECTED: Final[str] = (
    "Proxy endpoint is protected by Vercel Authentication. "
    "Make the deployment public or configure Vercel protection bypass."
)
LOG_NETWORK_ERROR_WITH_PROXY: Final[str] = (
    "Network error while reaching Telegram API via %s: %s"
)
LOG_NETWORK_ERROR_DIRECT: Final[str] = "Network error while reaching Telegram API: %s"

# Error templates
ERR_MISSING_ENV_ADD_TEMPLATE: Final[str] = (
    "Missing {name}. Add it to .env or your shell environment."
)
ERR_MISSING_ENV_SET_TEMPLATE: Final[str] = (
    "Missing {name}. Set it in .env or shell environment."
)
ERR_INVALID_URL_TEMPLATE: Final[str] = (
    "Invalid {name}={value!r}. Must start with http:// or https://."
)
ERR_INVALID_BOT_ENV_TEMPLATE: Final[str] = (
    "Invalid {name}={value!r}. Use '{development}' or '{production}'."
)
ERR_DEV_PROXY_REQUIRED: Final[str] = "Development mode requires proxy settings."

# Proxy internals
HEADER_PROXY_TARGET: Final[str] = "x-proxy-target"
QUERY_BYPASS_COOKIE_KEY: Final[str] = "x-vercel-set-bypass-cookie"
QUERY_BYPASS_COOKIE_VALUE: Final[str] = "true"
QUERY_BYPASS_TOKEN_KEY: Final[str] = "x-vercel-protection-bypass"
PROXY_BOT_PATH_SUFFIX: Final[str] = "/bot{token}/{method}"
PROXY_FILE_PATH_SUFFIX: Final[str] = "/file/bot{token}/{path}"

# Detection text
VERCEL_AUTH_MARKER: Final[str] = "vercel authentication"
GENERIC_AUTH_REQUIRED_MARKER: Final[str] = "authentication required"
