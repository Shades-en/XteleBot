# Simple Telegram Bot (aiogram 3.25.0)

## 1) Install uv (required in this repo workflow)

```bash
brew install uv
```

## 2) Install dependencies

```bash
uv sync --dev
```

## 3) Configure token

Put your bot token in `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
BOT_ENV=development
TELEGRAM_DISABLE_SSL_VERIFY=false
TELEGRAM_PROXY=
```

Optional network troubleshooting:
- If your network requires an HTTPS proxy, set `TELEGRAM_PROXY` (for example `http://127.0.0.1:7890`).
- You can disable certificate verification for testing only: `TELEGRAM_DISABLE_SSL_VERIFY=true`.
- `TELEGRAM_DISABLE_SSL_VERIFY=true` is allowed only in `BOT_ENV=development`.
- `TELEGRAM_DISABLE_SSL_VERIFY=true` does not fix raw connectivity blocks; it only bypasses cert validation.

## 4) Run bot

```bash
uv run python main.py
```

Then message your bot in Telegram.

Commands:
- `/start`
- `/ping`
- Any text message is echoed.

## Development Deploy (Render worker)

Use this if your local network cannot access `api.telegram.org`.

1. Push this repo to GitHub.
2. In Render, create from Blueprint and select this repo (`render.yaml` is included).
3. In Render service env vars, set:
   - `TELEGRAM_BOT_TOKEN` = your token
   - keep `BOT_ENV=development`
   - keep `TELEGRAM_PROXY` empty unless your Render environment needs one
4. Start the worker.

The worker runs polling mode (`python main.py`) and is intended for development testing.
