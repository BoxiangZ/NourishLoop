# Product roadmap

## Implemented local demo

The recommendation → plan → confirmed meal loop remains the authoritative product path. Community now supports explicit meal sharing, comments, likes, reporting and a moderator queue. Habits derive from confirmed meals and voluntary shares; a daily cap, streaks, weekly progress, append-only demo credit ledger, reversals and digital badge redemption are integrated. Automated tests cover the boundaries and role checks. These are development-only features on fictional data and two selectable demo identities.

## Next engineering priorities

1. Replace the single demo identity with real authentication, roles and multiuser ownership tests before public Community access.
2. Add abuse controls: rate limits, comment reports, moderator audit trails, appeal/review rules and privacy settings.
3. Curate and verify a small real menu/nutrition dataset with source dates and allergen review; distinguish estimates.
4. Improve worker observability and recovery: queue depth, processing latency, explicit failed-job retry, resumable browser polling and idempotency.
5. Evaluate recommendation relevance, restriction compliance, user selection and confirmation, and reward effects against a frozen baseline.
6. Add profile/goal editing and richer discovery in the web UI. Decide separately whether the historical Week 4 diet-plan/photo proposal should be revived.

Real exercise tracking, commercial rewards, merchant partnerships, subscriptions and payments remain later phases. Sponsored content must be labelled and never alter organic ranking. This demo offers general wellness estimates, not medical guidance.
