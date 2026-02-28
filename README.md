# Simple Telegram Bot (aiogram 3.25.0)

This bot supports two run modes:
- `polling` for local development
- `webhook` for free Render Web Service deployment

## Local setup

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
BOT_RUN_MODE=polling
WEBHOOK_BASE_URL=
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET_TOKEN=
```

4. Run locally:

```bash
uv run python main.py
```

Commands:
- `/start`
- `/ping`
- any text message is echoed

## Free Render deploy (Webhook mode)

Background workers are paid on Render. Use a free **Web Service** instead.

1. Push this repo to GitHub.
2. In Render, create service from this repo as a **Web Service** (or use Blueprint with `render.yaml`).
3. Use:

```bash
Build Command: pip install -r requirements.txt
Start Command: python main.py
```

4. Set environment variables in Render:

```bash
TELEGRAM_BOT_TOKEN=<your token>
BOT_RUN_MODE=webhook
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET_TOKEN=<random_secret_string>
```

5. Optional (if Render does not auto-provide `RENDER_EXTERNAL_URL`):

```bash
WEBHOOK_BASE_URL=https://<your-service>.onrender.com
```

6. Deploy. Check logs for:
- `Webhook set to https://.../telegram/webhook`

7. Open health check:
- `https://<your-service>.onrender.com/health`

## Notes

- If local network blocks Telegram, use Render webhook mode.
- Regenerate your bot token in BotFather if it was exposed.
