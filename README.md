# Simple Telegram Bot (aiogram 3.25.0)

Polling-only Telegram bot for local testing.

## Project layout

- `main.py` - thin launcher
- `telebot/constants.py` - shared constants (commands, text, env keys/defaults, log/error templates)
- `telebot/config.py` - settings parsing and validation
- `telebot/handlers.py` - message handlers and router registration
- `telebot/session.py` - single source of truth for proxy behavior
- `telebot/app.py` - bot creation, startup flow, and runtime logging/errors

## Setup

1. Install uv:

```bash
brew install uv
```

2. Install deps:

```bash
uv sync --dev
```

3. Configure `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
BOT_ENV=production
TELEGRAM_API_BASE_URL=https://portfolio-git-proxy-owais-iqbals-projects-ae6a6135.vercel.app/proxy
TELEGRAM_PROXY_TARGET=https://api.telegram.org
VERCEL_BYPASS_TOKEN=
```

- `BOT_ENV=development`: enables proxy mode and adds `x-proxy-target` header.
- `BOT_ENV=production`: disables proxy mode and uses direct Telegram API.
- If `BOT_ENV` is missing, default is `production`.
- `TELEGRAM_API_BASE_URL`, `TELEGRAM_PROXY_TARGET`, and `VERCEL_BYPASS_TOKEN` are used only in development mode.

4. Run:

```bash
uv run python main.py
```

Commands:
- `/start` and `/help` show an inline GUI command panel
- `/replypost`
- `/post`
- `/schedule`
- `/top10`
- `/top10fav`
- `/updatefav`
- `/contentStyleCreators`
- `/updateContentStyleCreators`
- `/ping`

Current boilerplate behavior:
- `/ping` replies `pong`
- other listed commands reply with a boilerplate placeholder
- unknown slash commands reply `Unrecognized command. Use /help.`
- plain non-command text is ignored

## Important

If the proxy URL returns a Vercel Authentication page (`401 Authentication Required`), the bot cannot work until you make that deployment public or configure Vercel protection bypass.
