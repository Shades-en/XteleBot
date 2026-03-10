# AGENTS.md

## Scope
- These rules apply to the `/Users/5155106/mystuff/bots/telebot` repository.
- They extend the global `~/.codex/AGENTS.md` rules with project-specific requirements.

## Runtime Model
- This project uses `uv` and `pyproject.toml`.
- Preferred commands:
  - `uv sync --dev`
  - `uv run python main.py`
  - `uv run python worker.py`
- The app currently has a two-process runtime:
  - `main.py` handles Telegram polling and command routing
  - `worker.py` handles queued background jobs like `/analysetoday`
- Do not collapse worker behavior into `main.py` unless the user explicitly asks for that architectural change.

## Repository Architecture
- Keep code separated by package responsibility:
  - `telebot/common/` shared constants, enums, command labels, user-facing messages
  - `telebot/config/` environment loading and settings only
  - `telebot/db/` SQLAlchemy models, schema bootstrap, repositories
  - `telebot/telegram/` aiogram handlers, menu wiring, router, Telegram proxy session
  - `telebot/twitter/` twitterapi.io client, queries, schemas
  - `telebot/search/` web-search orchestration and evidence processing
  - `telebot/agents/` Agno factory and agent construction
  - `telebot/workflows/` command workflows and orchestration services
  - `telebot/prompts/` prompt text only
  - `telebot/worker/` background worker loop and job execution

## Non-Negotiable Structure Rules
- Do not dump new logic into `main.py`, `worker.py`, or `telebot/app.py`.
- Keep each source file under 200 lines where practical; 250 lines is the hard cap.
- Keep constants in `telebot/common/constants.py`.
- Keep enums in `telebot/common/enums.py`.
- Keep user-facing text in `telebot/common/messages.py`.
- Keep command labels and Telegram menu metadata in `telebot/common/commands.py`.
- Do not add reusable raw literals directly in business logic if they belong in one of the shared modules above.
- A file should contain only closely related code with one clear responsibility.

## Proxy And Environment Rules
- Telegram proxy behavior is development-only.
- Telegram proxy implementation must stay isolated in `telebot/telegram/session.py`.
- Do not duplicate proxy URL/header/bypass logic elsewhere in the repo.
- `BOT_ENV=development` currently implies app-schema reset on `main.py` startup when `AUTO_CREATE_SCHEMA=true`.
- Do not make `worker.py` auto-drop schema on startup unless the user explicitly asks for that behavior.

## Database Rules
- Postgres is the primary database.
- Use SQLAlchemy async patterns already established in the repo.
- Prefer repository methods in `telebot/db/repositories/` over direct ORM queries in handlers/workflows when reuse is likely.
- Schema reset logic belongs in `telebot/db/bootstrap.py`.

## Agno Rules
- Use Agno Workflow 2.0 patterns only.
- Use class-based executors for workflow steps.
- Use structured outputs with Pydantic where outputs are machine-consumed.
- Keep reusable web-search orchestration in `telebot/search/`; do not scatter retrieval logic across unrelated modules.
- For image/media input to Agno agents, do not pass image URLs only as plain text in prompts when visual inspection is required.
- Pass images using Agno multimodal input objects such as `images=[Image(url=...)]` or the equivalent supported media argument for the agent/team call.
- When combining structured output with image analysis, prefer attaching the output schema to the agent and sending media through the `images=` argument.

## Search Rules
- During per-post research, do not re-query or re-rank the same URL more than once within the same run.
- Brave LLM Context is the primary retrieval source. Do not reintroduce Serper or Trafilatura into the mainline retriever without an explicit architectural change.
- Keep evidence grouped by URL and preserve merged query provenance across duplicate results.
- Parse Brave `sources[url].age` and carry the normalized `source_date` through search evidence into persisted `related_sources`.
- Skip social links that are not useful research targets, including:
  - `x.com`
  - `twitter.com`
  - `t.co`
  - `facebook.com`
  - `fb.com`
  - `instagram.com`
  - `linkedin.com`
  - `threads.net`
- Use a two-stage Brave evidence selection flow:
  - title-prefilter first
  - excerpt scoring second
- In the title-prefilter stage, embed `query_text` and all candidate titles in one embedding call, then reuse that same query embedding for the excerpt stage.
- In the excerpt stage, embed only merged `title + excerpt` texts. Do not re-embed the query there.
- Keep `content_excerpts` as a list and keep `similarity_scores` aligned 1:1 with that list by index.
- Enforce the configured excerpt token budget before excerpt scoring by removing the lowest title-similarity candidates until the total excerpt tokens fit.
- Search fallbacks should degrade cleanly to structured empty-evidence results rather than surfacing raw provider errors to the user.

## Telegram Rules
- Canonical Telegram commands are lowercase only.
- Inline button callbacks must use the real actor from `callback.from_user`, not `callback.message.from_user`.
- Shared command behavior should live in workflow services and be reused by both slash commands and callback buttons.

## Development And Validation
- Before finishing Python changes, run at minimum:
  - `.venv/bin/python -m py_compile main.py worker.py $(find telebot -name '*.py' -type f | tr '\n' ' ')`
- If dependency changes are made, update `pyproject.toml` and keep `.env.example` aligned for any new environment variables.
- Never commit real secret values. Keep `.env.example` keys only.

## Project Conventions
- Prefer deterministic application behavior over letting the model decide control flow.
- Use LLMs for planning, drafting, classification, and synthesis, not for routing or persistence correctness.
- When returning source references to the user for X posts, prefer full X status URLs over raw post IDs.
