# MVP database schema

Alembic revision `20261024_0002` creates NourishLoop tables after the historical starter revision. IDs are UUID strings, except the fixed local demo user ID. Timestamps use timezone-aware UTC values. Foreign keys and delete behavior are explicit in the migration.

| Table | Key relationships and constraints | Data owner/privacy |
|---|---|---|
| `users` | Primary user ID | Private identity |
| `user_profiles` | One row per user; preferences and allergies as JSON arrays | Private dietary information |
| `user_goals` | One row per user; goal and optional daily target | Private wellness information |
| `user_consents` | One row per user; analytics opt-in defaults false | Private consent state |
| `venues` | Public demo venue data | Catalog |
| `menu_items` | Venue FK; availability, tags, source and freshness fields | Catalog |
| `nutrition_facts` | One per item; kcal/macros per serving, provenance and uncertainty | Catalog estimates |
| `recommendation_runs` | User FK; meal slot, scoring version/config | Private behavior history |
| `recommendation_items` | Run/item FKs; unique pair, rank, score, explanation | Private behavior history |
| `recommendation_feedback` | Recommendation/user FKs | Private feedback |
| `user_decisions` | User/item FKs; optional recommendation FK; planned or confirmed | Private action history |
| `meal_logs` | Unique decision FK; user/item FKs; servings, consumed time, immutable nutrition snapshot | Private consumption history |

The meal log copies calculated nutrition at confirmation, so later catalog edits do not change historical totals. User deletes cascade through private history; catalog item deletion is restricted by history foreign keys. The local demo seed is repeatable and uses stable IDs. There is no automatic schema creation in the running application.

Current limitations: preference/allergy strings are free-text normalized to lowercase; a controlled vocabulary and catalog audit are required for real dietary safety. Nutrition data is fictional and unverified. Additional database checks for positive numeric values and decision state should be added before public launch.

## Week 7 additions

Alembic revision `20261027_0003` adds `recommendation_jobs` (user, meal slot, requested limit, provider, lifecycle status, claim count/lease, result run, error type and timestamps) and `community_posts` (author, unique confirmed meal-log reference, caption and creation time). The worker stores a run and job completion in one transaction. A post references a meal log rather than duplicating nutrition; deleting a post does not delete the log. Only a confirmed log can be shared through the API service. The schema does not yet include a moderation workflow or audience controls.
