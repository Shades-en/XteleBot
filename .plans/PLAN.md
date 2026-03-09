# Master Plan

## Milestones
- [x] Create target package structure
- [x] Add shared config/constants/enums
- [x] Add Postgres schema and repositories
- [x] Add Telegram command and session routing foundation
- [x] Add twitter/search/agent/workflow package scaffolding
- [x] Add worker entrypoint and DB-backed job loop
- [ ] Validate full dependency install with `uv`
- [ ] Run migrations against the real database
- [ ] End-to-end test onboarding, analysis, and creator flows

## Sub Plans
- [db-and-schema.md](db-and-schema.md)
- [telegram-and-session-state.md](telegram-and-session-state.md)
- [twitter-ingestion-and-ranking.md](twitter-ingestion-and-ranking.md)
- [web-research-architecture.md](web-research-architecture.md)
- [content-creator-workflows.md](content-creator-workflows.md)
- [infra-jobs-and-observability.md](infra-jobs-and-observability.md)
