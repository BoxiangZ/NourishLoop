# Developer onboarding

1. Read the root [README](../../README.md) and [module map](../architecture/modules.md).
2. Install Python 3.12 and Node 22. Start PostgreSQL with `docker compose up -d db`.
3. Create a Python virtual environment; run `pip install -e '.[dev]'`.
4. Set `DATABASE_URL` for localhost, run `alembic upgrade head`, then `python -m scripts.seed_nourishloop`.
5. Start `uvicorn apps.api.main:app --reload --port 8000` and inspect `http://localhost:8000/docs`.
6. Enable pnpm 9.15.9 with Corepack, run `pnpm install` and `pnpm dev`; visit `http://localhost:3000`.
7. Run backend tests, Ruff, frontend typecheck/lint/test/build, and regenerate API types after any contract change.

The quickest backend tour: `apps/api/main.py` composes routers, each module's `router.py` declares its routes, `service.py` implements workflows, `models.py` maps tables, `schemas.py` defines public JSON, and `recommendations/engine.py` contains pure ranking rules. The browser page is in `apps/web/src/features/dashboard`. The old `services/` tree is the untouched course starter example, not the current API entry point.

Demo data can be reseeded safely. If you need a clean local database, `docker compose down -v` deletes the Compose database volume. Do not use that command against a database holding data you need. Private routes require the seeded demo user and explicit development mode.
