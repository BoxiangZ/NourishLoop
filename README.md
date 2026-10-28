# NourishLoop engineering foundation

NourishLoop helps students discover food and workouts, make a stage-aware choice, keep a record, and share confirmed meals in Community. Confirmed meals, voluntary shares and completed workouts build habit progress and earn demo credits for digital badges. The 35 HKUST and THE LOHAS venue records come from official directories; the six recordable demo meals remain fictional and their nutrition is illustrative.

This repository adapts the MAIE 6000C starter. The active app is the modular FastAPI monolith under `apps/api` and the Next.js frontend under `apps/web`. The former case/worker/AI code remains under `services/`; its AI service now has optional HKGAI text and Gemini image-draft adapters for the Week 4 diet-planning proposal. These adapters are separate from the active NourishLoop flow. The Week 4 persisted plan/meal workflow remains unimplemented. The old starter README is archived at [docs/legacy/starter-README.md](docs/legacy/starter-README.md).

## Structure

| Directory | Purpose |
|---|---|
| `apps/api` | Versioned FastAPI API, sourced place directory, workouts, worker, Community, habits and demo rewards |
| `apps/web` | Mobile-first Next.js interface with Discover, Workouts, For you, History, Community, Rewards and Profile screens |
| `packages/api-client` | OpenAPI snapshot, generated TypeScript schema types, fetch client |
| `alembic` | Historical starter migration plus NourishLoop product migrations |
| `scripts` | API type generation and idempotent fictional demo seed |
| `tests` | Backend unit and integration tests |
| `services` | Preserved starter example plus optional Week 4 HKGAI text adapter |

See [architecture overview](docs/architecture/overview.md), [data sources](docs/data-sources.md), [module boundaries](docs/architecture/modules.md), [database schema](docs/database/schema.md), [API contracts](docs/api/contracts.md), [onboarding](docs/development/onboarding.md), and [verification](docs/development/verification.md).

## Quick start with Docker

Prerequisites: Docker Desktop or compatible Docker Engine with Compose. Ports 3000, 8000, and 5432 must be available.

```bash
docker compose up --build
```

The API container applies Alembic migrations and loads the idempotent demo seed at startup. The worker starts after API health and processes persisted recommendation jobs and photo reviews. Open `http://localhost:3000` for the app, `http://localhost:8000/docs` for OpenAPI, and `http://localhost:8000/api/v1/health` for readiness. The first build downloads Python and Node dependencies. Stop with `docker compose down`. To delete the local demo database volume, use `docker compose down -v`.

## Local development

Prerequisites: Python 3.12, Node 22, pnpm 9.15.9, PostgreSQL 16. The Python dependency manager is `pip` with pinned top-level versions in `pyproject.toml`; a virtual environment is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d db
export DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/maie6000c'
export APP_ENV=development DEMO_AUTH_ENABLED=true
alembic upgrade head
python -m scripts.seed_nourishloop
uvicorn apps.api.main:app --reload --port 8000
```

In a second terminal, run `python -m apps.api.worker`. In another terminal:

```bash
npm install --global pnpm@9.15.9
pnpm install --frozen-lockfile
pnpm dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` if using a different API origin. For ports and other settings, see [.env.example](.env.example). The demo identity is only accepted when `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; production auth is not implemented, so private routes return 503 outside demo mode.

## Optional Week 4 AI service

Put the course keys in a local `.env` file as `HKG_API_KEY` and `GEMINI_API_KEY`; `.env` is ignored by Git. Model and address settings are in [.env.example](.env.example). Start the separate AI service with `docker compose --profile week4-ai up --build ai`, then open `http://localhost:8100/docs`. `POST /diet-plans/draft` writes review-required guidance around a **caller-supplied** target, `POST /meals/interpret-notes` extracts candidates from text, and `POST /meals/recognize` accepts a small base64 image plus optional notes and returns a review-required image draft. None of these endpoints stores a plan or meal or calculates nutrition. The optional historical worker handles starter case triage; the Week 4 plan/meal persistence workflow is not connected yet. See [adapter details](docs/architecture/week04-hkgai-adapter.md).

## Checks

```bash
python -m pytest -q tests/unit tests/integration
ruff check .
python -m scripts.generate_api_types
pnpm typecheck
pnpm lint
pnpm test:web
pnpm build
make smoke  # after the stack is running
```

Run type generation after changing a Pydantic request or response schema and commit both `packages/api-client/src/openapi.json` and `schema.ts`. The API contract is the source of truth. The generated schema is imported by the browser client in `packages/api-client/src/client.ts`.

## Troubleshooting

- If the page says the demo user is missing, run `python -m scripts.seed_nourishloop` against the same database as the API.
- If the API cannot connect to PostgreSQL, check whether `DATABASE_URL` uses `db` inside Compose and `localhost` on the host.
- If the web app cannot reach the API, check `NEXT_PUBLIC_API_URL` and port 8000. Browser calls require the origin configured in `CORS_ORIGIN`.
- If pnpm or pip cannot install, check network access. The repo includes generated API types, but a clean frontend build still needs Node dependencies.

## Current scope

The current UI and API implement paginated food and real-place discovery, one-click photo recognition with an immediate OpenRouter and USDA nutrition estimate, asynchronous meal recommendations, plan/confirmation tracking, stage-aware workout plans and session logs, paginated History and Community, posts/comments/likes/report review, daily and weekly habits, an auditable demo credit ledger, badge redemption, and editable demo profile/goals. Public Reddit discussions appear only as attributed paraphrases with source links. OpenRouter can optionally reword grounded meal explanations and workout coaching notes; exercise selection, sets and meal ranking remain rule based. Instant photo records store no image. Background reviews keep a metadata-free, resized photo temporarily until success or deletion; their AI visual estimate is shown separately and never enters daily totals. Complete source-backed estimates use matched USDA nutrient densities and visually estimated or user supplied edible grams, with an optional correction panel and a source/quantity snapshot. A bundled USDA SR Legacy index supports nutrition lookup when the public API is rate limited. If some sources or portions are unresolved, the app shows only a clearly labelled partial total for matched foods and excludes that partial total from History's daily nutrition. Photo records remain separate from menu meals and Community posts. Production authentication, verified restaurant menus/nutrition, production moderation, and commercial features remain future work. Recommendations never use merchant payments. See the [Week 7 checkpoint](submissions/week07/README.md), [current architecture](docs/architecture/overview.md), [operations](docs/operations.md), and [roadmap](docs/product/roadmap.md).
