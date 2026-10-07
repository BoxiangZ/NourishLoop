# API Draft — Diet Planning and Meal Analysis

Team **group14**. Proposed Week 5 contract; the current executable code still uses the starter case-triage API.

## 1. Shared rules

- JSON response envelope for asynchronous creation: target ID, job ID, status and status URL; respond `202` after durable record/job creation.
- Unknown resource: `404`; invalid body, quantity or timestamp: `422`; absent active plan, active duplicate job or stale revision: `409`.
- Unsupported upload type: `415`; excessive size: `413`. Validate decoded content separately from filename/MIME.
- Private demo uses one server-selected owner. Owner IDs in paths must match that owner; another owner's resource is not exposed. Multiuser release requires authentication/authorization before deployment.
- Eating times are ISO-8601 with an offset; persist UTC and report the user's timezone. Initially `Asia/Hong_Kong`.
- Examples use symbolic IDs. Numeric nutrition/target examples are synthetic fixtures, not recommendations or imported source values.

## 2. Profile and plan

`POST /users/{user_id}/profiles` → `201`. Persist a new snapshot rather than modifying one referenced by a plan. Inputs include height/weight, an allowed activity-level value and at least one target. Validate positive dimensions and goals, body-fat percentages within 0–100, supported units, and required fields of the selected target-generation method. Define final supported ranges and any extra method-specific fields during Week 5; do not leave implementation to an unconstrained prompt.

`GET /users/{user_id}/profiles/latest` → latest snapshot or `404`.

`POST /diet-plans` request:

```json
{"body_profile_id": "profile-id"}
```

Response `202`:

```json
{
  "diet_plan_id": "plan-id",
  "job_id": 101,
  "status": "pending",
  "status_url": "/jobs/101"
}
```

`GET /diet-plans/{plan_id}` → `200` with lifecycle, profile/job reference, targets, meal fractions and guidance when available, otherwise null result fields. Failed plans expose a safe error and do not replace an existing active plan. Activation/superseding are atomic.

`GET /users/{user_id}/diet-plans/active` → active plan or `404`.

## 3. Meal upload and retrieval

`POST /meals` is multipart/form-data:

| Field | Rule |
|---|---|
| `image` | One JPEG/PNG, maximum 10 MiB and 20 megapixels; decoded/re-encoded, model input long edge ≤1280 pixels |
| `diet_plan_id` | Required, active at submission, owned by demo user; bound to meal permanently |
| `meal_slot` | breakfast/lunch/dinner/snack, with a budget in that plan |
| `eaten_at` | Required offset-aware timestamp |
| `quantity_notes` | Optional bounded text, e.g. `150 g cooked beef; 2 large eggs`; 2000-character limit |

Generated file keys remain internal. A shared API/AI volume stores re-encoded images. Store no raw image in PostgreSQL. Cleanup removes a newly written image on failed database creation.

Response `202`:

```json
{
  "meal_id": "meal-id",
  "job_id": 102,
  "status": "uploaded",
  "status_url": "/jobs/102"
}
```

`GET /meals/{meal_id}` → `200`, meal metadata/status, latest analysis draft, `confirmed_revision`, and current confirmed result. Distinguish latest draft from confirmed revision so a new/late analysis is never mistaken for approved data.

`GET /meals/{meal_id}/analysis` returns an existing meal's workflow envelope:

- `202` while a job is pending/claimed and there is no result; include job ID/status URL.
- `200` for a schema-valid draft, including incomplete draft questions, or a confirmed result.
- `200` with `status=failed`, safe error code and allowed next actions when terminal processing failed; retrieving a persisted failure is successful retrieval.
- `404` for an unknown meal; no fabricated empty success result.

`GET /jobs/{job_id}` → `200`, type/state, attempts, claim/end time, next attempt, error code and safe summary. Browser polls every two seconds and stops at completed/failed; a completed recognition job may still leave the meal awaiting review.

## 4. Catalog and user confirmation

`GET /nutrition-foods?query=egg&limit=20&offset=0` searches bounded aliases/descriptions; limits 1–100. Return stable entry IDs, preparation, source/version, per-100-g energy/macros, missing nutrient fields, and supported portion IDs/unit/size/edible grams. No unsupported count conversion is synthesized.

`PUT /meals/{meal_id}/confirmation` replaces the complete effective item list, with optimistic revision checking:

```json
{
  "expected_revision": 0,
  "source_analysis_id": "analysis-id",
  "items": [
    {"nutrition_food_id": "beef-entry", "quantity": 150, "unit": "g"},
    {"nutrition_food_id": "egg-entry", "quantity": 2, "unit": "count", "food_portion_id": "large-egg-portion"}
  ],
  "change_reason": "Confirmed preparation, edible beef weight and egg size"
}
```

One to twenty items; positive quantities; normalized weight at most 5000 g per item; valid catalog and portion/preparation associations; nonempty reason up to 1000 characters. Missing required nutrition prevents confirmation. `source_analysis_id` may be null for manual entry, otherwise it must belong to the meal. Clients cannot override authoritative densities/totals.

Lock meal, check expected revision, resolve entries/conversions, calculate energy/macros/alignment, replace current items, append immutable snapshot, and mark `analyzed` in one transaction. Invalid input changes nothing; old/repeated revision returns `409`.

Response `200` includes revision number, normalized items, source/conversion snapshots, totals, budget ratios/differences, rule version, assumptions and current template feedback. If user quantities changed, old AI feedback remains archived, not shown as current explanation.

Manual confirmation is allowed for failed/uploaded/processing meals if a complete catalog-backed list is supplied. It records `input_mode=manual`; late processing cannot overwrite it. `GET /meals/{meal_id}/revisions` returns paginated immutable history with reason/time and source analysis.

## 5. Retry, history and daily comparison

`POST /jobs/{job_id}/retry` accepts an optional note and returns `202` with a new job ID. Only failed, still-unconfirmed targets can be retried; known configuration/quota failure should be corrected first. Reuse the validated input snapshot; corrected food quantities use confirmation rather than mutating the failed job. A new image creates a new meal. Return `409` if a job is active or a result already confirmed; retain old job evidence.

`GET /meals?date=YYYY-MM-DD&limit=20&offset=0` → local-day paginated history, including drafts/failures. Limits 1–100, nonnegative offset.

`GET /users/{user_id}/daily-summary?date=YYYY-MM-DD` → local date/timezone, confirmed energy/macros/meal count, unconfirmed count, and totals grouped by original plan ID. Convert local midnight boundaries to UTC; never use UTC-date grouping. Summarize current confirmed revisions only, not every historical revision or AI draft. A missing macro remains null/incomplete, not zero.

## 6. Internal AI service

Internal calls are not browser endpoints. `POST /generate-diet-plan` receives job ID and validated synthetic-profile snapshot for hosted demo inference; returns typed targets, meal fractions, guidance, provider/model metadata and original validated output. Required numeric fields are finite/positive and supported fractions sum to 1; reject invalid output before activation.

`POST /recognize-meal` receives meal/job IDs, generated image key, input revision, quantity notes and prompt version. AI resolves the key under its fixed mounted root and submits image bytes through its provider adapter. Proposed response:

```json
{
  "foods": [
    {"label": "cooked beef", "preparation": "cooked", "quantity": 150, "unit": "g", "quantity_source": "user_note"},
    {"label": "egg", "preparation": "unknown", "quantity": 2, "unit": "count", "size": "large", "quantity_source": "user_note"}
  ],
  "questions": ["Confirm egg preparation and source portion match"],
  "model_metadata": {"provider": "configured-provider", "model": "configured-model", "request_id": "request-id"},
  "prompt_version": "meal-recognition-v1"
}
```

Empty foods with an explicit unreadable/non-food reason is a valid review outcome. Bound types/counts/strings and reject malformed/non-finite output. Model claims cannot create catalog records or validated serving conversions.

`POST /explain-meal` receives computed complete totals, exact plan budget/rule label and assumptions, and produces short grounded feedback plus provider/prompt metadata. The worker owns catalog lookup/comparison. The feedback call is optional if no complete draft exists; if only explanation fails after recognition/calculation succeeded, persist the draft with template feedback and a warning. Log actual call counts without retaining sensitive prompts in normal logs.

## 7. Readiness and current limitations

API readiness checks database access and image-store availability. AI readiness reports configured model/provider mode and missing configuration; model preflight/quota checks are explicit, not expensive inference on every health request. Full deployment and integration evidence will be added as implemented. These contracts do not claim an existing endpoint, trained model, successful account access or nutrition import.
