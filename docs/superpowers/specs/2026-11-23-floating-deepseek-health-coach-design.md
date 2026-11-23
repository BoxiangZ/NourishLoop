# Floating DeepSeek Health Coach Design

Date: 2026-11-23

Branch: `wzy/5534/demo`

Base: `origin/boxiang/w07-midterm` at `4a0caf6`

## Summary

NourishLoop already combines meal recommendations, photo nutrition records, workout
sessions, history, community, and rewards. This change keeps those workflows and turns the
frontend from a collection of equally weighted data views into a daily health companion.

The visible product will have five primary destinations: Today, Food, Move, Progress, and
Community. Profile moves to the existing avatar action. Rewards becomes a compact store
entry in the top bar because it encourages repeated check-ins and is not a health record.

A global ring-shaped coach control sits at the bottom-right of the application. It opens a
blurred transparent layer with only one current question and one short answer. Users may ask
again, but every answer is independent: no conversation history or prior answer is sent to
the model. Full daily coaching remains a separate action in Progress and is not displayed by
the floating coach.

The coach uses a new, isolated DeepSeek provider. Existing OpenRouter photo review, photo
nutrition, meal explanation, and workout explanation behavior remains unchanged.

## Goals

- Make today's health status and next action easier to understand than raw metric grids.
- Preserve all existing meal, photo, workout, history, community, profile, and reward
  capabilities.
- Support browser voice input with a text fallback.
- Return one short answer for one user question from current confirmed data.
- Generate a structured full daily report only when requested from Progress.
- Use at most one DeepSeek LLM call for each user action.
- Keep questions, answers, and reports transient and outside the database.
- Maintain clear separation between suggestions, planned actions, and confirmed records.

## Non-goals

- No persistent chat, chat history, conversation memory, or multi-turn context.
- No new exercise data model or wearable integration.
- No report history, generated-report table, or historical report retrieval.
- No automatic retry, background worker, or streamed model response.
- No LLM-driven meal ranking, workout selection, nutrition calculation, or reward changes.
- No exposure of private data, source images, credentials, or developer review logs.
- No medical diagnosis, treatment, or guarantees about health outcomes.

## Product Information Architecture

### Primary navigation

The primary sidebar has five entries:

| Visible label | Responsibility |
|---|---|
| Today | One daily status conclusion, one primary next action, and secondary entry points into food or movement |
| Food | Current food plans, real places, photo meal check-in, meal recommendations, search, and filters |
| Move | Existing workout recommendations, exercise library, sessions, and workout history |
| Progress | Existing history records, date summary, and full daily coach report generation |
| Community | Existing posts, comments, reactions, reporting, and sharing |

The profile avatar opens Profile. The top bar contains a compact rewards store button showing
the current balance and opening the existing Rewards experience. Rewards is not a section of
Progress.

Existing screen URLs remain compatible where practical:

- `discover` and `for-you` resolve into the Food experience while preserving the requested
  mode when possible.
- `history` resolves to Progress.
- `rewards` continues to open the rewards store from its top-bar entry.
- `profile`, `community`, and `workouts` remain reachable through their existing concepts.

The frontend continues to render one active screen at a time and does not create duplicate
assistant or nutrition views.

### Information hierarchy

Each primary page leads with:

1. One plain-language status or conclusion.
2. One primary action.
3. A small number of directly relevant details.

Secondary content is progressively disclosed rather than removed:

- Today shows at most two headline indicators if needed, with a status-first sentence.
- Food places search, filters, full catalog, places, and community preview behind secondary
  controls or disclosure sections.
- Move leads with a suggested session; training context, library, and history remain
  available below.
- Progress replaces the three equal-weight statistic cards with a short sentence such as
  "2 meals and 1 workout today; protein is below the current pace" while retaining the
  detailed history tabs and date selection.

The existing fictional/estimated labels, confidence language, and confirmation semantics
must remain visible wherever nutrition or recommendations appear.

### Today focus rules

Today does not make a medical inference and does not call an LLM on page load. A small pure
frontend helper derives one factual state from the existing daily-summary and completed-workout
data:

| Data present | Today conclusion | Primary action |
|---|---|---|
| No confirmed meals | "No meals are logged yet today." | Check in or choose a meal |
| Meals, no completed workout | "Meals are logged; movement is still open." | View a workout suggestion |
| Workout, no confirmed meals | "Movement is logged; your next meal is still open." | Choose a meal |
| Both meals and workout | "You have checked in with food and movement today." | Review progress or continue the day |

This helper produces presentation copy only. It does not set nutrition targets, estimate
calories burned, diagnose a deficiency, or alter recommendation ranking. It uses the existing
`me`, `daily-summary`, `meal-logs`, and workout-session data and requires no additional backend
endpoint.

## Floating Coach Experience

### Entry control

- A 56-60 px ring-shaped control is fixed to the bottom-right viewport corner.
- On mobile it sits above the bottom navigation and respects the safe-area inset.
- It is available on every primary screen.
- It has an accessible name, visible focus treatment, and does not rely on color alone.

### Overlay

Opening the coach displays a centered, full-viewport transparent layer:

- Background content is blurred with `backdrop-filter: blur(...)` and a lightweight tint for
  text contrast.
- Text is left-aligned inside a centered reading column.
- No dashboard cards, nutrition summary, workout summary, report link, activity log, or
  prior exchange appears.
- The overlay opens with the single greeting:
  "Ask me about today's meals or movement."
- Escape, a close control, and clicking outside the reading column close the overlay.

### Asking

- The user can tap a microphone control or enter text.
- Browser speech recognition populates an editable transcript before sending.
- If speech recognition is unavailable or permission is denied, the text input remains and
  the user can continue without an API call for speech.
- Empty or whitespace-only questions cannot be submitted.
- While a request is pending, duplicate submission is disabled and a lightweight thinking
  state is shown.
- Success replaces the greeting with the current question and exactly one short answer.
- "Ask another question" resets the visible exchange and starts a new independent request.
- Starting another question does not send the previous question or answer to the backend.
- Closing the overlay discards the current visible exchange.

No assistant exchange is persisted in the browser, database, or server logs.

## Daily Coach Report

Progress displays `Generate daily coach report` near the date summary.

- Clicking the button sends one request using today's Hong Kong-local date.
- The report appears in Progress below the summary.
- Loading, failure, and retry states are local to that report section.
- Navigating away or refreshing clears the report.
- The floating coach does not display or link to metric summaries; the report only exists in
  Progress.

The validated report has this shape:

```json
{
  "headline": "One-sentence conclusion.",
  "nutrition_insight": "What the confirmed food records support.",
  "activity_insight": "What the completed workout records support.",
  "next_actions": [
    "A specific, bounded next action."
  ],
  "limitations": [
    "Relevant missing or estimated data."
  ]
}
```

Constraints:

- `headline` is at most 160 characters.
- `nutrition_insight` and `activity_insight` are each at most 500 characters.
- `next_actions` contains at most three non-empty strings, each at most 240 characters.
- `limitations` contains at most three non-empty strings, each at most 240 characters.
- Every field must be based only on supplied context.
- If there are no meals or no completed workouts, the report says the record is absent instead
  of inventing a behavior.

## Assistant Data Context

The backend builds a fresh read-only `AssistantContext` for the current authenticated user and
the current `Asia/Hong_Kong` local date. The client cannot supply or override health facts.

The context contains:

- Goal type and daily calorie target.
- Dietary preferences and allergies.
- Daily nutrition totals and confirmed meal count.
- Confirmed menu meals: item name, servings, consumed time, and nutrition snapshot.
- Confirmed photo meal records: visible food names, user notes, review status, nutrition status,
  nutrition when available, unresolved foods, and limitations.
- Completed workout sessions: focus, stage, duration, exercise names, and completion time.
- Workout profile stage, available equipment, and days-per-week target when present.

The context excludes:

- User ID and display name.
- Raw or base64 images.
- Image paths or photo bytes.
- Developer-only AI review logs and provider diagnostics.
- Community posts, comments, reactions, and reports.
- Planned decisions that were not confirmed.
- Workout plans that were not completed.
- Reward balances and transaction history.

Photo rows with `review_status` `completed` or `not_requested` are confirmed. Their `complete`
nutrition snapshots contribute to daily totals; `partial` snapshots are included per row as
matched-food estimates without being represented as aggregate intake. Rows with `pending`,
`processing`, or `failed` status are status-only and include no row nutrition or daily intake
contribution. Only confirmed food records count as intake. Only completed workout sessions count
as movement. The service must not call helpers that create missing workout profiles or otherwise
mutate data while constructing context.

The context is serialized as compact JSON. The user's question is passed separately and is
treated as untrusted input. System instructions must tell the model to ignore instructions in
the question or context that attempt to change its role, reveal secrets, or violate grounding.

## DeepSeek Provider

The assistant uses an isolated provider interface:

```text
AssistantLLMProvider.answer(question, context) -> str
AssistantLLMProvider.report(context) -> structure matching the report contract
```

The initial implementation is `DeepSeekChatProvider` using DeepSeek's OpenAI-compatible Chat
Completions interface. It does not import or call OpenRouter code.

Settings:

| Setting | Default |
|---|---|
| `DEEPSEEK_API_KEY` | unset |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-flash` |
| `DEEPSEEK_TIMEOUT_SECONDS` | `25` |

Provider behavior:

- Use one HTTP POST for one user action.
- Use `deepseek-flash` for both short answers and the full report.
- Reserve 2400 completion tokens for a short answer and 2400 for a report because
  `deepseek-flash` may spend part of the budget on reasoning content before final text.
- Request a plain answer for `ask` and JSON output for `daily-report`.
- Do not stream.
- Do not retry automatically.
- Do not log the API key, question, context, raw response, authorization header, or generated
  answer.
- Validate response content before returning it to the service.

The assistant provider does not influence deterministic recommendation scores, selected
workouts, stored nutrition, rewards, or Community behavior.

## API Contracts

### `POST /api/v1/assistant/ask`

Request:

```json
{ "question": "How should I plan dinner?" }
```

Validation:

- `question` is trimmed.
- Length is 1-500 characters after trimming.

Response:

```json
{ "answer": "One short grounded answer." }
```

The answer must be non-empty and at most 600 characters. The prompt requests approximately 70
English words so the display remains a short response rather than a report.

### `POST /api/v1/assistant/daily-report`

Request body: none.

Response: the structured report contract described above.

Both endpoints require the existing demo-capable current-user dependency. Demo identity still
works only when `APP_ENV=development` and `DEMO_AUTH_ENABLED=true`; this work adds no production
authentication bypass.

No Alembic migration is required.

## Backend Components

New module: `apps/api/modules/assistant`

- `schemas.py`: request, short-answer response, report, and validated report components.
- `context.py`: read-only today context builder and compact serialization.
- `provider.py`: assistant protocol, DeepSeek adapter, provider exceptions, and response
  validation.
- `service.py`: orchestration, error mapping, and prompt construction.
- `router.py`: validated endpoints delegating to the service.

The router is included in `apps/api/main.py`. The existing tracking, identity, catalog,
recommendation, workout, community, and reward routers remain unchanged in behavior.

## Error Handling

| Condition | HTTP status | User-facing behavior |
|---|---|---|
| Missing or empty DeepSeek key | 503 | Coach unavailable; configuration message without secrets |
| DeepSeek timeout | 504 | Retryable "Coach timed out" state |
| Other upstream/provider failure | 502 | Retryable "Coach is unavailable" state |
| Empty or invalid short answer | 502 | Retryable invalid-response state |
| Missing or invalid report JSON | 502 | Retryable invalid-response state |
| Invalid local request | 422 | Existing validation error envelope |
| Demo identity unavailable | 503 | Existing authentication behavior |

Each retry is an explicit user action and creates at most one additional LLM call. There is no
automatic retry in the frontend or backend.

## Security and Privacy

- API credentials remain server-side.
- The assistant context is built from the authenticated user's database records.
- No photo or image path is sent to DeepSeek.
- No generated content is persisted.
- Provider errors use fixed safe messages rather than raw upstream bodies.
- The user question and generated answer are not included in application logs.
- The existing development-only demo identity boundary remains intact.
- Model output is treated as untrusted text and rendered as text, never raw HTML.

## Accessibility and Responsive Behavior

- The ring has `aria-label` and keyboard activation.
- The overlay moves focus into the question field and restores focus to the ring on close.
- Escape closes the overlay.
- The question, pending status, and answer are announced through appropriate live-region/status
  semantics without repeatedly announcing partial content.
- Speech input has a text alternative.
- The overlay uses sufficient contrast over the blurred background.
- Mobile placement does not cover the bottom navigation.
- Existing visible focus styles remain.

## Frontend Components

- `FloatingCoach.tsx`: ring control, overlay lifecycle, speech/text input, submit, current
  exchange, close behavior, and accessibility.
- `FloatingCoach.test.tsx`: interaction and speech fallback tests.
- `DailyCoachReport.tsx`: report button, pending state, validated report rendering, and retry.
- `DailyCoachReport.test.tsx`: report states and clearing behavior.
- `todayFocus.ts` and `todayFocus.test.ts`: deterministic factual-state selection and action
  mapping.
- `AppShell.tsx`: five primary navigation items, top-bar rewards store entry, avatar profile
  action, and the global floating coach mount point.
- `Dashboard.tsx`: map consolidated navigation to the existing screens and progressively
  disclose secondary content.
- `globals.css`: compact navigation, current-action hierarchy, ring/overlay, blur, and mobile
  layout styles.

The frontend imports API types generated from the FastAPI OpenAPI contract. It does not
construct health facts for the assistant request.

## Testing Strategy

### Backend unit tests

- Context uses the Hong Kong-local day boundaries.
- Confirmed menu meals, `completed` and `not_requested` photo records, and completed workouts are
  included.
- Complete photo nutrition is included per row and in totals for confirmed statuses; partial
  photo nutrition remains per-row context and is excluded from aggregate totals.
- Planned meals, incomplete workout plans, community content, IDs, images, and review logs are
  excluded.
- Missing workout profile does not create a database row.
- Context handles days with no meals, no workouts, partial photo nutrition, failed photo review,
  and no calorie target.
- Ask and report prompts request no prior exchange and contain no forbidden fields.
- Provider sends exactly one HTTP request and uses the configured DeepSeek model/base URL.
- Provider validates empty answers and malformed report JSON without a second call.
- Missing key, timeout, and upstream failures map to safe HTTP errors.

### Backend integration tests

- `/assistant/ask` accepts a valid question, rejects empty/oversized input, and returns a short
  answer with a fake provider.
- `/assistant/daily-report` returns every required report field and no persisted row.
- Cross-user data is never included.
- Existing demo identity behavior applies.
- Existing meal, photo, workout, history, community, and reward flows continue to pass.

### Frontend tests

- AppShell renders exactly five primary nav buttons and separates rewards/profile.
- Today focus maps no food, no movement, and complete check-in states to the specified copy and
  action without making a nutrition or medical claim.
- Ring opens the overlay with the default greeting and centers only the dialogue content.
- Text question and answer replace the greeting.
- A subsequent question replaces the previous exchange and sends no previous answer.
- Speech recognition populates an editable transcript.
- Missing speech support and permission denial leave text input usable.
- Pending state prevents duplicate sends.
- Errors are retryable and do not auto-retry.
- Escape, close control, and outside click close the overlay.
- Progress report button renders loading, structured report, and failure/retry states.
- Navigating away or remounting clears the report.
- Existing Dashboard, photo meal, workout, community, reward, and profile tests continue to
  pass after navigation remapping.

### Verification commands

```bash
python -m pytest -q tests/unit tests/integration
ruff check .
python -m scripts.generate_api_types
pnpm typecheck
pnpm lint
pnpm test:web
pnpm build
```

## Documentation

Update:

- `README.md` with the DeepSeek demo flow and required environment.
- `.env.example` with the DeepSeek settings.
- `docs/architecture/overview.md` and `modules.md` with the assistant boundary.
- `docs/api/contracts.md` with both new endpoints.
- `docs/operations.md` with provider failure behavior and the one-call/no-persistence policy.
- `docs/product/roadmap.md` only where the implemented state changes.

Generate and commit `packages/api-client/src/openapi.json` and
`packages/api-client/src/schema.ts`.

## Acceptance Criteria

- The app retains every current product capability and all existing tests pass.
- The primary sidebar has five task-based destinations; rewards and profile are utilities.
- The right-bottom ring opens a centered blurred overlay with left-aligned text and the default
  greeting.
- The overlay displays only the current question and one answer, never other health metrics or
  prior exchanges.
- Multiple questions are possible, but no question or answer context is sent or stored.
- A full structured report is generated only from Progress and disappears without persistence.
- DeepSeek is configured independently from OpenRouter and uses `deepseek-flash`.
- Each ask/report action causes at most one model call and has a manual retry path.
- Only confirmed food and completed workouts are used as health facts.
- No migration is added, no report/chat row is written, and no sensitive image or developer log
  reaches DeepSeek.
- Backend, frontend, type generation, lint, tests, and build checks pass.
