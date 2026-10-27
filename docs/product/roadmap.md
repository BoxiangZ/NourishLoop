# Product roadmap after Week 7

## Implemented midterm slice

A seeded demo user can browse fictional meals, queue a recommendation, see the worker's persisted ranking, plan and confirm a meal, see daily nutrition totals, and explicitly share that confirmed meal to Community. The author can retract a post. An optional OpenRouter adapter rewrites the first explanation only; deterministic ranking and fallback remain authoritative. Automated tests cover the core flow, stale-claim recovery, hard dietary filters, and Community's confirmation boundary.

## Second-half priorities

1. Replace development-only single-user identity with real authentication and add multiuser ownership tests before any public community use.
2. Add Community moderation, reporting, privacy controls, and pagination. Current Community is a local demo, not a public social network.
3. Curate and verify a small real menu/nutrition dataset with source dates and allergen review; clearly distinguish estimates.
4. Improve worker observability and recovery: queue depth, processing latency, explicit retry of failed jobs, resumable browser polling, and database-backed idempotency.
5. Evaluate recommendation relevance, restriction compliance, latency, user selection and confirmation. Keep a frozen deterministic baseline.
6. Add profile/goal editing and discovery filters to the web interface. Decide whether the historical Week 4 diet-plan/photo proposal should be revived after the core loop is stable.

Habits/rewards and commercial features are later work. Merchant sponsorship must never affect organic ranking. This demo offers general wellness estimates, not medical guidance.
