# W07 Midterm Milestone — NourishLoop

Team: **group14**  
Required checkpoint: **w07-midterm**  
Primary artifact: **submissions/week07/README.md**

## Demonstration artifact and course requirements

[Download the PowerPoint](NourishLoop_W07_Midterm_Demo.pptx). The existing 16-slide deck is retained unchanged. No separate video, narration or stage presentation is required under the [PPT clarification](https://canvas.ust.hk/courses/74201/discussion_topics/652340). See the [assignment](https://canvas.ust.hk/courses/74201/assignments/461342) and [four-document clarification](https://canvas.ust.hk/courses/74201/discussion_topics/652495).

**Version note:** the PPT captures source `6bfc9b8bf72b63a819646f8780d421d15fb3f329` on 29 October 2026. Its slides 13–16 accurately describe that earlier snapshot, including 42 Ruff errors and the old tag. The final checkpoint adds behavior-preserving formatting, updated documentation and these evidence files. [Final validation](assets/final-validation.txt) supersedes those older lint results. The required tag identifies the final repository checkpoint; the slide's earlier tag warning is historical. Resolve the final tagged SHA with `git rev-parse 'w07-midterm^{commit}'` after fetching tags.

## Direction, scope and progress

NourishLoop's midterm focus is a student meal decision loop: request a recommendation → worker result → plan → confirmed meal log → voluntary Community share. This replaces the broader Week 4 diet-plan proposal as the active product direction. Historical submission files are preserved.

The current code also contains habits, demo rewards, workout planning and photo-meal estimation. Those extensions are not prerequisites for the demonstrated main slice. The captured reward ledger verifies integration from confirmed actions; real vision calls, workout completion and badge redemption were not part of this rehearsal.

## One coherent persisted path

| Requirement / stage | Actual observation | Evidence |
| --- | --- | --- |
| Input | Browser Find my lunch; POST /api/v1/recommendations/jobs returns 202 | [input screenshot](assets/ui-input.png), [request log](assets/operations.json), PPT 4 |
| Persisted change | Job pending, attempts 0, run_id null | [pending API and SQL](assets/pending.json), PPT 5 |
| Async worker | Separate process claims and completes; attempts 1 | [worker logs and SQL](assets/operations.json), [completed response](assets/completed.json), PPT 6 |
| Saved output | Job links to a run with three persisted ranked items | [results](assets/completed.json), [UI](assets/ui-result.png), PPT 7 |
| Cross-module integration | Plan leaves daily total 0; confirmation creates 1 meal log and 640 illustrative kcal | [planned](assets/planned.json), [confirmed](assets/confirmed.json), PPT 8 |
| Explicit sharing | Confirmed menu meal and caption create one Community post | [post](assets/shared.json), [UI](assets/ui-community.png), PPT 9 |
| Habit integration | Confirmation +5 and voluntary share +3 create 8 demo credits | [reward UI](assets/ui-rewards.png), [records](assets/shared.json), PPT 10 |
| Operational signal | Health, container states, claimed/completed event logs | [operations](assets/operations.json), PPT 11 |
| Restart durability | API/worker restart preserves the same job, run, meal log, post and credits | [restart capture](assets/restarted.json), PPT 11 |

Job `ad6b70b1-fa77-43e6-a9e6-58f40dce50e5` links to run `c2831e07-0dda-43e4-9d81-9adddb3f6fe0`. The worker was briefly paused to capture a real pending row, then resumed; this delay is not a benchmark. UTC timestamps are retained. Default worker formatting prints event names but omits extra IDs; correlation here comes from SQL, not invented log text.

## Reproduction

From the repository root with Docker Desktop/Engine and Compose:

```bash
docker compose up --build -d
docker compose ps
docker compose exec api alembic current
curl http://localhost:8000/api/v1/health
docker compose logs --tail=80 worker
```

Wait for API health, open http://localhost:3000, then follow [operations](../../docs/operations.md) steps 1–5. Use deterministic explanations without model keys. Planning and confirmation must be separate actions; sharing must be explicit. New runs have different UUIDs.

The evidence capture used isolated ports 13000/18080/15480. To reproduce that layout, add `-p w07-ppt-evidence -f compose.yaml -f submissions/week07/assets/compose.evidence.yaml` to each Compose command and open http://localhost:13000. The override requires Compose support for `!override`. Keep default worker/UI states running separate from actual configured API/DB health checks.

Use `docker compose restart api worker`, then query the existing job and History/Community to inspect persistence. `docker compose down` retains the data volume. Do not use `-v` unless intentionally resetting demo data.

## Validation and evidence boundaries

The 29 October Docker rehearsal passed PostgreSQL migrations through `20261028_0008`, seeded successfully and exercised the browser-to-database main loop. Backend unit/integration: **42 passed, 2 dependency deprecation warnings**. Frontend: **12 passed**, plus typecheck, ESLint and Next production build. Original outputs are in [checks.json](assets/checks.json) and associated logs.

The original snapshot had 42 E501 lint findings. The final formatting repair preserves Python ASTs and is separately checked in [final-validation.txt](assets/final-validation.txt). Backend automated integration fixtures use SQLite; the separate browser rehearsal used PostgreSQL. No claim is made that all automated tests ran against PostgreSQL. Real OpenRouter, food recognition accuracy, load testing, production authentication and public moderation operations remain unverified. Remote CI results must be read from the final PR, independently of local checks.

## Remaining work and second-half plan

| Priority | Risk / remaining work | Acceptance target |
| --- | --- | --- |
| Reliability | Reload loses polling context; failed jobs lack explicit retry | Resume a saved job ID; test bounded retry/idempotency |
| Safety before public use | Development identity, limited operational moderation | Real auth, ownership/privacy tests, rate limits, moderation procedure |
| Data evaluation | Fictional menus and uncertain photo portions | Curated sourced menu sample and fixed evaluation set; record errors and latency |
| Model validation | Real provider not exercised | Food-only consented examples, timeout/fallback checks and sourced nutrition review |
| Operations | No production deployment or load evidence | Structured correlation logs, recovery rehearsal and capacity measurements |

See [AI use disclosure](AI_USE.md). Four documents have distinct roles: the root README gives overview/setup, architecture explains components and decisions, operations explains running/recovery, and this file reports milestone evidence and remaining risks.
