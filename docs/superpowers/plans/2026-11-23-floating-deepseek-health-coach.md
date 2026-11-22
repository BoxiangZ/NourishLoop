# Floating DeepSeek Health Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a transient, data-grounded DeepSeek coaching experience and simplify NourishLoop's navigation and information hierarchy without removing existing food, photo, workout, history, community, reward, or profile features.

**Architecture:** Add an isolated `assistant` backend module that builds a read-only Hong Kong-local daily context and calls a dedicated DeepSeek Chat Completions provider at most once per user action. Mount a global floating ring coach in the existing app shell, consolidate five primary destinations, and place full report generation in Progress with no persistence.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, httpx, pytest, Next.js 15, React 19, TypeScript, Vitest, Testing Library, Tailwind/global CSS.

**Spec:** `docs/superpowers/specs/2026-11-23-floating-deepseek-health-coach-design.md`

## Global Constraints

- Work from branch `wzy/5534/demo`, based on `origin/boxiang/w07-midterm` commit `4a0caf6`.
- Preserve all existing meal, photo meal, workout, history, community, reward, and profile behavior.
- Keep the active modular monolith boundaries: routers validate/delegate, services own workflows, persistence stays in query/model code, and the pure recommendation/workout engines do not depend on providers.
- Use `APP_ENV=development` and `DEMO_AUTH_ENABLED=true` only for demo identity; do not add a production bypass.
- DeepSeek is independent from OpenRouter. Use `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL=https://api.deepseek.com`, `DEEPSEEK_MODEL=deepseek-chat`, and `DEEPSEEK_TIMEOUT_SECONDS=25`.
- Use at most one DeepSeek HTTP request for each `/assistant/ask` or `/assistant/daily-report` user action.
- Do not automatically retry provider failures.
- Do not persist questions, answers, reports, chat history, or conversation context.
- Do not add an Alembic migration.
- Build assistant context only from confirmed meals, saved photo meal records, and completed workout sessions for the current `Asia/Hong_Kong` day.
- Exclude user IDs, display names, images, image paths, developer AI logs, community data, planned meals, incomplete workout plans, rewards, and transaction history from assistant context.
- Do not send prior questions or answers on a subsequent assistant request.
- Keep model output as plain text; never render it as HTML.
- Keep all UI copy in English.
- Run `python -m scripts.generate_api_types` after changing Pydantic contracts and commit generated client files.

---

### Task 1: Add Assistant Contracts and Daily Context Builder

**Files:**
- Create: `apps/api/modules/assistant/__init__.py`
- Create: `apps/api/modules/assistant/schemas.py`
- Create: `apps/api/modules/assistant/context.py`
- Create: `tests/integration/test_assistant_context.py`

**Interfaces:**
- Produces: `AssistantAskRequest(question: str)`
- Produces: `AssistantAnswerRead(answer: str)`
- Produces: `DailyCoachReport(headline, nutrition_insight, activity_insight, next_actions, limitations)`
- Produces: `AssistantContext`
- Produces: `build_today_context(db: Session, user: User, day: date | None = None) -> AssistantContext`

- [ ] **Step 1: Write the failing context and contract tests**

```python
from datetime import datetime, timezone

from apps.api.modules.assistant.context import build_today_context
from apps.api.modules.assistant.schemas import AssistantAskRequest, DailyCoachReport
from apps.api.modules.identity.models import User


def test_ask_request_trims_question_and_rejects_blank_values():
    assert AssistantAskRequest(question="  dinner?  ").question == "dinner?"

    try:
        AssistantAskRequest(question="   ")
    except ValueError:
        pass
    else:
        raise AssertionError("blank question should fail")


def test_report_contract_rejects_more_than_three_actions():
    try:
        DailyCoachReport(
            headline="Today",
            nutrition_insight="Meals logged.",
            activity_insight="No completed workout yet.",
            next_actions=["one", "two", "three", "four"],
            limitations=[],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("four actions should fail")


def test_context_includes_only_confirmed_today_food_and_completed_workouts(nl_stack):
    client, session_factory = nl_stack
    menu_item = client.get("/api/v1/menu-items").json()[0]
    decision = client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    ).json()
    client.post(
        "/api/v1/meal-logs", json={"decision_id": decision["id"], "servings": 1}
    )
    client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    )

    workout = client.post(
        "/api/v1/workouts/recommend", json={"focus": "back", "minutes": 30}
    ).json()
    client.post(
        "/api/v1/workouts/sessions",
        json={"plan_id": workout["id"], "duration_min": 30},
    )
    client.post(
        "/api/v1/workouts/recommend", json={"focus": "legs", "minutes": 30}
    )

    with session_factory() as db:
        user = db.get(User, "demo-student")
        context = build_today_context(db, user)

    assert context.meal_count == 1
    assert len(context.menu_meals) == 1
    assert context.menu_meals[0].name == menu_item["name"]
    assert len(context.workouts) == 1
    assert context.workouts[0].duration_min == 30
    assert "user_id" not in context.model_dump_json()


def test_context_uses_hong_kong_day_boundaries(nl_stack):
    client, session_factory = nl_stack
    from apps.api.modules.tracking.models import MealLog

    menu_item = client.get("/api/v1/menu-items").json()[0]
    decision = client.post(
        "/api/v1/decisions", json={"menu_item_id": menu_item["id"]}
    ).json()
    logged = client.post(
        "/api/v1/meal-logs", json={"decision_id": decision["id"], "servings": 1}
    ).json()

    with session_factory() as db:
        row = db.get(MealLog, logged["id"])
        row.consumed_at = datetime(2026, 11, 22, 15, 59, tzinfo=timezone.utc)
        db.commit()
        user = db.get(User, "demo-student")
        context = build_today_context(db, user, day=datetime(2026, 11, 23).date())

    assert context.menu_meals == []
```

- [ ] **Step 2: Run the tests to verify the module is missing**

Run:

```bash
python -m pytest tests/integration/test_assistant_context.py -v
```

Expected: collection fails because `apps.api.modules.assistant` does not exist.

- [ ] **Step 3: Implement the assistant schemas**

Create typed, length-bounded models:

```python
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

NonBlank160 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
NonBlank500 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
ActionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)]


class AssistantAskRequest(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]


class AssistantAnswerRead(BaseModel):
    answer: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)
    ]


class DailyCoachReport(BaseModel):
    headline: NonBlank160
    nutrition_insight: NonBlank500
    activity_insight: NonBlank500
    next_actions: list[ActionText] = Field(max_length=3)
    limitations: list[ActionText] = Field(max_length=3)


class NutritionContext(BaseModel):
    calories_kcal: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MenuMealContext(BaseModel):
    name: str
    servings: float
    consumed_at: datetime
    nutrition: NutritionContext


class PhotoMealContext(BaseModel):
    food_names: list[str]
    notes: str
    review_status: Literal["not_requested", "pending", "processing", "completed", "failed"]
    nutrition_status: Literal["complete", "partial", "none"]
    nutrition: NutritionContext | None
    unresolved_foods: list[str]


class WorkoutContext(BaseModel):
    focus: str
    stage: str
    duration_min: int
    exercise_names: list[str]
    completed_at: datetime


class WorkoutProfileContext(BaseModel):
    stage: str
    equipment: list[str]
    days_per_week: int


class AssistantContext(BaseModel):
    date: date
    goal: str
    daily_calorie_target: float | None
    dietary_preferences: list[str]
    allergies: list[str]
    nutrition_totals: NutritionContext
    meal_count: int
    menu_meals: list[MenuMealContext]
    photo_meals: list[PhotoMealContext]
    workouts: list[WorkoutContext]
    workout_profile: WorkoutProfileContext | None
```

Use Pydantic's trimming validator already supplied by `StringConstraints`. If trimming occurs
after minimum-length validation in the installed Pydantic version, add this explicit validator:

```python
    @field_validator("question")
    @classmethod
    def nonblank_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question cannot be blank")
        return value
```

- [ ] **Step 4: Implement the read-only context builder**

Use the same Hong Kong-local day conversion as tracking:

```python
HK_ZONE = ZoneInfo("Asia/Hong_Kong")


def _day_bounds(day: date | None) -> tuple[date, datetime, datetime]:
    local_day = day or datetime.now(HK_ZONE).date()
    start_local = datetime.combine(local_day, time.min, tzinfo=HK_ZONE)
    end_local = start_local + timedelta(days=1)
    return (
        local_day,
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )
```

Query `MealLog`, `PhotoMealRecord`, and `WorkoutSession` directly with those bounds. Join
`MenuItem` for menu meal names and `WorkoutPlan` for workout focus/stage/prescription. Convert
photo JSON food objects to names. Reuse `session_read(db, session, plan)` from
`apps.api.modules.workouts.service` to resolve exercise names.

Get goal/profile through identity service. Read the workout profile with `db.get` so a GET-like
assistant request never creates one. Build `nutrition_totals` from `daily_summary(db, user,
local_day)`. Keep `build_today_context` free of provider imports.

- [ ] **Step 5: Run the focused tests**

Run:

```bash
python -m pytest tests/integration/test_assistant_context.py -v
```

Expected: PASS.

- [ ] **Step 6: Run the existing tracking, photo, and workout tests**

Run:

```bash
python -m pytest tests/integration/test_nourishloop_flow.py tests/integration/test_photo_meals.py tests/integration/test_places_workouts.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/api/modules/assistant tests/integration/test_assistant_context.py
git commit -m "feat(api): build daily assistant context"
```

---

### Task 2: Add the Isolated DeepSeek Provider

**Files:**
- Modify: `apps/api/core/config.py`
- Modify: `.env.example`
- Create: `apps/api/modules/assistant/provider.py`
- Create: `tests/unit/test_deepseek_assistant_provider.py`

**Interfaces:**
- Consumes: `AssistantContext`, `DailyCoachReport`
- Produces: `AssistantLLMProvider` protocol with `answer(question, context) -> str` and `report(context) -> DailyCoachReport`
- Produces: `DeepSeekChatProvider(settings, transport=None)`
- Produces exceptions: `AssistantConfigurationError`, `AssistantTimeoutError`, `AssistantUnavailableError`, `AssistantResponseError`

- [ ] **Step 1: Write failing provider tests**

```python
import json

import httpx
import pytest

from apps.api.core.config import Settings
from apps.api.modules.assistant.provider import (
    AssistantConfigurationError,
    AssistantResponseError,
    DeepSeekChatProvider,
)
from apps.api.modules.assistant.schemas import AssistantContext


def context() -> AssistantContext:
    return AssistantContext(
        date="2026-11-23",
        goal="eat_healthier",
        daily_calorie_target=1900,
        dietary_preferences=[],
        allergies=[],
        nutrition_totals={
            "calories_kcal": 800,
            "protein_g": 35,
            "carbs_g": 90,
            "fat_g": 25,
        },
        meal_count=2,
        menu_meals=[],
        photo_meals=[],
        workouts=[],
        workout_profile=None,
    )


def test_answer_uses_one_deepseek_chat_request():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Choose a protein-forward meal."}}]},
        )

    settings = Settings(
        _env_file=None,
        deepseek_api_key="test-key",
        deepseek_base_url="https://deepseek.test",
    )
    result = DeepSeekChatProvider(
        settings, transport=httpx.MockTransport(handler)
    ).answer("What should I eat?", context())

    assert result == "Choose a protein-forward meal."
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["model"] == "deepseek-chat"
    assert "What should I eat?" in body["messages"][-1]["content"]


def test_report_validates_json_without_retry():
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "headline": "A steady day.",
                            "nutrition_insight": "Two meals are logged.",
                            "activity_insight": "No workout is completed.",
                            "next_actions": ["Choose a balanced dinner."],
                            "limitations": ["No completed workout is recorded."],
                        })
                    }
                }]
            },
        )

    report = DeepSeekChatProvider(
        Settings(_env_file=None, deepseek_api_key="test-key"),
        transport=httpx.MockTransport(handler),
    ).report(context())

    assert report.headline == "A steady day."
    assert calls == 1


def test_missing_key_does_not_make_request():
    with pytest.raises(AssistantConfigurationError):
        DeepSeekChatProvider(Settings(_env_file=None)).answer("Question", context())


def test_empty_answer_is_rejected():
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200, json={"choices": [{"message": {"content": "   "}}]}
        )
    )
    with pytest.raises(AssistantResponseError):
        DeepSeekChatProvider(
            Settings(_env_file=None, deepseek_api_key="test-key"), transport=transport
        ).answer("Question", context())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/unit/test_deepseek_assistant_provider.py -v
```

Expected: collection fails because settings fields and provider do not exist.

- [ ] **Step 3: Add settings**

```python
deepseek_api_key: SecretStr | None = None
deepseek_base_url: str = "https://api.deepseek.com"
deepseek_model: str = "deepseek-chat"
deepseek_timeout_seconds: float = Field(default=25.0, gt=0, le=120)
```

Add matching blank/default values to `.env.example`.

- [ ] **Step 4: Implement the provider**

The provider must:

- Raise `AssistantConfigurationError` before network access if the key is missing.
- Use `POST {deepseek_base_url.rstrip("/")}/chat/completions`.
- Send `Authorization: Bearer <key>` and `Content-Type: application/json`.
- Use exactly one `httpx.Client(...).post(...)` per method call.
- Send `model=settings.deepseek_model`.
- For `ask`, use `max_tokens=220`, `temperature=0.2`, and request one short plain-text answer.
- For `report`, use `max_tokens=900`, `temperature=0.1`,
  `response_format={"type": "json_object"}`, and validate with `DailyCoachReport.model_validate`.
- Put all health facts in compact JSON and instruct the model to treat them and the question as
  data, not instructions.
- Include the instruction to use only supplied facts, state absent records, avoid diagnoses, and
  never invent nutrition, workouts, or medical outcomes.
- Wrap `httpx.TimeoutException` as `AssistantTimeoutError`.
- Wrap other `httpx.HTTPError`, missing choices, and parse errors as
  `AssistantUnavailableError`.
- Wrap empty answers and invalid report JSON as `AssistantResponseError`.
- Never log request content, response content, the key, or the question.

Use this protocol:

```python
class AssistantLLMProvider(Protocol):
    def answer(self, question: str, context: AssistantContext) -> str: ...

    def report(self, context: AssistantContext) -> DailyCoachReport: ...
```

- [ ] **Step 5: Run provider tests**

Run:

```bash
python -m pytest tests/unit/test_deepseek_assistant_provider.py -v
```

Expected: PASS.

- [ ] **Step 6: Verify no OpenRouter import**

Run:

```bash
rg -n "openrouter|OPENROUTER" apps/api/modules/assistant
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add apps/api/core/config.py .env.example apps/api/modules/assistant/provider.py tests/unit/test_deepseek_assistant_provider.py
git commit -m "feat(api): add isolated DeepSeek coach provider"
```

---

### Task 3: Expose Assistant Service and API

**Files:**
- Create: `apps/api/modules/assistant/service.py`
- Create: `apps/api/modules/assistant/router.py`
- Modify: `apps/api/main.py`
- Create: `tests/integration/test_assistant_api.py`
- Generated: `packages/api-client/src/openapi.json`
- Generated: `packages/api-client/src/schema.ts`

**Interfaces:**
- Consumes: `build_today_context`, provider protocol and provider exceptions
- Produces: `ask_assistant(db, user, question, provider) -> AssistantAnswerRead`
- Produces: `create_daily_report(db, user, provider) -> DailyCoachReport`
- Produces: `assistant_provider() -> AssistantLLMProvider`
- Produces endpoints `POST /api/v1/assistant/ask` and `POST /api/v1/assistant/daily-report`

- [ ] **Step 1: Write failing API integration tests**

```python
import pytest
from fastapi import HTTPException

from apps.api.main import app
from apps.api.modules.assistant.router import assistant_provider
from apps.api.modules.assistant.schemas import DailyCoachReport


class FakeProvider:
    def __init__(self):
        self.answer_calls = 0
        self.report_calls = 0

    def answer(self, question, context):
        self.answer_calls += 1
        assert question == "What should I eat?"
        assert context.date.isoformat() == "2026-11-23"
        return "Choose a balanced meal."

    def report(self, context):
        self.report_calls += 1
        return DailyCoachReport(
            headline="A steady day.",
            nutrition_insight="Two meals are recorded.",
            activity_insight="No workout is completed.",
            next_actions=["Choose a balanced dinner."],
            limitations=["No workout is recorded."],
        )


def test_ask_uses_provider_once(nl_client):
    provider = FakeProvider()
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        response = nl_client.post(
            "/api/v1/assistant/ask",
            json={"question": "  What should I eat?  "},
        )
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert response.status_code == 200
    assert response.json() == {"answer": "Choose a balanced meal."}
    assert provider.answer_calls == 1


def test_ask_rejects_blank_and_oversized_questions(nl_client):
    assert nl_client.post(
        "/api/v1/assistant/ask", json={"question": "   "}
    ).status_code == 422
    assert nl_client.post(
        "/api/v1/assistant/ask", json={"question": "x" * 501}
    ).status_code == 422


def test_daily_report_returns_structured_content_without_persistence(nl_client):
    provider = FakeProvider()
    app.dependency_overrides[assistant_provider] = lambda: provider
    try:
        response = nl_client.post("/api/v1/assistant/daily-report")
    finally:
        app.dependency_overrides.pop(assistant_provider, None)

    assert response.status_code == 200
    assert response.json()["headline"] == "A steady day."
    assert provider.report_calls == 1

    from apps.api.core.database import Base

    assert not any("assistant" in name or "report" in name for name in Base.metadata.tables)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/integration/test_assistant_api.py -v
```

Expected: fails because the router and endpoints do not exist.

- [ ] **Step 3: Implement service orchestration and error mapping**

Implement:

```python
def ask_assistant(
    db: Session, user: User, question: str, provider: AssistantLLMProvider
) -> AssistantAnswerRead:
    context = build_today_context(db, user)
    return AssistantAnswerRead(answer=provider.answer(question, context))


def create_daily_report(
    db: Session, user: User, provider: AssistantLLMProvider
) -> DailyCoachReport:
    context = build_today_context(db, user)
    return provider.report(context)
```

Map exceptions to:

- `AssistantConfigurationError` -> `HTTPException(503, "Daily coach is not configured")`
- `AssistantTimeoutError` -> `HTTPException(504, "Daily coach timed out; please try again")`
- `AssistantUnavailableError` -> `HTTPException(502, "Daily coach is unavailable; please try again")`
- `AssistantResponseError` -> `HTTPException(502, "Daily coach returned an invalid response")`

Do not catch unrelated programming errors as provider failures.

- [ ] **Step 4: Implement the router and include it**

```python
router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


def assistant_provider() -> AssistantLLMProvider:
    return DeepSeekChatProvider(get_settings())


@router.post("/ask", response_model=AssistantAnswerRead)
def ask(
    payload: AssistantAskRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    provider: AssistantLLMProvider = Depends(assistant_provider),
):
    return ask_assistant(db, user, payload.question, provider)


@router.post("/daily-report", response_model=DailyCoachReport)
def daily_report(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    provider: AssistantLLMProvider = Depends(assistant_provider),
):
    return create_daily_report(db, user, provider)
```

Include `assistant_router` in `apps/api/main.py`.

- [ ] **Step 5: Run API tests**

Run:

```bash
python -m pytest tests/integration/test_assistant_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Generate and inspect API types**

Run:

```bash
python -m scripts.generate_api_types
rg -n "AssistantAskRequest|AssistantAnswerRead|DailyCoachReport" packages/api-client/src/schema.ts
```

Expected: all three generated types are present; generated endpoints appear in
`packages/api-client/src/openapi.json`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/main.py apps/api/modules/assistant tests/integration/test_assistant_api.py packages/api-client/src/openapi.json packages/api-client/src/schema.ts
git commit -m "feat(api): expose DeepSeek daily coach endpoints"
```

---

### Task 4: Add Client Methods and the Floating Coach

**Files:**
- Modify: `packages/api-client/src/client.ts`
- Create: `apps/web/src/features/dashboard/FloatingCoach.tsx`
- Create: `apps/web/src/features/dashboard/FloatingCoach.test.tsx`
- Modify: `apps/web/src/features/dashboard/AppShell.tsx`
- Modify: `apps/web/src/app/globals.css`

**Interfaces:**
- Consumes: `AssistantAnswerRead`, `DailyCoachReport`
- Produces: `api.askAssistant(question: string) -> Promise<AssistantAnswerRead>`
- Produces: `api.dailyCoachReport() -> Promise<DailyCoachReport>`
- Produces: `FloatingCoach()` with no props, mounted globally by `AppShell`

- [ ] **Step 1: Write failing floating coach tests**

```tsx
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import FloatingCoach from "./FloatingCoach";

const apiMock = vi.hoisted(() => ({ askAssistant: vi.fn() }));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe("FloatingCoach", () => {
  it("opens with the default greeting and replaces it with one answer", async () => {
    apiMock.askAssistant.mockResolvedValue({ answer: "Choose a balanced dinner." });
    render(<FloatingCoach />);

    fireEvent.click(screen.getByRole("button", { name: "Open daily coach" }));
    expect(screen.getByText("Ask me about today’s meals or movement.")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "What should I eat for dinner?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));

    await waitFor(() => expect(apiMock.askAssistant).toHaveBeenCalledWith(
      "What should I eat for dinner?",
    ));
    expect(await screen.findByText("Choose a balanced dinner.")).toBeTruthy();
    expect(screen.queryByText("Ask me about today’s meals or movement.")).toBeNull();
  });

  it("starts a new independent exchange without repeating the old answer", async () => {
    apiMock.askAssistant
      .mockResolvedValueOnce({ answer: "First answer." })
      .mockResolvedValueOnce({ answer: "Second answer." });
    render(<FloatingCoach />);

    fireEvent.click(screen.getByRole("button", { name: "Open daily coach" }));
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "First question?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("First answer.");

    fireEvent.click(screen.getByRole("button", { name: "Ask another question" }));
    fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
      target: { value: "Second question?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("Second answer.");

    expect(apiMock.askAssistant).toHaveBeenLastCalledWith("Second question?");
    expect(screen.queryByText("First answer.")).toBeNull();
  });

  it("uses a text fallback when speech recognition is unavailable", () => {
    render(<FloatingCoach />);
    fireEvent.click(screen.getByRole("button", { name: "Open daily coach" }));
    expect(screen.getByLabelText("Ask the daily coach")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start voice question" })).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm --filter @nourishloop/web test -- FloatingCoach.test.tsx
```

Expected: fails because the component and client method do not exist.

- [ ] **Step 3: Add client methods**

```ts
askAssistant: (question: string) =>
  request<AssistantAnswerRead>("/assistant/ask", json("POST", { question })),
dailyCoachReport: () =>
  request<DailyCoachReport>("/assistant/daily-report", { method: "POST" }),
```

Import the two generated schema types.

- [ ] **Step 4: Implement `FloatingCoach`**

State:

```ts
const [open, setOpen] = useState(false);
const [question, setQuestion] = useState("");
const [answer, setAnswer] = useState<string | null>(null);
const [submittedQuestion, setSubmittedQuestion] = useState("");
const [busy, setBusy] = useState(false);
const [error, setError] = useState("");
```

Required interactions:

- Ring button uses `aria-label="Open daily coach"`.
- On open, render exactly one greeting and focus the question input.
- Keep a `ref` to the ring and restore focus when closed.
- Escape and backdrop clicks close.
- `submit` trims the question, returns early when blank or busy, clears the previous answer,
  calls only `api.askAssistant(question)`, and stores only the current question/answer.
- `Ask another question` clears question, submitted question, answer, and error.
- Do not store exchanges in local storage, session storage, cookies, or module globals.

Speech support:

```ts
type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
};
```

If neither constructor exists, hide the microphone button and keep the text field. If
permission is denied, show a non-destructive text fallback message. The transcript populates the
editable input; it does not submit automatically.

- [ ] **Step 5: Add styles and mount globally**

Add `.nl-coach-ring`, `.nl-coach-blur`, `.nl-coach-dialogue`, and related classes. The overlay
must use a blur backdrop and a centered reading column with left-aligned text. On mobile, place
the ring above the bottom nav and safe-area inset.

Render `<FloatingCoach />` once inside `AppShell` after the main workspace and before the mobile
nav.

- [ ] **Step 6: Run floating coach tests**

Run:

```bash
pnpm --filter @nourishloop/web test -- FloatingCoach.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/api-client/src/client.ts apps/web/src/features/dashboard/FloatingCoach.tsx apps/web/src/features/dashboard/FloatingCoach.test.tsx apps/web/src/features/dashboard/AppShell.tsx apps/web/src/app/globals.css
git commit -m "feat(web): add floating DeepSeek coach"
```

---

### Task 5: Add the Progress Report

**Files:**
- Create: `apps/web/src/features/dashboard/DailyCoachReport.tsx`
- Create: `apps/web/src/features/dashboard/DailyCoachReport.test.tsx`
- Modify: `apps/web/src/features/dashboard/Dashboard.tsx`
- Modify: `apps/web/src/features/dashboard/Dashboard.test.tsx`
- Modify: `apps/web/src/app/globals.css`

**Interfaces:**
- Consumes: `api.dailyCoachReport()`
- Produces: `DailyCoachReport()` component with no props

- [ ] **Step 1: Write failing report tests**

```tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DailyCoachReport from "./DailyCoachReport";

const apiMock = vi.hoisted(() => ({ dailyCoachReport: vi.fn() }));
vi.mock("@nourishloop/api-client", () => ({ api: apiMock }));
afterEach(cleanup);

describe("DailyCoachReport", () => {
  it("generates one structured report on demand", async () => {
    apiMock.dailyCoachReport.mockResolvedValue({
      headline: "A steady day.",
      nutrition_insight: "Two meals are recorded.",
      activity_insight: "One workout is completed.",
      next_actions: ["Choose a balanced dinner."],
      limitations: ["Nutrition values are estimates."],
    });

    render(<DailyCoachReport />);
    expect(apiMock.dailyCoachReport).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));

    expect(await screen.findByText("A steady day.")).toBeTruthy();
    expect(screen.getByText("Two meals are recorded.")).toBeTruthy();
    expect(screen.getByText("One workout is completed.")).toBeTruthy();
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);
  });

  it("keeps one retry action after failure and does not retry automatically", async () => {
    apiMock.dailyCoachReport.mockRejectedValueOnce(new Error("Coach timed out"));
    render(<DailyCoachReport />);
    fireEvent.click(screen.getByRole("button", { name: "Generate daily coach report" }));
    expect(await screen.findByText("Coach timed out")).toBeTruthy();
    expect(apiMock.dailyCoachReport).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Retry daily coach report" })).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm --filter @nourishloop/web test -- DailyCoachReport.test.tsx
```

Expected: component missing.

- [ ] **Step 3: Implement `DailyCoachReport`**

Use local component state only. Show:

- `Generate daily coach report` initially.
- Disabled `Generating report…` pending state.
- Report headline, nutrition insight, activity insight, next actions, limitations.
- A safe alert and `Retry daily coach report` after failure.

No result should be written to storage. Unmount naturally discards state.

- [ ] **Step 4: Mount in Progress**

Place `<DailyCoachReport />` immediately after the summary card in the existing history screen.
Do not display it in the assistant, Food, Today, Move, or Community.

Update `Dashboard.test.tsx` API mocks with `dailyCoachReport: vi.fn()` and assert the report
button is present only when navigating to Progress.

- [ ] **Step 5: Run report and dashboard tests**

Run:

```bash
pnpm --filter @nourishloop/web test -- DailyCoachReport.test.tsx Dashboard.test.tsx
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/dashboard/DailyCoachReport.tsx apps/web/src/features/dashboard/DailyCoachReport.test.tsx apps/web/src/features/dashboard/Dashboard.tsx apps/web/src/features/dashboard/Dashboard.test.tsx apps/web/src/app/globals.css
git commit -m "feat(web): generate daily coach reports in progress"
```

---

### Task 6: Consolidate Navigation and Add Today Focus

**Files:**
- Create: `apps/web/src/features/dashboard/todayFocus.ts`
- Create: `apps/web/src/features/dashboard/todayFocus.test.ts`
- Create: `apps/web/src/features/dashboard/TodaySection.tsx`
- Create: `apps/web/src/features/dashboard/AppShell.test.tsx`
- Modify: `apps/web/src/features/dashboard/AppShell.tsx`
- Modify: `apps/web/src/features/dashboard/Dashboard.tsx`
- Modify: `apps/web/src/features/dashboard/Dashboard.test.tsx`
- Modify: `apps/web/src/app/globals.css`

**Interfaces:**
- Produces: `todayFocus({ mealCount, workoutMinutes }): { headline, action }`
- Produces: `TodaySection({ onNavigate, onAction })`
- Screen type: `"today" | "food" | "workouts" | "history" | "community" | "rewards" | "profile"`
- Primary nav labels: `Today`, `Food`, `Move`, `Progress`, `Community`

- [ ] **Step 1: Write failing focus and navigation tests**

```ts
import { describe, expect, it } from "vitest";
import { todayFocus } from "./todayFocus";

describe("todayFocus", () => {
  it("uses factual states without nutrition claims", () => {
    expect(todayFocus({ mealCount: 0, workoutMinutes: 0 })).toEqual({
      headline: "No meals are logged yet today.",
      action: "food",
    });
    expect(todayFocus({ mealCount: 2, workoutMinutes: 0 })).toEqual({
      headline: "Meals are logged; movement is still open.",
      action: "workouts",
    });
    expect(todayFocus({ mealCount: 0, workoutMinutes: 30 })).toEqual({
      headline: "Movement is logged; your next meal is still open.",
      action: "food",
    });
    expect(todayFocus({ mealCount: 2, workoutMinutes: 30 })).toEqual({
      headline: "You have checked in with food and movement today.",
      action: "history",
    });
  });
});
```

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AppShell from "./AppShell";

describe("AppShell navigation", () => {
  it("renders five health destinations and separates utilities", () => {
    render(
      <AppShell
        screen="today"
        me={null}
        busy={false}
        rewardBalance={1240}
        onNavigate={vi.fn()}
        onSwitchUser={vi.fn()}
      >
        <div>content</div>
      </AppShell>,
    );

    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav.textContent).toContain("Today");
    expect(nav.textContent).toContain("Food");
    expect(nav.textContent).toContain("Move");
    expect(nav.textContent).toContain("Progress");
    expect(nav.textContent).toContain("Community");
    expect(screen.getByRole("button", { name: "Open rewards store" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open profile" })).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pnpm --filter @nourishloop/web test -- todayFocus.test.ts AppShell.test.tsx
```

Expected: helper and new nav prop missing.

- [ ] **Step 3: Implement `todayFocus` and `TodaySection`**

`todayFocus` is a pure switch on `mealCount > 0` and `workoutMinutes > 0` returning exactly the
copy in the failing test.

`TodaySection`:

- Fetches current summary and workout sessions.
- Filters workouts to the current Hong Kong date using the date embedded in local browser data
  and `toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" })`.
- Sums today's workout minutes.
- Renders the `todayFocus` headline, one primary button based on the returned `action`, and a
  secondary pair of buttons labeled `Food` and `Move`.
- Does not show a macro table or raw history list.

- [ ] **Step 4: Consolidate the shell**

Change `Screen` to the interface above. Primary items:

```ts
const items = [
  { id: "today", label: "Today" },
  { id: "food", label: "Food" },
  { id: "workouts", label: "Move" },
  { id: "history", label: "Progress" },
  { id: "community", label: "Community" },
];
```

Add `rewardBalance: number` to `AppShell` props. Render:

```tsx
<button aria-label="Open rewards store" onClick={() => onNavigate("rewards")}>
  {rewardBalance.toLocaleString()} pts · Store
</button>
```

Keep the avatar profile button. Remove the old sidebar note and footer copy. Bottom mobile nav
uses the same five items.

- [ ] **Step 5: Remap Dashboard screens without losing features**

Implement URL compatibility:

- No `page` parameter -> `today`.
- `page=discover` -> `food` with browse mode.
- `page=for-you` -> `food` with recommendation mode.
- `page=workouts` -> `workouts`.
- `page=history` -> `history`.
- `page=community` -> `community`.
- `page=rewards` -> `rewards`.
- `page=profile` -> `profile`.

Add one Food mode control for `Explore` and `For you`. Place the current Discover browse content
under Explore and the current For You recommendation content under For you. Move the Real places
view under Food's Explore mode. Keep existing callbacks and API behavior.

Render `TodaySection` for `screen === "today"`. Pass actual `rewards?.balance ?? 0` to AppShell.
On initial refresh, calling `api.rewardOverview` already supplies the balance.

- [ ] **Step 6: Reduce default data density**

Use accessible `<details>` disclosures:

- Food: wrap search, filters, paged catalog, and community preview under
  `<details><summary>Browse all meals and places</summary>...</details>`. Keep the current
  recommended/first content visible.
- Move: keep the session recommendation visible. Wrap training context, exercise library, and
  completed workout history in separate `<details>` sections.
- Progress: replace the three equal statistic blocks with one sentence derived from
  `meal_count` and today's completed workout count, while retaining the existing date week,
  tabs, and list details.

Do not remove these controls or API functionality.

- [ ] **Step 7: Run focused frontend tests**

Run:

```bash
pnpm --filter @nourishloop/web test -- todayFocus.test.ts AppShell.test.tsx Dashboard.test.tsx FloatingCoach.test.tsx DailyCoachReport.test.tsx
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/features/dashboard/todayFocus.ts apps/web/src/features/dashboard/todayFocus.test.ts apps/web/src/features/dashboard/TodaySection.tsx apps/web/src/features/dashboard/AppShell.test.tsx apps/web/src/features/dashboard/AppShell.tsx apps/web/src/features/dashboard/Dashboard.tsx apps/web/src/features/dashboard/Dashboard.test.tsx apps/web/src/app/globals.css
git commit -m "feat(web): simplify navigation and daily focus"
```

---

### Task 7: Update Documentation and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/architecture/modules.md`
- Modify: `docs/api/contracts.md`
- Modify: `docs/operations.md`
- Modify: `docs/product/roadmap.md`

**Interfaces:**
- Consumes all prior tasks
- Produces current operator, API, and architecture documentation for the new coach

- [ ] **Step 1: Update environment and product documentation**

Document:

- DeepSeek settings and that the assistant cannot run without a key.
- The floating ring and browser-speech/text fallback.
- One call per ask/report action, no retry, and no persistence.
- The five primary destinations and top-bar reward store.
- The context allowlist and exclusions.
- The 502/503/504 failure behavior.

- [ ] **Step 2: Update API and architecture docs**

Add the two assistant endpoints, request/response examples, provider boundary, and explicit
statement that OpenRouter remains unchanged and DeepSeek is not used for ranking or stored
nutrition.

- [ ] **Step 3: Regenerate client artifacts**

Run:

```bash
python -m scripts.generate_api_types
git diff --exit-code packages/api-client/src/openapi.json packages/api-client/src/schema.ts
```

Expected: no diff after the generation command because Task 3 already committed generated
types.

- [ ] **Step 4: Run backend checks**

Run:

```bash
python -m pytest -q tests/unit tests/integration
ruff check .
```

Expected: all tests pass and Ruff reports no errors.

- [ ] **Step 5: Run frontend checks**

Run:

```bash
pnpm typecheck
pnpm lint
pnpm test:web
pnpm build
```

Expected: all commands exit 0.

- [ ] **Step 6: Run contract and security scans**

Run:

```bash
rg -n "openrouter|OPENROUTER" apps/api/modules/assistant || true
rg -n "localStorage|sessionStorage|document.cookie" apps/web/src/features/dashboard/FloatingCoach.tsx apps/web/src/features/dashboard/DailyCoachReport.tsx || true
rg -n "image_path|image_base64|review_log" apps/api/modules/assistant || true
```

Expected: no assistant OpenRouter dependency, no browser persistence, and no image/developer-log
field references.

- [ ] **Step 7: Review the final diff**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intended documentation changes are unstaged before commit.

- [ ] **Step 8: Commit**

```bash
git add README.md docs/architecture/overview.md docs/architecture/modules.md docs/api/contracts.md docs/operations.md docs/product/roadmap.md
git commit -m "docs: document DeepSeek coach and simplified navigation"
```

---

## Completion Checklist

- [ ] All seven task commits exist on `wzy/5534/demo`.
- [ ] Current meal, photo, workout, history, community, reward, and profile tests pass.
- [ ] The sidebar has five primary destinations and no Rewards/Profile row.
- [ ] The top bar exposes rewards balance/store and the avatar opens Profile.
- [ ] Today uses only factual no-food/no-workout/complete states.
- [ ] The floating coach shows one default greeting, one current question, and one answer.
- [ ] A repeated question sends no prior exchange and replaces the visible exchange.
- [ ] Speech recognition has a text fallback.
- [ ] Progress owns the full report UI and reports disappear on unmount/refresh.
- [ ] DeepSeek uses `deepseek-chat`, independent settings, and no OpenRouter imports.
- [ ] Each ask/report HTTP action performs at most one DeepSeek call.
- [ ] No assistant persistence or migration exists.
- [ ] Generated API files are current.
- [ ] Backend tests, Ruff, frontend typecheck, lint, tests, and build pass.
