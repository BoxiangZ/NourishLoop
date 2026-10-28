# Product roadmap

## Implemented local demo

The recommendation → plan → confirmed meal loop remains the catalog food path. A photo path now accepts an uploaded food image, returns a vision-model draft for review, and lets the user choose USDA SR Legacy food matches and edible grams, previews calculated approximate nutrition, and stores corrected food names with an optional sourced nutrition snapshot. Images are not stored. A separate Workout path includes a sourced exercise library, stage/equipment profile, recovery-aware recommendation, persisted plan, confirmed session and daily habit credit. Discover includes a dated snapshot of official HKUST and THE LOHAS venue listings plus attributed public-discussion summaries. Community supports explicit meal sharing, comments, likes, reporting and a moderator queue. A daily cap, streaks, weekly progress, append-only demo credit ledger, reversals and digital badge redemption are integrated. These remain development-only flows with two selectable demo identities.

## Next engineering priorities

1. Replace the single demo identity with real authentication, roles and multiuser ownership tests before public Community access.
2. Add abuse controls: rate limits, comment reports, moderator audit trails, appeal/review rules and privacy settings.
3. Curate and verify real restaurant menus, nutrition and allergens before connecting sourced venues to meal recommendations; schedule venue refreshes.
4. Improve worker observability and recovery: queue depth, processing latency, explicit failed-job retry, resumable browser polling and idempotency.
5. Evaluate recommendation relevance, restriction compliance, user selection and confirmation, and reward effects against a frozen baseline.
6. Evaluate workout plan adherence, exercise coverage and progression with qualified trainers. Evaluate photo recognition, USDA food matching and gram-entry usability; expand validated coverage for local mixed dishes without treating photo-only portions as measured. The historical Week 4 diet-plan proposal remains separate.

Commercial rewards, merchant partnerships, subscriptions and payments remain later phases. Sponsored content must be labelled and never alter organic ranking. This demo offers general fitness guidance and illustrative nutrition, not medical advice.
