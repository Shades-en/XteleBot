# AGENTS.md

## Purpose
- This repository is a Telegram copilot for X content research and draft generation.
- It runs as a single process:
  - `main.py` starts the Telegram bot, registers commands, and hosts the background analysis loop in-process.
- The bot is not a generic chat assistant. The product is deterministic application logic wrapped around targeted LLM use.

## First Read For A New Agent
- Read [README.md](README.md) for the high-level product summary.
- Read [telebot/app.py](telebot/app.py) to understand bot composition.
- Read [telebot/worker/service.py](telebot/worker/service.py) to understand job execution and progress reporting.
- Read [telebot/telegram/handlers.py](telebot/telegram/handlers.py) and [telebot/telegram/router.py](telebot/telegram/router.py) for command wiring.
- Read [telebot/workflows/analysis/__init__.py](telebot/workflows/analysis/__init__.py) for the main workflow graph.
- Read [telebot/common/constants.py](telebot/common/constants.py), [telebot/common/enums.py](telebot/common/enums.py), [telebot/common/messages.py](telebot/common/messages.py), and [telebot/common/commands.py](telebot/common/commands.py) before adding new reusable literals.

## Runtime And Setup
- Package manager and runtime: `uv`, Python 3.11+.
- Install dependencies with `uv sync --dev`.
- Run the app with `uv run python main.py`.
- Use `.env` for local secrets and keep `.env.example` aligned for any new environment variables.
- The current stack uses:
  - `aiogram` for Telegram interactions
  - `SQLAlchemy` async + Postgres for persistence
  - `Agno` agents/workflows for classification, planning, synthesis, and drafting
  - `twitterapi.io` for X data
  - Brave LLM Context for web research
  - OpenAI embeddings and chat models through Agno/OpenAI SDKs

## Mental Model
- Telegram handlers should stay thin. They validate request state, enqueue work, or delegate to workflow services.
- Workflow services own command behavior and orchestration.
- The in-process background analysis loop owns long-running analysis jobs and progress notifications.
- Repositories own persistence reads/writes that are reused or non-trivial.
- LLMs are used for classification, planning, synthesis, and content creation, not for routing correctness or persistence decisions.
- Shared literals and user-facing copy belong in common modules, not inline inside workflows.

## Current User Flow
1. `/start` begins onboarding and asks for an X username.
2. Onboarding verifies the username through the Twitter client and stores user/session state.
3. `/analysetoday` queues a job.
4. The background analysis loop runs the analysis workflow:
   - collect posts
   - rank posts
   - classify top posts
   - fetch reply context
   - run web research
   - synthesize grounded recommendations
5. `/postbyinspiration`, `/quote`, or `/comment` uses the ranked and researched posts to generate a draft.
6. Follow-up user messages can refine the active draft session.

## Repository Map
- `main.py`
  - Thin process entrypoint only. Keep it trivial.
- `telebot/app.py`
  - Bot composition root. Creates settings, engine, services, bot session, dispatcher, polling loop, and background analysis loop.
- `telebot/worker/`
  - In-process background analysis loop and job processor.
- `telebot/common/`
  - Shared constants, enums, command metadata, and user-visible text.
- `telebot/config/`
  - Environment loading and `Settings` only.
- `telebot/telegram/`
  - Router, handlers, menus, and development proxy session wiring.
- `telebot/workflows/`
  - Command-facing orchestration services and analysis workflow executors.
- `telebot/workflows/analysis/`
  - Step executors for the main analysis pipeline.
- `telebot/db/`
  - SQLAlchemy base/models/bootstrap plus typed DB schemas and repositories.
- `telebot/db/repositories/`
  - Reusable persistence operations. Prefer adding logic here over duplicating ORM queries.
- `telebot/twitter/`
  - X client, provider schemas, and query builders.
- `telebot/search/`
  - Search planning, Brave retrieval, candidate dedupe, embedding-based reranking, and workflow wrapper.
- `telebot/agents/`
  - Agno agent factory and structured output schemas.
- `telebot/prompts/`
  - Prompt text only. No orchestration logic.
- `alembic/`
  - Migration assets. Do not mix migration work with ad hoc schema resets casually.
- `.plans/`
  - Local planning artifacts.

## Non-Negotiable Structure Rules
- Do not dump business logic into `main.py` or `telebot/app.py`.
- Keep source files focused. Target under 200 lines where practical; 250 lines is the hard limit.
- Reuse the existing module split before creating new packages.
- Keep constants in [telebot/common/constants.py](telebot/common/constants.py).
- Keep enums in [telebot/common/enums.py](telebot/common/enums.py).
- Keep user-facing messages in [telebot/common/messages.py](telebot/common/messages.py).
- Keep command labels/menu metadata in [telebot/common/commands.py](telebot/common/commands.py).
- Do not introduce reusable raw literals directly into handlers, workflows, or repositories.
- Avoid direct cross-feature imports when a shared module already exists.

## How To Add Or Change Features

### Add A Telegram Command
- Add the enum in [telebot/common/enums.py](telebot/common/enums.py).
- Add descriptions, button labels, and menu inclusion in [telebot/common/commands.py](telebot/common/commands.py).
- Add user-facing copy in [telebot/common/messages.py](telebot/common/messages.py).
- Implement or extend a workflow service in `telebot/workflows/`.
- Wire the handler in [telebot/telegram/handlers.py](telebot/telegram/handlers.py).
- Register slash-command and callback behavior in [telebot/telegram/router.py](telebot/telegram/router.py).
- Shared behavior must be reused between slash commands and inline buttons.

### Add Background Work
- Queue it from handlers through `JobRepository`; do not perform long-running work in the bot request path.
- Implement execution in [telebot/worker/service.py](telebot/worker/service.py) or a dedicated background-loop helper.
- Use the existing progress stage model and send user-visible progress updates through the background notifier path.

### Add Analysis Workflow Logic
- Keep it in `telebot/workflows/analysis/` as a dedicated executor or helper, not inside handlers.
- Compose it into [telebot/workflows/analysis/__init__.py](telebot/workflows/analysis/__init__.py).
- Prefer deterministic step ordering and explicit data passing through `StepInput.additional_data`.
- Report progress through `AnalysisContext.progress_callback`, not ad hoc Telegram calls.

### Add Persistence Logic
- Prefer repository methods in `telebot/db/repositories/`.
- Keep SQLAlchemy async usage consistent with the existing session factory pattern.
- Reuse typed DB schemas in `telebot/db/schemas.py` where possible.
- When building dictionaries from fetched rows, prefer `.get(...)` or explicit guards over assuming keys exist.

### Add Prompting Or LLM Output
- Put prompt text in `telebot/prompts/`.
- Put agent construction and shared model wiring in [telebot/agents/factory.py](telebot/agents/factory.py).
- Put machine-consumed outputs in Pydantic schemas under `telebot/agents/` or `telebot/search/`.
- Keep control flow outside the prompt. The model should not decide whether persistence, routing, or status transitions occur.

## Search And Research Rules
- Brave LLM Context is the primary retrieval source. Do not reintroduce general HTML scraping or alternate providers into the main path without an explicit architecture change.
- Skip blocked social domains such as `x.com`, `twitter.com`, `t.co`, `facebook.com`, `instagram.com`, `linkedin.com`, and `threads.net`.
- Within one research run, do not re-query or re-rank the same URL more than once.
- Preserve merged query provenance when duplicate search candidates collapse to one canonical URL.
- Carry normalized source dates through research evidence and into persisted `related_sources`.
- Keep `content_excerpts` as a list and keep `similarity_scores` aligned by index.
- Maintain the current two-stage reranking approach:
  - title-prefilter first
  - excerpt scoring second
- Use one embedding call for `query_text + all titles` in the title stage, then reuse the same query embedding in excerpt scoring.
- Trim candidates to the excerpt token budget before excerpt scoring.
- Search failures should degrade to structured fallback results, not raw provider errors shown to the user.

## Agno And Multimodal Rules
- Use Agno Workflow 2.0 patterns already present in the repo.
- Prefer class-based step executors.
- Use structured Pydantic output whenever downstream code consumes the result.
- When image inspection matters, attach images as multimodal inputs such as `Image(url=...)`; do not only paste image URLs into prompt text.
- Keep reusable research tooling in `telebot/search/` and reusable agent construction in `telebot/agents/`.

## Telegram Rules
- Canonical command names are lowercase only.
- For callback actions, use the actor from `callback.from_user`, not `callback.message.from_user`.
- Keep handlers thin and predictable.
- Non-command text should only be treated as meaningful when the current session status expects it, such as onboarding or draft refinement.

## Environment And Proxy Rules
- Development proxy behavior must stay isolated in [telebot/telegram/session.py](telebot/telegram/session.py).
- Do not duplicate proxy URL, header, or bypass logic anywhere else.
- `BOT_ENV=development` enables proxy setup in the bot and background notification path.
- `AUTO_CREATE_SCHEMA=true` currently causes schema creation on app startup.
- Schema reset behavior belongs in [telebot/db/bootstrap.py](telebot/db/bootstrap.py).
- Do not make the background analysis loop auto-drop schema on startup unless explicitly requested.

## Database And Schema Rules
- Postgres is the source of truth.
- Use SQLAlchemy async patterns already established here.
- Schema bootstrap and reset helpers live in [telebot/db/bootstrap.py](telebot/db/bootstrap.py).
- Prefer repository operations over direct ORM access in handlers and workflows when logic could be reused.
- Be careful with dev-only schema reset paths; they are destructive by design.

## Existing Commands
- `/start`
- `/help`
- `/ping`
- `/currentuser`
- `/jobstatus`
- `/reset_schema`
- `/analysetoday`
- `/reanalysefortoday`
- `/postbyinspiration`
- `/quote`
- `/comment`
- `/schedule`

## Environment Variables In Use
- Telegram:
  - `TELEGRAM_BOT_TOKEN`
  - `BOT_ENV`
  - `TELEGRAM_API_BASE_URL`
  - `TELEGRAM_PROXY_TARGET`
  - `VERCEL_BYPASS_TOKEN`
- Postgres:
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_DBNAME`
  - `POSTGRES_SSLMODE`
- External APIs:
  - `TWITTER_API_KEY`
  - `BRAVE_SEARCH_API_KEY`
  - `OPENAI_API_KEY`
- Runtime:
  - `AUTO_CREATE_SCHEMA`

## Validation Before Finishing
- At minimum run:
  - `.venv/bin/python -m py_compile main.py $(find telebot -name '*.py' -type f | tr '\n' ' ')`
- When you change behavior meaningfully, also run the most relevant `uv run` command path or targeted sanity checks.
- If you add or change environment variables, update `.env.example`.
- If you add dependencies, update `pyproject.toml` and keep `uv.lock` consistent.

## Common Pitfalls
- Do not perform heavy analysis directly inside Telegram handlers.
- Do not bypass repositories with one-off ORM logic in multiple places.
- Do not invent new raw status strings, command names, or progress labels inline.
- Do not let the model silently decide whether a user is onboarded, whether analysis exists, or whether a job succeeded.
- Do not expose raw provider failures to the user when a controlled fallback exists.
- Do not return raw X post IDs when a full status URL is available.
- Do not commit secrets or real token values.

## Definition Of A Good Change Here
- The change fits the existing package boundaries.
- User-facing behavior is deterministic and clear.
- Shared literals live in the common modules.
- Long-running work is delegated to the in-process background analysis loop when appropriate.
- LLM outputs are structured when code consumes them.
- Validation was run and any gaps were stated explicitly.
