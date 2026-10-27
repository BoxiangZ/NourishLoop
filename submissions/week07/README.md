# W07 Midterm Milestone Demo — NourishLoop

Team: **group14**

Required tag: `w07-midterm`

Primary artifact: this file

## Product direction and change since Week 4

The midterm product is a student meal decision loop: discover fictional campus meals, receive a ranked recommendation, plan a meal, confirm consumption, view daily totals, and optionally share the confirmed meal in Community. This is the team's current NourishLoop direction. The Week 4 diet-plan and meal-photo architecture in `docs/architecture.md` is preserved as a proposal, not a claim about implemented features. The active architecture is in `docs/architecture/overview.md`.

Community is part of the core loop: only an owned, confirmed meal log can be shared, posting requires a caption and an explicit user action, and a post can be retracted without changing intake. Recommendations remain rule ranked. The optional OpenRouter model rewords the first explanation, with deterministic fallback; it cannot alter rankings, catalog choices, or nutrition.

## Live vertical slice

Start with `docker compose up --build -d`, wait for `docker compose ps` to show `api` healthy, then open `http://localhost:3000`. See `docs/operations.md` for full commands and recovery. The browser is the preferred demo because it shows all actions and persisted states in one sequence.

| Stage | User action / system signal | Persisted evidence |
|---|---|---|
| Request enters | Select **Find my lunch**; `POST /api/v1/recommendations/jobs` returns 202 | `recommendation_jobs.status=pending` |
| Async work | Worker claims job; browser polls `GET /jobs/{id}` | `claimed` and attempt count; worker log with job ID |
| Result | Worker applies restrictions/rules and optional explanation adapter | `recommendation_runs`, `recommendation_items`, job `completed` + run ID |
| Decision | Select **Plan this meal** | `user_decisions.status=planned`; daily total unchanged |
| Confirmation | Select **I ate this meal** | `meal_logs` nutrition snapshot, decision `confirmed`, daily total changes |
| Community | Select confirmed meal, write caption, select **Share meal** | `community_posts` row appears in feed; author can remove it |
| Operational signal | Show `docker compose logs --tail=40 worker`, `/api/v1/health`, and job status | Claimed/completed logs and database health |

For a stable demo, use `EXPLANATION_PROVIDER=deterministic`. The live model path requires a local untracked `.env` with `EXPLANATION_PROVIDER=openrouter` and `OPENROUTER_API_KEY`; if unavailable, the same job and persisted run still complete with baseline explanations.

## Evidence checked on the development machine

- `python -m pytest -q`: **27 passed, 2 skipped**. Integration tests cover queued → worker → completed result → plan → confirmation → Community post/retraction, plus stale job reclaim and model failure fallback.
- Frontend: TypeScript typecheck, ESLint, 2 dashboard interaction tests, and Next.js production build all passed. The UI test verifies that Community sharing occurs only after confirmation and explicit form submission.
- `python -m scripts.generate_api_types` regenerated browser types from the FastAPI OpenAPI contract.
- Alembic upgraded a temporary SQLite database from the starter revision to `20261027_0003 (head)`. A full Docker Compose rehearsal was **not run on this machine** because Docker Desktop and a running daemon were unavailable. PostgreSQL migration and container startup remain to be checked on a machine with Docker before the live review. Backend integration tests use SQLite; CI is configured with PostgreSQL and Alembic, but the new revision has not yet been observed passing CI.

## Current limits and second-half plan

This is a local development demo with one seeded identity. The menu and nutrition are fictional estimates; they are not verified restaurant or medical data. There is no public authentication, multiuser privacy validation, Community moderation, or real-user relevance evaluation. The browser does not resume a previous job after reload. A processing exception marks a job failed; stale claims can be reclaimed but explicit failed-job retry is not yet available.

Next: add real authentication and multiuser ownership tests; add Community reporting/moderation and privacy controls; curate a verified menu sample; measure recommendation compliance/relevance and worker latency/failures; add resumable polling and retry/idempotency. Habits, commercial features, and historical Week 4 photo analysis stay outside this midterm slice.

## Repository checkpoint

The required tag `w07-midterm` should identify the exact commit demonstrated. The Canvas submission must contain the repository URL, tag, tagged SHA, this path, team name, and a demo readiness note. Do not treat a local tag as pushed until `git ls-remote --tags origin w07-midterm` confirms it.
