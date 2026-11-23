# NourishLoop engineering foundation

NourishLoop helps students discover food and workouts, make a stage-aware choice, keep a record, and share confirmed meals in Community. Confirmed meals, voluntary shares and completed workouts build habit progress and earn demo credits for digital badges. The 35 HKUST and THE LOHAS venue records come from official directories; the six recordable demo meals remain fictional and their nutrition is illustrative.

This repository adapts the MAIE 6000C starter. The active app is the modular FastAPI monolith under `apps/api` and the Next.js frontend under `apps/web`. The former case/worker/AI code remains under `services/`; its AI service now has optional HKGAI text and Gemini image-draft adapters for the Week 4 diet-planning proposal. These adapters are separate from the active NourishLoop flow. The Week 4 persisted plan/meal workflow remains unimplemented. The old starter README is archived at [docs/legacy/starter-README.md](docs/legacy/starter-README.md).

## Structure

| Directory | Purpose |
|---|---|
| `apps/api` | Versioned FastAPI API, DeepSeek assistant, sourced place directory, workouts, worker, Community, habits and demo rewards |
| `apps/web` | Mobile-first Next.js interface with Today, Food, Move, Progress and Community destinations, plus Rewards and Profile utilities |
| `packages/api-client` | OpenAPI snapshot, generated TypeScript schema types, fetch client |
| `alembic` | Historical starter migration plus NourishLoop product migrations |
| `scripts` | API type generation and idempotent fictional demo seeds |
| `tests` | Backend unit and integration tests |
| `services` | Preserved starter example plus optional Week 4 HKGAI text adapter |

See [architecture overview](docs/architecture/overview.md), [data sources](docs/data-sources.md), [module boundaries](docs/architecture/modules.md), [database schema](docs/database/schema.md), [API contracts](docs/api/contracts.md), [onboarding](docs/development/onboarding.md), and [verification](docs/development/verification.md).

## Quick start with Docker

Prerequisites: Docker Desktop or compatible Docker Engine with Compose. Ports 3000, 8000, and 5432 must be available.

```bash
docker compose up --build
```

The API container applies Alembic migrations, loads the base demo seed, then loads seven local days of fictional activity for `demo-student` before startup. Re-running the activity seed on the same Hong Kong day is idempotent. The worker starts after API health and processes persisted recommendation jobs and photo reviews. Open `http://localhost:3000` for the app, `http://localhost:8000/docs` for OpenAPI, and `http://localhost:8000/api/v1/health` for readiness. The first build downloads Python and Node dependencies. Stop with `docker compose down`. To delete the local demo database volume, use `docker compose down -v`.

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
python -m scripts.seed_demo_activity
uvicorn apps.api.main:app --reload --port 8000
```

In a second terminal, run `python -m apps.api.worker`. In another terminal:

```bash
npm install --global pnpm@9.15.9
pnpm install --frozen-lockfile
pnpm dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` if using a different API origin. For ports and other settings, see [.env.example](.env.example). The demo identity is only accepted when `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; production auth is not implemented, so private routes return 503 outside demo mode.

## Floating DeepSeek coach

The floating coach and the report in **Progress** need a non-empty server-side `DEEPSEEK_API_KEY`; without it, both assistant endpoints return 503. The settings are independent of OpenRouter:

| Setting | Default | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | unset | Required API credential; keep it in the untracked local `.env` |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Chat Completions base URL |
| `DEEPSEEK_MODEL` | `deepseek-flash` | Model used for conversational answers and reports |
| `DEEPSEEK_TIMEOUT_SECONDS` | `25` | Per-action upstream timeout |

When running the API directly from the repository root, the settings above can be placed in `.env` before starting `uvicorn`. The Compose API service also forwards all four `DEEPSEEK_*` values from `.env`, using the defaults shown above when they are absent.

The bottom-right **Coach** ring opens a textured blurred overlay containing one current question and at most one answer. It sends no prior question, answer, or conversation history. Closing it, asking another question, or refreshing the page clears the visible exchange. Optional browser speech recognition fills the text field when the browser exposes `SpeechRecognition` or `webkitSpeechRecognition`; the text input and send button remain available when speech is unsupported, denied, stopped, or fails.

Each **Send question** or **Generate daily coach report** action makes at most one DeepSeek request. There is no automatic backend or frontend retry; a failed action can be retried explicitly by the user. Answers and reports are validated, rendered as text rather than HTML, and never persisted in PostgreSQL, browser storage, or cookies. Application logs omit the question, health context, generated answer or report, raw upstream body, Authorization header, and API key. Refreshing, navigating away, or remounting removes the report. No migration or assistant history table exists.

The question prompt requests two to four natural conversational sentences with no headings, bullets, tables, Markdown bold, labels, or label-value formatting. The response contract permits a nonblank plain-text answer of up to 1000 characters; the sentence count and formatting are prompt guidance rather than runtime validation.

**Progress** owns full report generation and display. The assistant receives only the current question plus a read-only context allowlist. Current-day intake includes confirmed menu meals, saved photo-review rows, completed workouts, recorded nutrition totals, and confirmed meal count. Current planning includes up to five recent planned meal decisions and up to three unfinished workout plans. The context also contains the profile and goal, workout profile, up to 100 fictional recordable menu items with nutrition and provenance, up to 100 sourced venue entries, and derived remaining calories plus planned calories and protein. Pending, processing, or failed photo rows are status-only and are excluded from the confirmed meal count and daily nutrition. `not_requested` and `completed` photo rows count as confirmed meals; their complete nutrition snapshots contribute to daily totals, while partial snapshots remain per-row matched-food estimates and are not treated as aggregate intake.

The server computes menu eligibility from normalized allergies, dietary preferences, tags, and allergens. Any hard allergy intersection and a strict vegan or vegetarian preference make an item ineligible; soft preferences such as `high_protein` remain eligible. The model is instructed to recommend only eligible catalog items and to include venue, price, estimated calories, and protein when available. A planned meal is a suggestion, not consumed intake, and an unfinished workout plan is not a completed workout. Real venues are place-only: the assistant may identify their supplied location data but cannot invent menu items, prices, allergens, or nutrition for them. Seeded menu data and nutrition remain fictional/illustrative, and photo nutrition remains an estimate.

The assistant receives no image bytes or image paths, raw photo-review attempt log, user/display identity, secrets, Community content, recommendation/deepseek job history, merchant payments, or prior chat.

Both endpoints require the existing development-only demo identity. They return 503 when the key, base URL, or model is missing or blank, or demo authentication is unavailable; 504 on a DeepSeek timeout; and 502 when the upstream provider or returned content is unusable. Settings validation rejects a blank, non-positive, or oversized timeout before the API starts. DeepSeek does not rank meals, select workouts, create stored nutrition, award rewards, or alter Community behavior. OpenRouter explanation and photo-recognition paths are unchanged.

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

If `pnpm` is unavailable, run `./node_modules/.bin/tsc --noEmit`, `./node_modules/.bin/eslint .`, `./node_modules/.bin/vitest run`, and `./node_modules/.bin/next build` from `apps/web`.

Run type generation after changing a Pydantic request or response schema and commit both `packages/api-client/src/openapi.json` and `schema.ts`. The API contract is the source of truth. The generated schema is imported by the browser client in `packages/api-client/src/client.ts`.

## Troubleshooting

- If the page says the demo user is missing, run `python -m scripts.seed_nourishloop` against the same database as the API.
- If the API cannot connect to PostgreSQL, check whether `DATABASE_URL` uses `db` inside Compose and `localhost` on the host.
- If the web app cannot reach the API, check `NEXT_PUBLIC_API_URL` and port 8000. Browser calls require the origin configured in `CORS_ORIGIN`.
- If pnpm or pip cannot install, check network access. The repo includes generated API types, but a clean frontend build still needs Node dependencies.

## Current scope

The current UI and API implement five primary destinations: **Today**, **Food**, **Move**, **Progress** and **Community**. The top bar shows the current demo rewards balance with a **Store** action, while the avatar opens **Profile**; neither utility occupies a primary navigation row. Today selects only a factual no-food, no-workout, food-only, movement-only, or complete check-in state. Food consolidates Explore, For you, Meals and Real places, and the instant/background photo modes. Progress contains the dated summary and the full daily coach report.

The product also implements paginated food and real-place discovery, one-click photo recognition with an immediate USDA nutrition estimate or a clearly labelled AI visual fallback, asynchronous meal recommendations, plan/confirmation tracking, stage-aware workout plans and session logs, paginated Decision/Menu meal/Photo meal records, Community posts/comments/likes/report review, daily and weekly habits, an auditable demo credit ledger, badge redemption, and editable demo profile/goals. Public Reddit discussions appear only as attributed paraphrases with source links. OpenRouter can optionally reword grounded meal explanations and workout coaching notes; exercise selection, sets and meal ranking remain rule based. The separate DeepSeek assistant only explains the current allowlisted health facts and writes transient suggestions.

Instant photo records store no image. Background reviews keep a metadata-free, resized photo temporarily until success or deletion; their AI visual estimate is shown separately and never enters daily totals. Complete source-backed estimates use matched USDA nutrient densities and visually estimated or user supplied edible grams, with an optional correction panel and a source/quantity snapshot. A bundled USDA SR Legacy index supports nutrition lookup when the public API is rate limited. If some sources or portions are unresolved, the app shows only a clearly labelled partial total for matched foods and excludes that partial total from the daily nutrition shown in Progress. Photo records remain separate from menu meals and Community posts. Production authentication, verified restaurant menus/nutrition, production moderation, and commercial features remain future work. Recommendations never use merchant payments. See the [Week 7 checkpoint](submissions/week07/README.md), [current architecture](docs/architecture/overview.md), [operations](docs/operations.md), and [roadmap](docs/product/roadmap.md).

## W07 submission materials

The [milestone evidence](submissions/week07/README.md) links the [demonstration PPT](submissions/week07/NourishLoop_W07_Midterm_Demo.pptx), raw screenshots/logs, final validation and [AI use disclosure](submissions/week07/AI_USE.md). Start with the [active architecture overview](docs/architecture/overview.md) and [operations](docs/operations.md) for the reproducible demo. The historical W04 proposal remains archived separately, and the root `docs/architecture.md` is preserved course history rather than the current architecture. The PPT reports validation and checkpoint status as of 30 October 2026 while preserving the actual 29 October runtime screenshots.
