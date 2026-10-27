# NourishLoop operations (Week 7)

## Start the live stack

Use Docker Desktop / Docker Engine with Compose. From the repository root:

```bash
docker compose up --build -d
docker compose ps
docker compose exec api alembic current
```

The API container runs migrations and seeds fictional catalog data before becoming healthy. The worker starts after API health succeeds. Open `http://localhost:3000` and `http://localhost:8000/docs`. Keep `.env` local and untracked. The normal demo uses `EXPLANATION_PROVIDER=deterministic`; set `EXPLANATION_PROVIDER=openrouter` and a valid `OPENROUTER_API_KEY` in `.env` to use model-written wording for the first ranked meal. Ranking and nutrition remain rule/data based. If the model fails, the worker stores the deterministic explanation.

## Live demo sequence

1. Open the web app and select **Find my lunch**. The browser sends `POST /api/v1/recommendations/jobs`; the API persists a `pending` recommendation job and returns `202` with its ID.
2. The worker claims that job, ranks fictional menu candidates with the rules engine, and stores a recommendation run/items and `completed` job state in PostgreSQL. The browser polls `GET /api/v1/recommendations/jobs/{id}` and displays the result.
3. Select **Plan this meal**. `POST /api/v1/decisions` persists a `planned` decision. The daily total still excludes it.
4. Select **I ate this meal**. `POST /api/v1/meal-logs` persists a nutrition snapshot, confirms the decision, and changes the daily summary.
5. In **Community**, select that confirmed meal, write a caption, and select **Share meal**. `POST /api/v1/community/posts` persists the voluntary post, which then appears in the feed. The author can remove it.
6. Show the job state in the browser or API, API health, and worker logs as operational evidence:

```bash
docker compose logs --tail=40 worker
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"
```

Worker logs include `recommendation_job_claimed` and `recommendation_job_completed` with IDs. The API health route checks PostgreSQL. `docker compose ps` shows container health.

## Failure and recovery

A failed processing exception sets the job to `failed` with the exception type; the UI shows a failure. A worker interrupted after claiming leaves a `claimed` job; after `WORKER_LEASE_SECONDS` (default 120) it is eligible for reclaim. Claims use PostgreSQL `FOR UPDATE SKIP LOCKED` and at most three claims. Model explanation errors fall back to deterministic wording without changing ranking or nutrition. If no worker is running, the browser times out after 30 seconds while the persisted job remains queryable; start/restart `worker` and reload the page to request another job. The current UI does not resume an earlier job after a browser reload.

## Checks and cleanup

```bash
python -m pytest -q
python -m scripts.generate_api_types
cd apps/web && ./node_modules/.bin/tsc --noEmit && ./node_modules/.bin/vitest run && ./node_modules/.bin/eslint .
```

The optional historical Week 4 AI service runs only with `docker compose --profile week4-ai up ai`. Do not use its old case endpoints for the NourishLoop demo. `docker compose down` stops the stack. `docker compose down -v` also deletes local demo data; use only for an intentional reset.

## Security and data limits

Demo identity is enabled only with `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; this stack must remain local. Seeded venues and nutrition are fictional illustrative data. Community shares a confirmed meal and its nutrition snapshot publicly within the demo feed, so do not enter private health details or real users' data. API keys stay in `.env`, which is ignored by Git; only the worker receives the OpenRouter key in Compose.
