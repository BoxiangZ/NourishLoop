# Week 3 Submission — Individual Readiness Lab

- Name: 王子扬 (Wang Ziyang)
- Repository: https://github.com/Wzyoung203/MAIE6000C-starter-wzy
- Checkpoint tag: `w03-readiness`

## What I changed

Added one bounded read-only endpoint to the API service: `GET /cases/{case_id}/jobs`.

- returns `200` with the jobs of that case, ordered by `created_at` then `id` (empty array if none)
- returns `404` with `{"detail": "Case not found"}` for an unknown case id, matching
  `GET /cases/{case_id}`
- no schema, migration, worker, or AI-service change

The starter could already read a case or a single job by id, but there was no way to follow the
background work of a case without knowing its job ids.

## Files touched

- `services/api/app/main.py` — `list_jobs_for_case()` helper and the new route
- `tests/integration/test_api_case_flow.py` — three integration tests
- `docs/operations.md` — documented the case and job endpoints
- `submissions/week03/README.md` — this summary

## How I verified it

1. `pytest -q tests/unit tests/integration` → 7 passed (4 baseline + 3 new); `ruff check .` → clean.
2. `alembic upgrade head` on a clean database → revision `20260713_0001` applied, `cases` and `jobs`
   created.
3. Live end-to-end run with the API, AI service, and worker as three real processes: `POST /cases` →
   `201`; the worker completed the job and the case reached `status=triaged` (`ai_label=incident`,
   `ai_confidence=0.71`); `GET /cases/{case_id}/jobs` returned that completed job; an unknown case id
   returned `404`.
4. `SMOKE_BASE_URL=http://127.0.0.1:8000 pytest tests/smoke -q` → 1 passed.

## Notes and limitations

- The route is unauthenticated and unpaginated, like the rest of the starter; pagination is the
  obvious next step.
- Verification used the local SQLite path and the repository's own test suites. The
  `docker compose` / PostgreSQL path was not exercised because Docker was not running in my
  environment.
