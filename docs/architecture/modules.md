# Module boundaries

| Module | Responsibility | Main routes |
|---|---|---|
| Identity | Development-only demo identity, profile, goals | `/me`, `/me/profile`, `/me/goals` |
| Catalog | Fictional venues, meals and illustrative nutrition | `/venues`, `/menu-items` |
| Recommendations | Restriction filtering, rule ranking, job/run persistence, optional explanation wording | `/recommendations/jobs`, `/recommendations/meals` |
| Tracking | Planned decisions, confirmed meal snapshots, daily totals | `/decisions`, `/meal-logs`, `/me/daily-summary` |
| Community | Owned confirmed-meal posts, comments, likes, reports and demo moderation | `/community/posts`, `/community/reports` |
| Habits and rewards | Daily capped habit events, streak/weekly progress, append-only credit ledger and demo badge redemption | `/rewards/overview`, `/rewards/{id}/redeem` |
| Worker | Claim jobs, process recommendations, log status | `python -m apps.api.worker` |
| Web and client | Demo interactions, job polling, generated API types | `apps/web`, `packages/api-client` |

Domain code lives in `apps/api/modules`. HTTP handlers validate and delegate; services own workflows; models represent persistence. The rule engine has no HTTP, SQL, model-provider or merchant-payment dependency. Community references the authoritative meal log; it cannot edit confirmed intake or catalog values. Tracking and Community award eligible Habit events in their own database transaction; neither recommendation clicks nor likes/comments award credits. The historical starter services and Week 4 image/diet draft adapters under `services/` are outside the active product path.
