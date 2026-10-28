# Module boundaries

| Module | Responsibility | Main routes |
|---|---|---|
| Identity | Development-only demo identity, profile, goals | `/me`, `/me/profile`, `/me/goals` |
| Catalog | Sourced real-place directory and external discussion notes; separate fictional meals and illustrative nutrition | `/venues`, `/external-notes`, `/menu-items` |
| Workouts | Sourced exercise library, training profile, stage-aware plan and confirmed session | `/exercises`, `/me/workout-profile`, `/workouts/recommend`, `/workouts/sessions` |
| Recommendations | Restriction filtering, rule ranking, job/run persistence, optional explanation wording | `/recommendations/jobs`, `/recommendations/meals` |
| Tracking | Planned decisions, confirmed menu snapshots, photo recognition, USDA-backed nutrition estimates, reviewed records and daily totals | `/decisions`, `/meal-logs`, `/meals/analyze-photo`, `/photo-meals`, `/me/daily-summary` |
| Community | Owned confirmed-meal posts, comments, likes, reports and demo moderation | `/community/posts`, `/community/reports` |
| Habits and rewards | Daily capped habit events, streak/weekly progress, append-only credit ledger and demo badge redemption | `/rewards/overview`, `/rewards/{id}/redeem` |
| Worker | Claim jobs, process recommendations, log status | `python -m apps.api.worker` |
| Web and client | Demo interactions, job polling, generated API types | `apps/web`, `packages/api-client` |

Domain code lives in `apps/api/modules`. HTTP handlers validate and delegate; services own workflows; models represent persistence. The meal and workout selection engines have no HTTP, SQL, model-provider or merchant-payment dependency. Community references the authoritative menu meal log; it cannot edit confirmed intake or catalog values. Tracking, Community and Workouts award eligible Habit events in their own database transaction; neither recommendation clicks nor likes/comments award credits. Photo analysis calls OpenRouter from the active Tracking module and returns a draft requiring review; image bytes are not persisted. The historical starter services and Week 4 image/diet draft adapters under `services/` remain outside the active product path.
