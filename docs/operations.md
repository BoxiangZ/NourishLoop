# NourishLoop operations

## Start the live stack

Use Docker Desktop / Docker Engine with Compose. From the repository root:

```bash
docker compose up --build -d
docker compose ps
docker compose exec api alembic current
```

The API container runs migrations, loads the base fictional demo catalog/venues/exercises, then runs the seven-day activity seed before becoming healthy. The activity seed creates seven menu-meal days, a current-day fictional photo meal, two planned meals, four completed workouts, and one unfinished workout plan for `demo-student`. It uses deterministic Hong Kong-local-day IDs, is idempotent when rerun on the same local day, and touches only that demo user. On a later local day it adds that day's deterministic activity and replaces only stale seeded planned decisions and unfinished seeded workout plans; completed history remains. The worker starts after API health succeeds. Open `http://localhost:3000` and `http://localhost:8000/docs`. Keep `.env` local and untracked. The normal demo uses `EXPLANATION_PROVIDER=deterministic`; set `EXPLANATION_PROVIDER=openrouter` and a valid `OPENROUTER_API_KEY` in `.env` for model-written meal wording and workout coaching notes. Photo recognition requires the OpenRouter key in the API container, independent of that explanation setting. Selection and nutrition remain rule/data based. If the model fails, both explanation flows retain grounded wording; photo recognition shows an error instead of inventing a result.

The floating coach and Progress report require a non-empty `DEEPSEEK_API_KEY`. Their independent defaults are `DEEPSEEK_BASE_URL=https://api.deepseek.com`, `DEEPSEEK_MODEL=deepseek-flash`, and `DEEPSEEK_TIMEOUT_SECONDS=25`. The Compose `api` service forwards all four values from `.env`, falling back to those defaults. Omit the key and both endpoints return 503. A blank base URL or model also returns 503; settings validation rejects a blank, non-positive, or oversized timeout before startup, and the provider rechecks the values before any HTTP request. The provider budgets 1200 completion tokens for a conversational answer and 2400 for a report so reasoning-capable responses still leave room for final text.

## Live demo sequence

1. Open the web app on **Today**, then **Food**. In Food, **Explore** contains the **Real places** tab with sourced HKUST and THE LOHAS venues and official links; external discussion cards link back to Reddit. The **Meals** tab searches the separate fictional food catalog and uses **Previous/Next** for server-paged results. Open **For you** and select **Find my lunch**. The browser sends `POST /api/v1/recommendations/jobs`; the API persists a `pending` recommendation job and returns `202` with its ID.
2. The worker claims that job, ranks fictional menu candidates with the rules engine, and stores a recommendation run/items and `completed` job state in PostgreSQL. The browser polls `GET /api/v1/recommendations/jobs/{id}` and displays the result.
3. Select **Plan this meal**. `POST /api/v1/decisions` persists a `planned` decision and opens **Progress**. The daily total still excludes it.
4. In **Progress**, open the Decisions record and select **I ate this meal**. `POST /api/v1/meal-logs` persists a nutrition snapshot, confirms the decision, and changes the selected day's summary. Decisions and confirmed meals have separate paginated lists.
5. In **Community**, select that confirmed meal, write a caption, and select **Share meal**. `POST /api/v1/community/posts` persists the voluntary post, which then appears in the paginated feed. The author can remove it.
6. Open the top-bar points/**Store** control. The confirmed meal adds 5 demo credits, and the first shared meal of the day adds 3. Redeem the starter badge for 5; the ledger records the deduction. A removed shared post appends a 3-credit reversal. Community likes/comments do not award credits.
7. For Community review, use the **Demo account** selector to switch from **Demo Student** to **Community Peer**. The peer can report the student's post. Switch back to **Demo Student** to dismiss the report or hide the post in the moderator queue. Both accounts are fictional and available only when development demo authentication is enabled.
8. Open **Move**. Choose a muscle group, stage, equipment and session time, then select **Recommend my session**. The API persists a stage-aware plan. Select **I completed this session** only after doing it; the workout enters its own paginated history and the first completion of the Hong Kong day adds 5 demo credits. Repeat the same focus to see the recovery-aware alternate suggestion. Optional OpenRouter wording falls back to a grounded explanation.
9. On **Food → Meals**, open **Instant nutrition** (or **Background review**), add optional notes, take or upload a food photo (JPEG/PNG/WebP, up to 5 MB), and select **Recognize food**. That one action identifies visible foods, estimates edible grams, matches USDA entries, and displays approximate kcal/macros with source links without per-food confirmation. If only some foods match, the result displays a clearly labelled partial total and lists excluded foods. **Adjust foods and portions** is optional after the result. Save the complete result or the partial estimate to **Progress → Photo meals** in a separate action; if no food can be matched, the save action stores names without nutrition. Partial nutrition stays visible in Progress but does not contribute to the daily total. The image is not stored. Older names-only records without saved portions cannot be recalculated from the server; re-upload the photo. All saved photo meals count toward the confirmed-meal habit, but cannot yet be shared as a Community menu-meal post.
10. Open the bottom-right **Coach** ring. The blurred overlay shows one greeting, then one current question and at most one answer. Browser speech may fill the input; typing and **Send question** remain available when speech is unavailable. Each send is one action with at most one DeepSeek request. No previous exchange is sent, and closing the overlay or refreshing clears it. The same request rules apply to **Progress → Generate daily coach report**.
11. Open **Progress** and generate the full report. It combines nutrition and activity observations with next actions and limitations, disappears when the screen unmounts or the browser refreshes, and never writes a question, answer, report, or conversation row. Check the top bar for the points/**Store** control and use the avatar for **Profile**; primary navigation remains **Today**, **Food**, **Move**, **Progress** and **Community**.
12. Show the job state in the browser or API, API health, and worker logs as operational evidence:

```bash
docker compose logs --tail=40 worker
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"
```

Worker logs include `recommendation_job_claimed` and `recommendation_job_completed`. The default formatter omits their extra IDs; correlate via the persisted job response/SQL rather than claiming the IDs are present in log text. The API health route checks PostgreSQL. `docker compose ps` shows container health.

## Failure and recovery

A failed processing exception sets the job to `failed` with the exception type; the UI shows a failure. A worker interrupted after claiming leaves a `claimed` job; after `WORKER_LEASE_SECONDS` (default 120) it is eligible for reclaim. Claims use PostgreSQL `FOR UPDATE SKIP LOCKED` and at most three claims. Model explanation errors fall back to deterministic wording without changing ranking or nutrition. If no worker is running, the browser times out after 30 seconds while the persisted job remains queryable; start/restart `worker` and reload the page to request another job. The current UI does not resume an earlier job after a browser reload.

For the assistant, missing or blank key/base URL/model configuration returns 503, DeepSeek timeout returns 504, and an upstream failure or invalid/empty response returns 502. A blank, non-positive, or oversized timeout is rejected by settings validation before startup. The UI exposes the safe runtime messages but performs no automatic retry. A retry requires another user submit and is a new action with at most one additional DeepSeek request. DeepSeek has no job row, queue item, browser cache, or migration; rereading the day always builds a fresh context. Saved pending/processing/failed photo-review rows appear as status-only without row nutrition. `not_requested` and `completed` rows count toward the confirmed meal count; only their `complete` nutrition snapshots contribute to daily nutrition totals, while `partial` snapshots remain per-row matched-food estimates.

## Checks and cleanup

```bash
python -m pytest -q
python -m scripts.generate_api_types
ruff check .
cd apps/web
./node_modules/.bin/tsc --noEmit
./node_modules/.bin/eslint .
./node_modules/.bin/vitest run
./node_modules/.bin/next build
```

The repository-wide Ruff run currently also discovers imported historical code. In this branch it reports existing E501/E731 violations outside the changed feature files; verification must separately run Ruff on the changed Python files and require that subset to pass.

The optional historical Week 4 AI service runs only with `docker compose --profile week4-ai up ai`. Do not use its old case endpoints for the NourishLoop demo. `docker compose down` stops the stack. `docker compose down -v` also deletes local demo data; use only for an intentional reset.

## Security and data limits

Demo identity is enabled only with `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; this stack must remain local and adds no production bypass. The six seeded menu meals and their nutrition are fictional illustrative data. The seven-day activity seed is also fictional and scoped only to the current `demo-student`; it is not benchmark evidence or data for another demo identity. Photo-meal nutrition uses automatically matched or user-selected USDA records and estimated or entered grams. Community shares a confirmed menu meal and its nutrition snapshot publicly within the demo feed, so do not enter private health details or real users' data. API keys stay in `.env`, which is ignored by Git; the API and worker receive the OpenRouter key in Compose. The photo is sent to the configured external vision provider when the user selects **Recognize food**. The UI re-encodes it to JPEG to drop camera metadata, and NourishLoop does not persist its bytes. The free Nemotron endpoint may log submitted content, so use food-only photos without faces or private details.

Coach questions and allowlisted health context are sent to DeepSeek when the user submits an action. The backend keeps `DEEPSEEK_API_KEY` server-side and sends no image bytes/paths, photo-review developer logs, identity/display fields, Community content, payments, secrets, or prior conversation. Questions, health context, answers, reports, raw provider bodies, Authorization headers, and API keys are not included in application logs, and questions/answers/reports are not persisted. Model output is validated and rendered as text with no raw-HTML injection path. No DeepSeek-generated value feeds ranking, workout selection, stored nutrition, credits, or Community state. Because the request still contains demo profile/meal/workout facts, use the seeded fictional demo data and do not enter real health information.

The seed grants moderator role to the local demo user only and also creates a non-moderator peer. The `X-Demo-User-Id` switch header accepts only these two seeded IDs in development; it is a demo impersonation mechanism, not real authentication. Reports are not automatically hidden; the moderator must review them. There is no real identity, rate limiting, audit-grade production moderation, or monetary reward. Keep the stack private. The USDA `DEMO_KEY` in `.env.example` is limited; set your own `USDA_API_KEY` for sustained use. After updating an existing database, run `docker compose up --build` so migrations through `20261028_0008` and the current seed are applied.

## W07 captured validation and final checks

The [milestone README](../submissions/week07/README.md) records the actual 29 October runtime evidence and the final 30 October validation reflected in the revised PPT. PostgreSQL startup, migration 0008, seed and the browser main path were exercised. API/worker restart retained records. Backend automated fixtures use SQLite.

From the repository root:

```bash
docker compose exec -T api pytest -q tests/unit tests/integration
docker compose exec -T api ruff check .
docker compose exec -T api python -m scripts.generate_api_types
git diff --exit-code -- packages/api-client/src/openapi.json packages/api-client/src/schema.ts
docker compose exec -T web pnpm typecheck
docker compose exec -T web pnpm lint
docker compose exec -T web pnpm test
docker compose exec -T web pnpm build
```

When running the isolated evidence override on port 13000, the existing CORS test still expects localhost:3000. Set `-e CORS_ORIGIN=http://localhost:3000` on the test process only. The actual web application retains its 13000 origin. Raw final checks are in [final-validation.txt](../submissions/week07/assets/final-validation.txt). No model key is needed for the deterministic main path.
