# NourishLoop operations

## Start the live stack

Use Docker Desktop / Docker Engine with Compose. From the repository root:

```bash
docker compose up --build -d
docker compose ps
docker compose exec api alembic current
```

The API container runs migrations and seeds fictional demo meals, sourced venue listings and the exercise library before becoming healthy. The worker starts after API health succeeds. Open `http://localhost:3000` and `http://localhost:8000/docs`. Keep `.env` local and untracked. The normal demo uses `EXPLANATION_PROVIDER=deterministic`; set `EXPLANATION_PROVIDER=openrouter` and a valid `OPENROUTER_API_KEY` in `.env` for model-written meal wording and workout coaching notes. Photo recognition requires the OpenRouter key in the API container, independent of that explanation setting. Selection and nutrition remain rule/data based. If the model fails, both explanation flows retain grounded wording; photo recognition shows an error instead of inventing a result.

## Live demo sequence

1. Open **My plan** to see the current goal, the last four weeks of meal and training activity, and today’s suggested actions. The browser requests a meal recommendation job automatically when today has no saved meal waiting for confirmation. **Discover → Real menus** remains available for sourced dishes and branch browsing.
2. The worker ranks fictional menu candidates against the profile, goal and recent history. **How your history shaped this** shows the number of confirmed meals and any repeatedly logged dishes that affected ranking. **See other meal options** shows the remaining suggestions.
3. Select **Plan this meal**. The meal appears under today’s plan on the same page. Only confirmed meal logs enter the intake totals and progress counts.
4. Select **I ate this meal** after eating. The confirmed meal updates the four-week progress and refreshes the next suggestion. **Progress & history** contains the daily summary and separate lists for meal plans, confirmed menu meals, photo meals and completed training.
5. In **Community → Member posts**, select that confirmed meal, write a caption, and select **Share meal**. `POST /api/v1/community/posts` persists the voluntary post, which then appears in the paginated feed. The author can remove it. In **Local reviews**, select an area and open the Reddit or OpenRice link to read the source.
6. In **Rewards**, the confirmed meal adds 5 demo credits, and the first shared meal of the day adds 3. Redeem the starter badge for 5; the ledger records the deduction. A removed shared post appends a 3-credit reversal. Community likes/comments do not award credits.
7. The browser uses the default local account. To exercise Community moderation in development, submit a report through the API with `X-Demo-User-Id: demo-peer`, then use the moderator queue in **Community** to dismiss the report or hide the post.
8. Select **View workout plan** on **My plan**, or open **Workouts** directly. The default suggestion uses the saved stage and equipment, a 30-minute duration and the least recently trained compatible focus. **Adjust workout** exposes the training settings and manual focus and duration. Select **I completed this session** after doing it. The workout enters **Progress & history → Training**, and the first completion of the Hong Kong day adds 5 demo credits. Today’s plan then shows the completion. Optional OpenRouter wording falls back to the rules-based explanation.
9. On **Discover → Log a meal**, add optional notes, take or upload a food photo (JPEG/PNG/WebP, up to 5 MB), and select **Recognize food**. That one action identifies visible foods, estimates edible grams, matches USDA entries, and displays approximate kcal/macros with source links without per-food confirmation. If only some foods match, the result displays a clearly labelled partial total and lists excluded foods. **Adjust foods and portions** is optional after the result. Save the complete result or the partial estimate to **Progress & history → Photo meals** in a separate action; if no food can be matched, **Save foods to History** saves names without nutrition. Partial nutrition stays visible in Progress & history but does not contribute to the daily total. The image is not stored. Older names-only records without saved portions cannot be recalculated from the server; re-upload the photo. All saved photo meals count toward the confirmed-meal habit, but cannot yet be shared as a Community menu-meal post.
10. Show the job state in the browser or API, API health, and worker logs as operational evidence:

```bash
docker compose logs --tail=40 worker
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/health').read().decode())"
```

In **Profile**, edit optional age, height, current and target weight, activity level, food preferences and a maximum meal budget. Select **Save profile**. The next **My plan** meal suggestion uses the saved budget. Use **Save goal** for the nutrition goal and **Save training settings** for experience, available equipment and training frequency. The same training settings are available under **Workouts → Adjust workout**.

In **Discover → Real menus**, use **Find food near me** to request browser location access. With access granted, Real menus can automatically select the closest catalog location. Choose another nearby location or browse by area at any time. Use HTTPS for the device location flow on a shared host. Localhost is suitable for the local demo.

Worker logs include `recommendation_job_claimed` and `recommendation_job_completed`. The default formatter omits their extra IDs; correlate via the persisted job response/SQL rather than claiming the IDs are present in log text. The API health route checks PostgreSQL. `docker compose ps` shows container health.

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

Demo identity is enabled only with `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; this stack must remain local. The six seeded menu meals and their nutrition are fictional illustrative data; photo-meal nutrition uses automatically matched or user-selected USDA records and estimated or entered grams. Community shares a confirmed menu meal and its nutrition snapshot publicly within the demo feed, so do not enter private health details or real users' data. API keys stay in `.env`, which is ignored by Git; the API and worker receive the OpenRouter key in Compose. The photo is sent to the configured external vision provider when the user selects **Recognize food**. The UI re-encodes it to JPEG to drop camera metadata, and NourishLoop does not persist its bytes. The free Nemotron endpoint may log submitted content, so use food-only photos without faces or private details.

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
