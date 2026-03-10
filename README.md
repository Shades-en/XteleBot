# X Content Copilot

Telegram bot plus worker for X research and content drafting.

## Run Model

Two processes are expected:
- `python main.py` for the Telegram bot
- `python worker.py` for background analysis jobs

## Package Layout

- `telebot/common/` shared enums, constants, text, commands
- `telebot/config/` environment settings
- `telebot/db/` models, repositories, schema bootstrap
- `telebot/telegram/` bot handlers, menu, proxy session
- `telebot/twitter/` twitterapi.io client, schemas, queries
- `telebot/search/` Brave LLM Context search orchestration
- `telebot/agents/` Agno factory and learning config
- `telebot/workflows/` onboarding, schedule, analysis, creator flows
- `telebot/worker/` dedicated async worker loop
- `.plans/` implementation tracking plans

## Commands

- `/start`
- `/help`
- `/ping`
- `/pingworker`
- `/currentuser`
- `/jobstatus`
- `/reset_schema` (development only)
- `/analysetoday`
- `/reanalysefortoday`
- `/postbyinspiration`
- `/quote`
- `/comment`
- `/schedule`

## Command Behavior

- `/analysetoday`
  - queues the analysis workflow and sends progress updates as it moves through collection, ranking, classification, reply fetching, research, and synthesis
- `/reanalysefortoday`
  - deletes today's analysis rows for the current Telegram user and reruns the workflow from scratch
- `/postbyinspiration`, `/quote`, `/comment`
  - acknowledge immediately
  - send a second progress message while drafting
  - use today's grounded analysis as source context
- `/pingworker`
  - verifies that the background worker is alive by round-tripping a lightweight job through the queue
- `/jobstatus`
  - shows the latest job state and stored API cost summary

## Environment

Use `.env` for local secrets and `.env.example` as the template.

Key groups:
- Telegram: `TELEGRAM_BOT_TOKEN`, `BOT_ENV`, proxy settings for development
- Postgres: `POSTGRES_*`
- APIs: `TWITTER_API_KEY`, `BRAVE_SEARCH_API_KEY`, `OPENAI_API_KEY`

## Setup

1. Install `uv`.
2. Run `uv sync --dev`.
3. Start the bot:
   - `uv run python main.py`
4. Start the worker:
   - `uv run python worker.py`

## Notes

- Development mode uses the Telegram proxy only from `telebot/telegram/session.py`.
- The bot process auto-creates schema on startup when `AUTO_CREATE_SCHEMA=true`.
- In `BOT_ENV=development`, use `/reset_schema` or `/reanalysefortoday` when you want to clear dev data deliberately.
- Analysis completion and failure messages include API-only cost reporting for OpenAI, Brave, and TwitterAPI.io.
- Alembic files are included for migration management.
- The credentials and tokens currently present in chat history should be rotated if this thread is not private.

## Notes On Search

- Reusable web search uses Brave LLM Context as the primary retrieval source.
- Cross-query ranking is done in two stages before synthesis:
  - title prefiltering against the post-level query intent
  - excerpt scoring with a bounded excerpt token budget
- `pypdf` remains available for optional PDF fallback work, but HTML scraping is not in the mainline path.

## Notes On Creator Drafts

- `/postbyinspiration` targets roughly `600-800` characters.
- `/quote` targets roughly `200-400` characters.
- `/comment` targets under `100` characters.
- Creator drafts are instructed to open clearly, sound human, and avoid flat informational tone.
