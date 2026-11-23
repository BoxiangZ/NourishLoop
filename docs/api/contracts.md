# API contracts

Current product routes are under `/api/v1`; OpenAPI is at `/openapi.json`. Run `python -m scripts.generate_api_types` after Pydantic changes and commit the generated `packages/api-client/src` files.

| Method | Path | Effect |
|---|---|---|
| GET | `/api/v1/health` | Database readiness |
| GET, PATCH | `/api/v1/me`, `/api/v1/me/profile` | Demo user and profile |
| GET, PUT | `/api/v1/me/goals` | Goal |
| POST | `/api/v1/assistant/ask` | One grounded, conversational DeepSeek answer to the current question; no persistence |
| POST | `/api/v1/assistant/daily-report` | One structured DeepSeek report from the current allowlisted daily context; no persistence |
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

### Assistant endpoints

`POST /api/v1/assistant/ask` trims and validates a question, then sends that question with a fresh read-only health context to DeepSeek:

```json
{ "question": "How should I plan dinner?" }
```

```json
{ "answer": "Choose a balanced dinner that leaves room for protein, vegetables, and a comfortable portion." }
```

The question must contain 1-500 characters after trimming and the returned answer must contain 1-1000 characters. Blank or oversized input returns 422. The answer prompt requests two to three short, spoken-style sentences in the user's language, usually under 80 words, with no headings, bullets, numbered lists, tables, labels, Markdown bold, or label-value formatting. It tells the model not to explain internal accounting and to phrase plan context naturally. The contract validates nonblank length and terminal punctuation; sentence count and style are provider guidance.

`POST /api/v1/assistant/daily-report` has no request body. It returns one validated report with a headline, nutrition and activity insights, and at most three next actions and three limitations:

```json
{
  "headline": "A steady day.",
  "nutrition_insight": "One confirmed meal is recorded.",
  "activity_insight": "One completed workout is recorded.",
  "next_actions": ["Choose a balanced dinner."],
  "limitations": ["Photo nutrition is approximate."]
}
```

The read-only context has these sections:

- Profile: goal, optional daily calorie target, dietary preferences, allergies, and workout stage/equipment/days per week.
- Current intake: Hong Kong-local-day nutrition totals and confirmed meal count; confirmed menu meals; saved photo-review rows; and completed workouts.
- Plans and catalog: up to five recent `planned` meal decisions, up to three unfinished workout plans, up to 100 fictional recordable menu items, and up to 100 venue entries that may be demo or sourced real places.
- Derived values: remaining calories after confirmed intake, plus planned calories and protein. Planned values are not included in current intake.
- Current ask: the question for `/ask`; `/daily-report` has no question.

Menu catalog entries include name, venue, area, description, category, price, tags, allergens, estimates, provenance, and server-computed `eligible` and `ineligibility_reasons`. Normalized allergen intersections and strict vegan/vegetarian requirements make an item ineligible; other preferences such as high protein do not remove it. The prompt uses the catalog as the sole source of menu recommendations and prohibits recommending an item marked ineligible. Demo menu items and their nutrition are fictional illustrative data. Venue entries contain only name, campus area, scope, `is_demo`, and an optional source URL; they may be fictional demo entries or sourced real places. The assistant receives real venues as place records. Published menu snapshots are served by the catalog endpoints and are outside the assistant context.

A planned meal decision is a suggestion and never counts as consumed or contributes to nutrition totals. An unfinished workout plan is not completed activity. Pending, processing, or failed photo rows are status-only and are excluded from the confirmed meal count and nutrition. `not_requested` and `completed` photo rows count as confirmed meals; only their `complete` nutrition snapshots contribute to aggregate nutrition totals, while `partial` snapshots remain per-row matched-food facts and are not treated as aggregate intake. The prompt labels seeded menu/nutrition data as fictional demo information, distinguishes estimates, and is structured into four sections: role, data authority, recommendation priorities, and response style. The context excludes image bytes or paths, photo-review logs/errors, identity and display fields, Community content, payments, secrets, recommendation/provider history, and prior questions/answers.

Both endpoints use the same current-user dependency. Missing/blank `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, or `DEEPSEEK_MODEL`, or unavailable demo identity returns 503; a DeepSeek timeout returns 504; an upstream failure or invalid/empty generated content returns 502. Settings validation rejects a blank, non-positive, or oversized timeout before the API starts, and the provider rechecks all required values before an HTTP request. Errors use fixed messages and the standard `{"error":{"code":"http_502","message":"..."}}` envelope. The frontend and backend do not retry automatically. Questions, answers, reports, and context are not persisted and are not included in application logs, along with raw upstream bodies, Authorization headers, and API keys. DeepSeek is independent of OpenRouter and does not influence recommendation ranking, stored nutrition, workouts, rewards, or Community; OpenRouter's existing explanation and photo-recognition contracts remain unchanged.

Background photo reviews use the existing `PhotoMealRecord` table. `review_status` moves through `pending`, `processing`, and `completed` or `failed`; `review_attempts` and a private append-only attempt log record worker activity. The result exposes AI visual nutrition separately from USDA matched nutrition. Only a complete USDA match enters daily macro totals; pending and failed reviews do not count as meals or earn habit credit. The temporary image is deleted on success or explicit removal. Failed reviews retain it for retry. The existing instant recognition route and its manual correction panel remain available.

Community likes are idempotent per user/post. Comments require a visible post; the author or demo moderator can delete them. Reports require a different author, allow one report per reporter/post, and are resolved by a moderator as dismissed or removed. Reported content is not hidden automatically. The seeded Demo Student has moderator role; the peer does not.

Reward credits are granted once per habit per Hong Kong local day. Confirmed menu meals, saved photo meals, explicit Community shares and completed workout plans qualify. Post removal appends a credit reversal. The ledger and redemptions are private to the current user. Badges have no cash value, and no recommendation click earns credits.

Real food scopes are `hkust`, `lohas`, `tko`, `hang_hau` and `tai_po_tsai`. Published dishes are browseable references. They carry no inferred allergen or nutrient values and are separate from the recordable demo catalog and its nutritional ranking.

`/menu-locations` returns a location ID, name, area, landmark coordinates and map source for locations with published dishes. The browser ranks them locally and sends `location_id` with the usual filters for the selected mall or other food location.

Published dishes and exercises optionally carry `source_photo` (`url`, `source_url`, `alt`, `credit`). Dishes with photos sort first. The image is loaded from the original provider and links back to its source page.

The default **Today** view requests meal and workout suggestions based on saved settings and confirmed activity. Four-week progress is available in **Progress**. Menu meals and confirmed photo meals contribute to `history_context` over the latest seven Hong Kong dates. Repeating the same menu item on at least two distinct days reduces that item’s fit score to favor variety. The run stores the history snapshot in `scoring_config`. Earlier runs can have a null history context. Automatic workout focus prefers compatible groups with no recorded session, then the least recently trained group. The browser shows today’s completion after the user confirms a workout.

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

Errors use `{"error":{"code":"http_404","message":"..."}}` for HTTP errors and `validation_error` for malformed inputs. Unavailable demo auth and assistant configuration return 503, assistant timeouts return 504, assistant upstream/invalid-content failures return 502, moderator-only access returns 403, missing or foreign objects return 404, duplicate confirmation/sharing/reporting or insufficient credits returns 409, and invalid fields return 422. List endpoints have bounded limits.
