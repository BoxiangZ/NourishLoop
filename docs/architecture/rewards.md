# Habit and reward policy

NourishLoop's current rewards are noncommercial demo credits for digital badges. They do not have cash value, cannot be transferred, and are not funded by merchants. The reward service has no dependency on recommendation ranking or model providers.

| Eligible event | Daily grant | Evidence |
|---|---:|---|
| First confirmed meal log | 5 credits | Owned `meal_logs.id` |
| First voluntary Community share of a confirmed meal | 3 credits | Owned `community_posts.id` |

The first eligible event for each user/habit/Hong Kong local day creates one `habit_events` row, enforced by a unique constraint. Extra confirmations or shares on the same day do not mint more credits. Planning a meal, clicking a recommendation, liking, commenting, and reporting do not mint credits. A shared post must remain visible to keep its share grant: author retraction or moderator removal records a negative reversal and marks the habit event reversed. That user cannot earn the same day's share grant again by reposting.

`credit_transactions` is a signed append-only ledger. Application code rejects updates and deletes; award, redemption and reversal add new rows. A badge redemption is unique per user/badge, snapshots its cost, and checks the sum of the user's ledger inside a user-row lock. Reversal after redemption can make the demo balance negative; future earned credits offset that debt. User-account deletion may cascade private ledger data under the deletion policy.

The overview computes today's completion, current consecutive-day streak, and this week's count against a three-day target. It suggests the next incomplete habit. Weekly progress is informational and does not mint another grant. The two seeded badge definitions are fictional and not proof of health outcomes.

This policy is a local demo baseline. Public rewards would need identity, abuse controls, dispute handling, rate limits, audited moderation, and legal/commercial review before any value-bearing redemption.
