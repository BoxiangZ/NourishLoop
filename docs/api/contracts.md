# API contracts

Current product routes are under `/api/v1`; OpenAPI is at `/openapi.json`. Run `python -m scripts.generate_api_types` after Pydantic changes and commit the generated `packages/api-client/src` files.

| Method | Path | Effect |
|---|---|---|
| GET | `/api/v1/health` | Database readiness |
| GET, PATCH | `/api/v1/me`, `/api/v1/me/profile` | Demo user and profile |
| GET, PUT | `/api/v1/me/goals` | Goal |
| GET | `/api/v1/venues`, `/api/v1/menu-items` | Fictional catalog |
| POST | `/api/v1/recommendations/jobs` | Persist pending job; 202 with job ID/status |
| GET | `/api/v1/recommendations/jobs/{id}` | Own job status and completed run |
| POST | `/api/v1/recommendations/meals` | Synchronous compatibility route |
| POST | `/api/v1/recommendations/{id}/feedback` | Helpfulness feedback |
| POST, GET | `/api/v1/decisions`, `/api/v1/me/decisions` | Plan/read decisions |
| POST, GET | `/api/v1/meal-logs`, `/api/v1/me/meal-logs` | Confirm/read consumed meals |
| GET | `/api/v1/me/daily-summary` | Confirmed totals for HK local day |
| POST, GET | `/api/v1/community/posts` | Explicitly share a confirmed log/read feed |
| DELETE | `/api/v1/community/posts/{id}` | Retract own post |

Demo private routes resolve identity on the server, never from a client-supplied user ID. Job reads and post removal check ownership. Community post creation checks that its meal log belongs to the current user; a meal can have one post. The feed shows a shared meal, illustrative nutrition snapshot, caption, and demo display name.

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

Errors use `{"error":{"code":"http_404","message":"..."}}` for HTTP errors and `validation_error` for malformed inputs. Unavailable demo auth returns 503, missing or foreign objects return 404, duplicate confirmation/sharing returns 409, and invalid fields return 422. List endpoints have bounded limits.
