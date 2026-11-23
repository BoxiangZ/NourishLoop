# API contracts

Current product routes are under `/api/v1`; OpenAPI is at `/openapi.json`. Run `python -m scripts.generate_api_types` after Pydantic changes and commit the generated `packages/api-client/src` files.

| Method | Path | Effect |
|---|---|---|
| GET | `/api/v1/health` | Database readiness |
| GET, PATCH | `/api/v1/me`, `/api/v1/me/profile` | Demo user and profile |
| GET, PUT | `/api/v1/me/goals` | Goal |
| GET | `/api/v1/venues`, `/api/v1/menu-items` | Sourced venue directory (`scope`, `q`, `limit`, `offset`) and separate fictional meal catalog (`q`, `tag`, `max_price_hkd`, `limit`, `offset`) |
| GET | `/api/v1/published-dishes` | Dated public menu entries with venue, optional reference price, source and branch/brand scope. Filters include `scope`, `q`, `venue_id`, `location_id`, `limit` and `offset`. |
| GET | `/api/v1/menu-locations` | Public mall and other food-location landmarks associated with published menus |
| GET | `/api/v1/external-notes` | Public dining review and discussion summaries with source links. `scope` accepts `all`, `hkust` (default), `tko`, `hang_hau`, `lohas` and `tai_po_tsai`. Pages use `limit` (1–50, default 20) and `offset` (default 0). |
| GET | `/api/v1/exercises` | Sourced exercise library by muscle group/equipment with `limit`, `offset`. `equipment_detail` gives a more specific requirement when available. |
| GET | `/api/v1/workouts/equipment` | Equipment categories published for HKUST’s fitness centers, with source and check date |
| GET, PUT | `/api/v1/me/workout-profile` | Declared stage, equipment and days per week |
| POST | `/api/v1/workouts/recommend` | Persist a stage-aware plan. An empty JSON object picks an eligible focus from session history with a 30-minute default. Explicit focus and minutes remain supported. |
| POST, GET | `/api/v1/workouts/sessions`, `/api/v1/me/workout-sessions` | Confirm a completed plan and read paginated session history |
| POST | `/api/v1/recommendations/jobs` | Persist pending job; 202 with job ID/status |
| GET | `/api/v1/recommendations/jobs/{id}` | Own job status and completed run |
| GET | `/api/v1/me/plan-progress` | Four Hong Kong calendar weeks of meal and training days, weekly targets, recent and current meal counts, and today's latest planned meal |
| POST | `/api/v1/recommendations/meals` | Synchronous compatibility route |
| POST | `/api/v1/recommendations/{id}/feedback` | Helpfulness feedback |
| POST, GET | `/api/v1/decisions`, `/api/v1/me/decisions` | Plan/read decisions; list supports `limit` and `offset` |
| POST, GET | `/api/v1/meal-logs`, `/api/v1/me/meal-logs` | Confirm/read consumed meals; list supports `limit` and `offset` |
| POST | `/api/v1/meals/analyze-photo` | Send a JPEG/PNG/WebP image (base64, max 5 MB) to OpenRouter vision; return food names, rough edible grams, review questions and a clearly labelled AI visual nutrition estimate when available |
| POST | `/api/v1/photo-meals/auto-estimate` | Match visible foods to USDA entries; return `estimate` for a complete meal, or `partial_estimate` for matched foods plus `unresolved` reasons |
| GET | `/api/v1/nutrition-foods` | Search the bundled USDA SR Legacy index, then cached or live entries by `q`; returns sourced per-100-g kcal/macros |
| POST | `/api/v1/photo-meals/estimate` | Recalculate an optionally edited result from one USDA entry and edible gram amount per food; no model-derived totals |
| POST, GET | `/api/v1/photo-meals`, `/api/v1/me/photo-meals` | Save recognized foods with USDA matched nutrition and/or the AI visual estimate. A new photo meal without either estimate is rejected. Responses carry `nutrition_status` (`complete`, `partial`, `none`) and `unresolved_foods`; AI and partial USDA snapshots are excluded from daily totals |
| POST | `/api/v1/photo-meals/reviews` | Multipart `photo` (JPEG/PNG/WebP, max 8 MB) and optional `notes`; returns 202 with a pending photo meal. The server removes metadata and temporarily stores a resized copy for worker processing. |
| GET, DELETE | `/api/v1/photo-meals/{id}` | Read own review status/result; delete an own pending or failed review and its temporary photo. |
| POST | `/api/v1/photo-meals/{id}/retry` | Retry an own failed review while its temporary photo exists, up to three total attempts. |
| GET | `/api/v1/me/daily-summary` | Confirmed totals for HK local day |
| POST, GET | `/api/v1/community/posts` | Explicitly share a confirmed log/read feed; feed supports `limit` and `offset` |
| DELETE | `/api/v1/community/posts/{id}` | Retract own post |
| GET | `/api/v1/community/me/shared-meal-log-ids` | Own already-shared log IDs, including hidden posts |
| PUT, DELETE | `/api/v1/community/posts/{id}/like` | Idempotent like/unlike |
| POST | `/api/v1/community/posts/{id}/comments` | Comment on a visible post |
| DELETE | `/api/v1/community/comments/{id}` | Remove own or moderated comment |
| POST | `/api/v1/community/posts/{id}/reports` | Report another user's post once |
| GET, POST | `/api/v1/community/reports/pending`, `/api/v1/community/reports/{id}/resolve` | Moderator queue and decision |
| GET | `/api/v1/rewards/overview` | Balance, daily/weekly habit progress, badge catalog and ledger; ledger supports `transaction_limit` and `transaction_offset` |
| POST | `/api/v1/rewards/{id}/redeem` | Redeem one noncommercial badge |

Demo private routes resolve identity on the server. In development with demo auth enabled, `X-Demo-User-Id` can select only the seeded moderator or peer; it is a local impersonation mechanism. Job reads and post removal check ownership. Community post creation checks that its meal log belongs to the current user; a meal can have one post. The feed shows a shared meal, illustrative nutrition snapshot, caption, and demo display name.

`GET /api/v1/me` returns optional `age`, `height_cm`, `weight_kg`, `target_weight_kg`, `activity_level` and `meal_budget_hkd` in `profile`. For these fields, `PATCH /api/v1/me/profile` keeps omitted values and clears fields sent as `null`. `activity_level` accepts `low`, `light`, `moderate` and `high`. A set budget filters demo meals by their listed price before ranking. Workout planning reads training stage, equipment and days per week from `/me/workout-profile`. Body measurements and general activity are stored for reference. The daily calorie target is set explicitly in Goals.

Background photo reviews use the existing `PhotoMealRecord` table. `review_status` moves through `pending`, `processing`, and `completed` or `failed`; `review_attempts` and a private append-only attempt log record worker activity. The result exposes AI visual nutrition separately from USDA matched nutrition. Only a complete USDA match enters daily macro totals; pending and failed reviews do not count as meals or earn habit credit. The temporary image is deleted on success or explicit removal. Failed reviews retain it for retry. The existing instant recognition route and its manual correction panel remain available.

Community likes are idempotent per user/post. Comments require a visible post; the author or demo moderator can delete them. Reports require a different author, allow one report per reporter/post, and are resolved by a moderator as dismissed or removed. Reported content is not hidden automatically. The seeded Demo Student has moderator role; the peer does not.

Reward credits are granted once per habit per Hong Kong local day. Confirmed menu meals, saved photo meals, explicit Community shares and completed workout plans qualify. Post removal appends a credit reversal. The ledger and redemptions are private to the current user. Badges have no cash value, and no recommendation click earns credits.

Real food scopes are `hkust`, `lohas`, `tko`, `hang_hau` and `tai_po_tsai`. Published dishes are browseable references. They carry no inferred allergen or nutrient values and are separate from the recordable demo catalog and its nutritional ranking.

`/menu-locations` returns a location ID, name, area, landmark coordinates and map source for locations with published dishes. The browser ranks them locally and sends `location_id` with the usual filters for the selected mall or other food location.

Published dishes and exercises optionally carry `source_photo` (`url`, `source_url`, `alt`, `credit`). Dishes with photos sort first. The image is loaded from the original provider and links back to its source page.

The default **My plan** view shows progress and requests meal and workout suggestions. Menu meals and confirmed photo meals contribute to `history_context` over the latest seven Hong Kong dates. Repeating the same menu item on at least two distinct days reduces that item’s fit score to favor variety. The run stores the history snapshot in `scoring_config`. Earlier runs can have a null history context. Automatic workout focus prefers compatible groups with no recorded session, then the least recently trained group. The browser shows today’s completion after the user confirms a workout.

Example async path:

```text
POST /api/v1/recommendations/jobs {"meal_slot":"lunch","limit":3}
→ 202 {"id":"...","status":"pending","run":null,...}
GET /api/v1/recommendations/jobs/{id}
→ 200 {"status":"completed","run":{"recommendations":[...]},...}
POST /api/v1/decisions {"menu_item_id":"...","recommendation_id":"..."}
POST /api/v1/meal-logs {"decision_id":"...","servings":1}
POST /api/v1/community/posts {"meal_log_id":"...","caption":"Lunch today"}
```

Errors use `{"error":{"code":"http_404","message":"..."}}` for HTTP errors and `validation_error` for malformed inputs. Unavailable demo auth returns 503, moderator-only access returns 403, missing or foreign objects return 404, duplicate confirmation/sharing/reporting or insufficient credits returns 409, and invalid fields return 422. List endpoints have bounded limits.
