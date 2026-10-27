# Agent guidance

Active NourishLoop code is in `apps/api`, `apps/web`, and `packages/api-client`. `services/` and the root `docs/architecture.md` are preserved course history; do not treat them as the active product architecture. Do not erase historical Week 4 submission files.

Maintain the modular monolith: HTTP handlers validate and delegate, domain services own workflows, persistence stays in model/query code, and the pure recommendation engine cannot depend on providers or merchant payments. A recommendation is a suggestion, a decision is a planned meal, and only a confirmed meal log counts as consumed. Seeded venues and nutrition are fictional and must remain labelled that way.

When changing Pydantic contracts, run `python -m scripts.generate_api_types` and update the client and docs. Add Alembic migrations for schema changes. Run available backend and frontend checks. Demo identity must only operate with `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; never add a production bypass. Prefer small coherent changes and update documentation to match actual code.
