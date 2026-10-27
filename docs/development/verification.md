# Foundation verification (2026-10-24)

Executed on this workspace after implementation:

| Check | Result |
|---|---|
| `python -m pytest -q tests/unit tests/integration` | 14 passed; one upstream Starlette/httpx deprecation warning |
| `ruff check .` | Passed with locally cached Ruff 0.15.20; project CI installs pinned Ruff 0.12.4 |
| `python -m scripts.generate_api_types` | Passed; generated OpenAPI JSON and TypeScript schema |
| Alembic `upgrade head`, seed, and `alembic check` on a temporary SQLite database | Passed; no pending schema differences |
| `docker compose config --quiet` | Passed |
| `pnpm install --frozen-lockfile` | Passed using pnpm 9.15.9 |
| Frontend `tsc --noEmit`, `eslint .`, `vitest run`, `next build` | Passed; one UI flow test passed |
| Local API `/api/v1/health` and `/api/v1/me` plus built frontend `/` HTTP requests | Returned 200 using a temporary SQLite database |

The Docker daemon was not running, so the actual PostgreSQL Compose stack and its container builds were not executed. The localhost browser UI could not be inspected through the available computer-use browser surface; the page was served successfully by Next.js and the interaction was covered by the frontend test. The live smoke test requires a running stack and was skipped when `SMOKE_BASE_URL` was unset. PostgreSQL-specific migration behavior and the complete browser-to-API journey remain to be checked on a machine with Docker running.

Corepack on this machine rejected the pnpm package signature. `npm exec --yes --package=pnpm@9.15.9 -- pnpm install` was used to install dependencies; the repository's Dockerfile, CI, and README use `npm install --global pnpm@9.15.9` to avoid that Corepack issue. No external LLM credentials or real user data were used.

## Optional Week 4 AI adapter check (2026-10-27)

With the supplied course key stored only in a local ignored `.env`, a real text request to `https://api1.hkgai.net/v1/chat/completions` returned HTTP 200 and the requested `pong`. Synthetic plan-target and meal-note requests passed the new adapter and returned model request IDs. A synthetic one-pixel image request returned HTTP 400 with the provider message `is not a multimodal model`; photo recognition is therefore not exposed by this adapter. `python -m pytest -q tests/unit tests/integration` passed (18 tests), `python -m compileall -q services/ai/app services/common/config.py`, and `docker compose config --quiet` passed. Ruff was unavailable in this shell. The Docker daemon was not running, so the optional AI container itself was not started.

The later Gemini check used a second supplied credential, also stored only in `.env`. `gemini-3.8-flash` model lookup and synthetic-image token counting returned HTTP 200, but text generation through both `generateContent` and Interactions timed out. With the same credential, `gemini-3.5-flash-lite` returned `pong`, identified a synthetic red image as red, and returned a schema-valid empty-food draft plus a review question from the new `/meals/recognize` adapter. A real FastAPI `POST /meals/recognize` request using a synthetic non-food image returned HTTP 200 with the same draft shape. `python -m pytest -q tests/unit tests/integration` passed (23 tests). No real meal-photo accuracy test was performed. The configured default is the verified Flash-Lite model; the original model can be retried by setting `GEMINI_MODEL=gemini-3.8-flash`.
