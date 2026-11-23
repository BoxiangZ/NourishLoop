# MVP database schema

Alembic revision `20261024_0002` creates NourishLoop tables after the historical starter revision. IDs are UUID strings, except the fixed local demo user ID. Timestamps use timezone-aware UTC values. Foreign keys and delete behavior are explicit in the migration.

| Table | Key relationships and constraints | Data owner/privacy |
|---|---|---|
| `users` | Primary user ID | Private identity |
| `user_profiles` | One row per user; preferences and allergies as JSON arrays, plus optional personal measurements, activity and meal budget | Display name on shared posts; other fields are private |
| `user_goals` | One row per user; goal and optional daily target | Private wellness information |
| `user_consents` | One row per user; analytics opt-in defaults false | Private consent state |
| `venues` | Source scope, official URL and check date for real listings; separate demo venues | Catalog |
| `external_notes` | Attributed, dated paraphrases linking to public discussion sources | Public reference material |
| `menu_items` | Venue FK; availability, tags, source and freshness fields | Catalog |
| `nutrition_facts` | One per item; kcal/macros per serving, provenance and uncertainty | Catalog estimates |
| `recommendation_runs` | User FK; meal slot, scoring version/config | Private behavior history |
| `recommendation_items` | Run/item FKs; unique pair, rank, score, explanation | Private behavior history |
| `recommendation_feedback` | Recommendation/user FKs | Private feedback |
| `user_decisions` | User/item FKs; optional recommendation FK; planned or confirmed | Private action history |
| `meal_logs` | Unique decision FK; user/item FKs; servings, consumed time, immutable nutrition snapshot | Private consumption history |

The meal log copies calculated nutrition at confirmation, so later catalog edits do not change historical totals. User deletes cascade through private history; catalog item deletion is restricted by history foreign keys. The local demo seed is repeatable and uses stable IDs. There is no automatic schema creation in the running application.

Revision `20261122_0012` adds nullable personal details and the meal budget to existing profiles. Existing users can leave these fields blank.

Current limitations: the API validates preferences and allergies against the demo vocabulary. Real dietary safety still requires a catalog audit. Nutrition data is fictional and unverified. Additional database checks for positive numeric values and decision state should be added before public launch.

## Week 7 additions

Alembic revision `20261027_0003` adds `recommendation_jobs` (user, meal slot, requested limit, provider, lifecycle status, claim count/lease, result run, error type and timestamps) and `community_posts` (author, unique confirmed meal-log reference, caption and creation time). The worker stores a run and job completion in one transaction. A post references a meal log rather than duplicating nutrition. Only a confirmed log can be shared through the API service.

## Community and rewards extension

Revision `20261028_0004` adds Community comments, unique per-user post reactions, reports with resolution state, post visibility, and a demo moderator role. Author removal and moderator removal hide a post while retaining its row and reports for audit. It also adds:

| Table | Constraint and purpose |
|---|---|
| `habit_definitions` | Seeded daily habits with points and weekly targets |
| `habit_events` | One event per user/habit/Hong Kong local day; source type and ID for audit |
| `credit_transactions` | Signed append-only ledger; a row refers to a habit event, redemption, or reversed credit |
| `reward_items` | Seeded noncommercial digital badges |
| `reward_redemptions` | One redemption per user/badge, with cost snapshot |

Habit events and credit grants commit with their confirmed meal log or voluntary Community post. Removing a credited post appends a negative reversal and marks its habit event reversed; it does not change the meal log. A revoked credit can leave a negative balance after a prior redemption, which future earned credits offset. No cash-value rewards, merchant funding, or payment integration exist.

## Places and workouts extension

Revision `20261028_0005` adds venue source fields and the `external_notes` table. It adds `exercises` (sourced action catalog), `workout_profiles` (one private stage/equipment/weekly goal per user), `workout_plans` (owned recommendation snapshot with stage, focus, prescriptions and explanation source), and `workout_sessions` (unique plan reference and completion time). A completed session creates one `complete_workout` habit event per Hong Kong day and a signed demo credit row in the same transaction. Plans alone do not award credits. Exercise and venue sources are dated or directly linked; real venues do not acquire invented nutrition facts.

Revision `20261122_0010` adds `published_dishes`, which links a dated menu entry and nullable reference price to a real venue, and `gym_equipment`, which stores school-published equipment categories and locations. `exercises.equipment_detail` is nullable for older movements and supplies more precise equipment requirements where known. Menu snapshots have no nutrition or allergen fields and do not participate in the demo meal decision/log schema.

Revision `20261122_0011` adds nullable `source_photo` metadata to `published_dishes` and `exercises`. Each populated record includes the remote image URL, source page, alternative text and credit.

## Photo meal records

Revision `20261028_0006` adds `photo_meal_records` with user ID, reviewed food names, optional notes, model name and consumption time. It has no image or image URL column. Revision `20261028_0007` adds a `nutrition_foods` cache of USDA SR Legacy per-100-g nutrient densities and nullable nutrition/item snapshots to photo records. Each item snapshot retains the selected source ID/description, entered edible grams and calculated values; later cache changes do not rewrite history. A photo meal with complete reviewed matches contributes its approximate values to that day's totals. A names-only photo meal counts toward the confirmed-meal count but contributes no nutrition values. Both can earn the daily `confirm_meal` credit. Photo records have their own paginated History list and cannot be shared through the existing menu-meal Community post route.
