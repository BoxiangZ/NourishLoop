# Rich Assistant Context and Demo Activity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the DeepSeek coach with safe menu/venue/plan context, conversational specific meal recommendations, and seven days of restart-safe fictional demo activity.

**Architecture:** Keep the existing assistant router/service/provider boundary. Extend the read-only context builder, add a pure eligibility helper, reshape the provider payload into a documented JSON envelope, and add a separate development-only activity seed that Compose runs after the catalog seed.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, httpx, pytest, Next.js/React/TypeScript, Vitest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-11-23-rich-assistant-context-demo-data-design.md`

## Global Constraints

- Work from `wzy/5534/demo`; preserve the existing page, assistant, report, and API behavior.
- Short answers must be two to four natural conversational English sentences with no headings, bullets, numbered lists, tables, labels, or Markdown formatting.
- The answer limit becomes 1000 characters; the question limit remains 500.
- DeepSeek remains isolated from OpenRouter and uses `deepseek-flash`.
- At most one DeepSeek request per action; no automatic retry, stream, worker job, or persistence.
- Only server-marked `eligible=true` menu items may be recommended.
- Allergies are hard exclusions. Vegan/vegetarian are hard preferences. High-protein/high-fibre are soft preferences.
- Planned meals are future context and never consumed intake.
- Real venues are place-only; do not infer menus, prices, or nutrition.
- Context and prompt contain no user IDs, names, images, image paths, developer review logs, or conversation history.
- Demo activity seed runs only when `APP_ENV=development`, touches only `demo-student`, and is idempotent per Hong Kong date.
- Do not edit the already deferred demo-account-switch behavior.
- No new database table or Alembic migration.
- Regenerate and commit OpenAPI/client types after changing `AssistantAnswerRead`.

---

### Task 1: Extend Assistant Context, Catalog, Plans, and Eligibility

**Files:**
- Create: `apps/api/modules/assistant/eligibility.py`
- Modify: `apps/api/modules/assistant/schemas.py`
- Modify: `apps/api/modules/assistant/context.py`
- Modify: `tests/integration/test_assistant_context.py`
- Create: `tests/unit/test_assistant_eligibility.py`

**Interfaces:**
- Produces: `menu_eligibility(tags: list[str], allergens: list[str], dietary_preferences: list[str], allergies: list[str]) -> tuple[bool, list[str]]`
- Produces context models:
  - `PlannedMealContext`
  - `PlannedWorkoutContext`
  - `MenuCatalogItemContext`
  - `VenueDirectoryContext`
  - `DerivedIntakeContext`
- Extends `MenuMealContext` with `venue_name`, `venue_area`, and `price_hkd`.
- Extends `AssistantContext` with `planned_meals`, `workout_plans`, `menu_catalog`, `venue_directory`, and `derived`.
- Keeps `build_today_context(db: Session, user: User, day: date | None = None) -> AssistantContext` as the entry point.

- [ ] **Step 1: Write failing eligibility tests**

```python
from apps.api.modules.assistant.eligibility import menu_eligibility


def test_allergen_is_a_hard_exclusion():
    eligible, reasons = menu_eligibility(
        ["high_protein"], ["soy"], ["high_protein"], ["soy"]
    )
    assert eligible is False
    assert reasons == ["allergen_match"]


def test_vegan_and_vegetarian_are_hard_preferences():
    vegan = menu_eligibility([], [], ["vegan"], [])
    vegetarian_ok = menu_eligibility(
        ["vegetarian"], [], ["vegetarian"], []
    )
    vegetarian_bad = menu_eligibility(
        ["high_protein"], [], ["vegetarian"], []
    )
    assert vegan == (False, ["not_vegan"])
    assert vegetarian_ok == (True, [])
    assert vegetarian_bad == (False, ["not_vegetarian"])


def test_soft_preferences_do_not_exclude_menu_items():
    eligible, reasons = menu_eligibility(
        ["high_protein"], [], ["high_protein", "high_fibre"], []
    )
    assert eligible is True
    assert reasons == []


def test_reason_order_is_stable_when_multiple_rules_fail():
    eligible, reasons = menu_eligibility(
        ["vegetarian"], ["egg"], ["vegan"], ["egg"]
    )
    assert eligible is False
    assert reasons == ["allergen_match", "not_vegan"]
```

- [ ] **Step 2: Write failing context tests**

Add tests covering the structured new fields:

```python
def test_context_includes_plans_catalog_venues_and_derived_values(nl_stack):
    client, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    menu = client.get("/api/v1/menu-items").json()
    venues = client.get("/api/v1/venues?limit=100").json()
    chicken = next(item for item in menu if item["name"] == "Chicken grain bowl")
    salmon = next(item for item in menu if item["name"] == "Salmon quinoa plate")

    client.post("/api/v1/decisions", json={"menu_item_id": chicken["id"]})
    client.post("/api/v1/decisions", json={"menu_item_id": salmon["id"]})

    with session_factory() as db:
        user = db.get(User, "demo-student")
        context = build_today_context(db, user, day=fixed_day)

    planned_by_name = {meal.name: meal for meal in context.planned_meals}
    assert set(planned_by_name) == {"Salmon quinoa plate", "Chicken grain bowl"}
    assert all(meal.status == "planned" for meal in context.planned_meals)
    assert planned_by_name["Salmon quinoa plate"].venue_name == "Garden Counter (demo)"
    assert context.menu_catalog
    assert {entry.name for entry in context.menu_catalog} >= {
        "Chicken grain bowl",
        "Salmon quinoa plate",
    }
    assert context.venue_directory
    assert len(context.venue_directory) == len(venues)
    assert context.derived.planned_calories_kcal == 1250
    assert context.derived.planned_protein_g == 81
    assert context.derived.remaining_calories_kcal == 1900


def test_context_marks_allergy_and_strict_preference_items_ineligible(nl_stack):
    client, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    client.patch(
        "/api/v1/me/profile",
        json={
            "display_name": "Demo Student",
            "dietary_preferences": ["vegan"],
            "allergies": ["soy"],
        },
    )

    with session_factory() as db:
        user = db.get(User, "demo-student")
        context = build_today_context(db, user, day=fixed_day)

    by_name = {item.name: item for item in context.menu_catalog}
    assert by_name["Grilled tofu rice bowl"].eligible is False
    assert "allergen_match" in by_name["Grilled tofu rice bowl"].ineligibility_reasons
    assert by_name["Chicken grain bowl"].eligible is False
    assert "not_vegan" in by_name["Chicken grain bowl"].ineligibility_reasons
    assert by_name["Chickpea salad"].eligible is True


def test_context_includes_only_unfinished_workout_plans(nl_stack):
    client, session_factory = nl_stack
    fixed_day = date(2026, 11, 23)
    planned = client.post(
        "/api/v1/workouts/recommend", json={"focus": "legs", "minutes": 30}
    ).json()
    completed = client.post(
        "/api/v1/workouts/recommend", json={"focus": "back", "minutes": 30}
    ).json()
    client.post(
        "/api/v1/workouts/sessions",
        json={"plan_id": completed["id"], "duration_min": 30},
    )

    with session_factory() as db:
        user = db.get(User, "demo-student")
        context = build_today_context(db, user, day=fixed_day)

    assert [plan.id for plan in context.workout_plans] == [planned["id"]]
    assert context.workout_plans[0].exercise_names
```

Also extend the existing context serialization test with:

```python
assert "user_id" not in context.model_dump_json()
assert "display_name" not in context.model_dump_json()
assert "image_path" not in context.model_dump_json()
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/unit/test_assistant_eligibility.py \
  tests/integration/test_assistant_context.py
```

Expected: collection/import failures for the missing eligibility module and schema fields.

- [ ] **Step 4: Implement eligibility**

Normalize values case-insensitively and strip whitespace. Build reasons in this exact order:

1. `allergen_match`
2. `not_vegan`
3. `not_vegetarian`

Return `(not reasons, reasons)`.

- [ ] **Step 5: Implement schemas**

Add the exact models:

```python
class PlannedMealContext(BaseModel):
    name: str
    venue_name: str
    venue_area: str
    price_hkd: float | None
    tags: list[str]
    allergens: list[str]
    nutrition: NutritionContext
    status: Literal["planned"] = "planned"
    created_at: datetime


class PlannedWorkoutContext(BaseModel):
    id: str
    focus: str
    stage: str
    minutes: int
    exercise_names: list[str]
    created_at: datetime


class MenuCatalogItemContext(BaseModel):
    name: str
    venue_name: str
    venue_area: str
    description: str
    category: str
    price_hkd: float | None
    tags: list[str]
    allergens: list[str]
    nutrition: NutritionContext
    provenance: str
    eligible: bool
    ineligibility_reasons: list[str]


class VenueDirectoryContext(BaseModel):
    name: str
    campus_area: str
    scope: str
    is_demo: bool
    source_url: str | None


class DerivedIntakeContext(BaseModel):
    remaining_calories_kcal: float | None = None
    planned_calories_kcal: float = 0
    planned_protein_g: float = 0
```

Extend `MenuMealContext`:

```python
    venue_name: str
    venue_area: str
    price_hkd: float | None
```

Extend `AssistantContext`:

```python
    planned_meals: list[PlannedMealContext] = Field(default_factory=list)
    workout_plans: list[PlannedWorkoutContext] = Field(default_factory=list)
    menu_catalog: list[MenuCatalogItemContext] = Field(default_factory=list)
    venue_directory: list[VenueDirectoryContext] = Field(default_factory=list)
    derived: DerivedIntakeContext = Field(default_factory=DerivedIntakeContext)
```

The defaults preserve existing provider unit fixtures while the real builder fills every field.

- [ ] **Step 6: Extend the context builder**

Queries:

- Menu meals join `Venue` for venue name/area and use `MenuItem.price_hkd`.
- Planned meals join `Decision -> MenuItem -> Venue -> NutritionFact`, filter `status == "planned"`, order by `created_at.desc(), id.desc()`, limit 5.
- Active workout plans use outer join to `WorkoutSession`, filter session ID is null, order by `created_at.desc(), id.desc()`, limit 3, and resolve exercise names with `plan_read`.
- Catalog uses `list_menu_items(db, limit=100)`; all returned items are already available.
- Venue directory uses `list_venues(db, limit=100)`.
- Compute planned calories/protein from planned meal nutrition.
- Compute remaining calories as `daily_calorie_target - nutrition_totals.calories_kcal` when target exists, otherwise `None`.

Do not use menu item IDs in outbound context models except the unfinished workout plan ID needed by the existing UI/plan semantics.

- [ ] **Step 7: Run focused context and eligibility tests**

Run the command from Step 3.

Expected: PASS.

- [ ] **Step 8: Run existing assistant and catalog/workout regressions**

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/integration/test_assistant_api.py \
  tests/integration/test_nourishloop_flow.py \
  tests/integration/test_places_workouts.py
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add apps/api/modules/assistant/eligibility.py \
  apps/api/modules/assistant/schemas.py \
  apps/api/modules/assistant/context.py \
  tests/unit/test_assistant_eligibility.py \
  tests/integration/test_assistant_context.py
git commit -m "feat(api): add safe plans catalog and venue context"
```

---

### Task 2: Build the Structured Prompt and Conversational Answer Contract

**Files:**
- Create: `apps/api/modules/assistant/prompts.py`
- Modify: `apps/api/modules/assistant/provider.py`
- Modify: `apps/api/modules/assistant/schemas.py`
- Modify: `tests/unit/test_deepseek_assistant_provider.py`
- Modify: `tests/integration/test_assistant_api.py`
- Generated: `packages/api-client/src/openapi.json`
- Generated: `packages/api-client/src/schema.ts`

**Interfaces:**
- Consumes: expanded `AssistantContext` from Task 1.
- Produces: `build_answer_payload(question: str, context: AssistantContext) -> dict`
- Produces: `build_report_payload(context: AssistantContext) -> dict`
- Produces: `ANSWER_SYSTEM_PROMPT` and `REPORT_SYSTEM_PROMPT` in `prompts.py`.
- Changes `AssistantAnswerRead.answer` maximum length from 600 to 1000.

- [ ] **Step 1: Write failing provider prompt tests**

Add assertions:

```python
def test_answer_prompt_is_structured_for_safe_specific_recommendations():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {
                "content": "Protein looks like the main gap, so try the Chicken grain bowl "
                           "at Harbour Kitchen for HK$55; it has about 610 kcal and 42 g protein."
            }}]},
        )

    DeepSeekChatProvider(
        Settings(_env_file=None, deepseek_api_key="test-key"),
        transport=httpx.MockTransport(handler),
    ).answer("What should I eat?", context())

    system = " ".join(requests[0]["messages"][0]["content"].lower().split())
    envelope = json.loads(requests[0]["messages"][-1]["content"])
    assert "role" in system
    assert "data authority" in system
    assert "recommendation priorities" in system
    assert "response style" in system
    assert "eligible" in system
    assert "conversational" in system
    assert "do not use headings, bullets, numbered lists, tables, labels" in system
    assert "two to four" in system
    assert "planned" in system
    assert "real venue" in system
    assert set(envelope) == {"question", "context"}
    assert set(envelope["context"]) == {
        "date", "user", "current_intake", "planned_meals",
        "completed_workouts", "workout_plans", "menu_catalog",
        "venue_directory", "derived",
    }
```

Change the overlong API regression from 601 to 1001:

```python
class OverlongAnswerProvider:
    def answer(self, question, context):
        return "x" * 1001
```

Add an acceptance test proving 1000 is allowed:

```python
class MaxLengthAnswerProvider:
    def answer(self, question, context):
        return "x" * 1000
```

- [ ] **Step 2: Run tests and verify failure**

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/unit/test_deepseek_assistant_provider.py \
  tests/integration/test_assistant_api.py
```

Expected: failures for the old prompt, old payload shape, and 600-character boundary.

- [ ] **Step 3: Implement structured prompts**

Create prompts with four visible sections:

```text
ROLE:
You are a practical campus food and movement coach...

DATA AUTHORITY:
Use only supplied facts...
Never invent menus, prices, nutrition, venues, workouts, or medical outcomes...
Do not treat planned meals as eaten...
Do not recommend eligible=false items...
Real venues are place-only...

RECOMMENDATION PRIORITIES:
1. allergies and strict dietary restrictions...
2. goal and remaining calories...
3. main supported nutrient gap...
4. planned meals and unfinished workouts...
5. price and convenience...

RESPONSE STYLE:
Write two to four natural, friendly English sentences.
Use conversational prose only.
Do not use headings, bullets, numbered lists, tables, labels, Markdown bold,
or label-value formatting.
Name the main nutrient or dietary focus naturally.
Recommend one or two eligible meals with venue, price, estimated calories,
and protein when available.
Keep the answer under 1000 characters.
```

Preserve the existing safety rules for status-only partial photo rows.

- [ ] **Step 4: Build the nested provider payload**

Use this exact shape:

```python
{
    "question": question,
    "context": {
        "date": data["date"],
        "user": {
            "goal": data["goal"],
            "daily_calorie_target": data["daily_calorie_target"],
            "dietary_preferences": data["dietary_preferences"],
            "allergies": data["allergies"],
        },
        "current_intake": {
            "nutrition_totals": data["nutrition_totals"],
            "meal_count": data["meal_count"],
            "menu_meals": data["menu_meals"],
            "photo_meals": data["photo_meals"],
        },
        "planned_meals": data["planned_meals"],
        "completed_workouts": data["workouts"],
        "workout_plans": data["workout_plans"],
        "menu_catalog": data["menu_catalog"],
        "venue_directory": data["venue_directory"],
        "derived": data["derived"],
    },
}
```

Report payload uses the same context object without the question wrapper.

- [ ] **Step 5: Update the answer contract**

Change `AssistantAnswerRead.answer` to `max_length=1000`.

- [ ] **Step 6: Run focused prompt and API tests**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 7: Generate types and verify**

```bash
.venv/bin/python -m scripts.generate_api_types
rg -n 'AssistantAnswerRead|DailyCoachReport' packages/api-client/src/schema.ts
git diff -- packages/api-client/src/openapi.json packages/api-client/src/schema.ts
```

Expected: the generated answer type uses the updated string contract, and the OpenAPI diff is
limited to the assistant answer maximum.

- [ ] **Step 8: Commit**

```bash
git add apps/api/modules/assistant/prompts.py \
  apps/api/modules/assistant/provider.py \
  apps/api/modules/assistant/schemas.py \
  tests/unit/test_deepseek_assistant_provider.py \
  tests/integration/test_assistant_api.py \
  packages/api-client/src/openapi.json \
  packages/api-client/src/schema.ts
git commit -m "feat(api): add structured conversational coach prompt"
```

---

### Task 3: Add Seven-Day Demo Activity Seed

**Files:**
- Create: `apps/api/demo_activity.py`
- Create: `scripts/seed_demo_activity.py`
- Create: `tests/integration/test_demo_activity_seed.py`
- Modify: `compose.yaml`

**Interfaces:**
- Consumes: existing seeded users, demo menu items, exercises, and habit definitions.
- Consumes: `award_event(db, user_id, habit_id, source_type, source_id, occurred_at)`.
- Produces: `seed_demo_activity(db: Session, now: datetime | None = None) -> None`.
- Produces CLI module `python -m scripts.seed_demo_activity`.

- [ ] **Step 1: Write failing seed tests**

```python
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from apps.api.demo_activity import seed_demo_activity
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.workouts.models import WorkoutPlan, WorkoutSession

HK = ZoneInfo("Asia/Hong_Kong")


def test_demo_activity_is_idempotent_and_populates_seven_days(nl_stack):
    _, session_factory = nl_stack
    now = datetime(2026, 11, 23, 9, 0, tzinfo=HK)

    with session_factory() as db:
        seed_demo_activity(db, now=now)
        first_counts = {
            model.__tablename__: db.scalar(select(func.count()).select_from(model))
            for model in (Decision, MealLog, PhotoMealRecord, WorkoutPlan, WorkoutSession)
        }

    with session_factory() as db:
        seed_demo_activity(db, now=now)
        second_counts = {
            model.__tablename__: db.scalar(select(func.count()).select_from(model))
            for model in (Decision, MealLog, PhotoMealRecord, WorkoutPlan, WorkoutSession)
        }

    assert first_counts == second_counts

    with session_factory() as db:
        menu_logs = db.scalars(
            select(MealLog).where(MealLog.id.like("demo-meal-%"))
        ).all()
        photo_logs = db.scalars(
            select(PhotoMealRecord).where(PhotoMealRecord.id.like("demo-photo-%"))
        ).all()
        sessions = db.scalars(
            select(WorkoutSession).where(WorkoutSession.id.like("demo-wsess-%"))
        ).all()
        planned = db.scalars(
            select(Decision).where(
                Decision.id.like("demo-plan-%"),
                Decision.status == "planned",
            )
        ).all()
        unfinished = db.scalars(
            select(WorkoutPlan)
            .outerjoin(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
            .where(
                WorkoutPlan.id.like("demo-wplan-%"),
                WorkoutSession.id.is_(None),
            )
        ).all()

    assert {row.consumed_at.astimezone(HK).date() for row in menu_logs + photo_logs}
    assert len(planned) == 2
    assert {row.focus for row in unfinished} == {"legs"}
    assert len(sessions) >= 4
    assert all(row.user_id == "demo-student" for row in sessions)


def test_demo_activity_refuses_non_development(monkeypatch, nl_stack):
    _, session_factory = nl_stack
    from apps.api.core.config import Settings
    import apps.api.demo_activity as demo_activity

    monkeypatch.setattr(
        demo_activity,
        "get_settings",
        lambda: Settings(_env_file=None, app_env="production"),
    )
    with session_factory() as db:
        with pytest.raises(RuntimeError, match="development"):
            seed_demo_activity(db, now=datetime(2026, 11, 23, 9, 0, tzinfo=HK))
```

Add assertions that no peer records exist:

```python
    assert not db.scalar(
        select(MealLog.id).where(MealLog.user_id == "demo-peer")
    )
```

- [ ] **Step 2: Run tests and verify failure**

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/integration/test_demo_activity_seed.py
```

Expected: module missing.

- [ ] **Step 3: Implement the seed**

Use IDs with explicit prefixes so stale plans can be identified safely:

```text
demo-meal-YYYYMMDD-0
demo-dec-YYYYMMDD-0
demo-photo-YYYYMMDD-s
demo-plan-YYYYMMDD-l
demo-plan-YYYYMMDD-d
demo-wplan-YYYYMMDD-c
demo-wplan-YYYYMMDD-a
demo-wsess-YYYYMMDD-c
```

All IDs must stay within `String(36)`.

Scenario:

- Offset 0: breakfast of `Egg and avocado toast` at 08:15.
- Offset 0: photo snack at 16:00 with foods Greek yogurt, berries, granola and complete
  nutrition `310 kcal / 18 g protein / 38 g carbs / 9 g fat`.
- Offsets 1–6: one confirmed meal per day using the six menu items in this order:
  Chickpea salad, Grilled tofu rice bowl, Vegetable noodle bowl, Chicken grain bowl,
  Salmon quinoa plate, Egg and avocado toast.
- Confirmed menu meals use their current `NutritionFact` values as an immutable snapshot.
- Workouts on offsets 0, 1, 3, and 5, with 30-minute completed plans.
- Today's two unfinished plan rows use Chicken grain bowl and Salmon quinoa plate.
- Today's unfinished workout is a 30-minute beginner legs plan.

Use `award_event(db, user_id, "confirm_meal", "meal_log", log.id, consumed_at)` for menu
meal logs, the equivalent `photo_meal` source for the photo record, and
`complete_workout`/`workout_session` for completed sessions.

Before inserting today's plans:

```python
db.execute(
    delete(Decision).where(
        Decision.user_id == user_id,
        Decision.status == "planned",
        Decision.id.like("demo-plan-%"),
    )
)
```

Then insert today's plan decisions with `created_at` set to today at 07:00 and 07:05 HK.

The function performs one final `db.commit()`.

- [ ] **Step 4: Add the CLI and Compose startup**

CLI follows `scripts/seed_nourishloop.py`:

```python
from apps.api.core.config import get_settings
from apps.api.core.database import make_engine, make_session_factory
from apps.api.demo_activity import seed_demo_activity


def main() -> None:
    engine = make_engine(get_settings().database_url)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed_demo_activity(db)
    engine.dispose()
    print("Seeded seven days of fictional demo activity.")


if __name__ == "__main__":
    main()
```

Change the Compose API command to:

```text
alembic upgrade head && python -m scripts.seed_nourishloop && python -m scripts.seed_demo_activity && uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 5: Run seed tests**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 6: Run existing seed and API regressions**

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/integration/test_nourishloop_flow.py \
  tests/integration/test_assistant_context.py \
  tests/integration/test_community_rewards.py
```

Expected: PASS. The pytest fixture calls only the base seed and remains activity-free for
`demo-peer`.

- [ ] **Step 7: Commit**

```bash
git add apps/api/demo_activity.py scripts/seed_demo_activity.py \
  tests/integration/test_demo_activity_seed.py compose.yaml
git commit -m "feat(api): seed seven-day fictional demo activity"
```

---

### Task 4: Frontend Contract, Documentation, and End-to-End Verification

**Files:**
- Modify: `apps/web/src/features/dashboard/FloatingCoach.test.tsx`
- Modify: `README.md`
- Modify: `docs/api/contracts.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/architecture/modules.md`
- Modify: `docs/operations.md`
- Modify: `docs/product/roadmap.md`

**Interfaces:**
- Consumes Tasks 1–3.
- Produces current docs and a frontend regression for a longer conversational answer.

- [ ] **Step 1: Add a failing long-answer rendering test**

```tsx
it("renders a long conversational answer without truncating it", async () => {
  const answer =
    "Protein looks like the main gap today, so I’d choose the Chicken grain bowl at " +
    "Harbour Kitchen for HK$55 because it has about 610 kcal and 42 g protein. The " +
    "Salmon quinoa plate at Garden Counter is another good option if you want variety, " +
    "though its nutrition is still only an estimate.";
  apiMock.askAssistant.mockResolvedValue({ answer });
  render(<FloatingCoach />);

  openCoach();
  fireEvent.change(screen.getByLabelText("Ask the daily coach"), {
    target: { value: "What should I eat for lunch?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send question" }));

  expect(await screen.findByText(answer)).toBeTruthy();
});
```

Run:

```bash
cd apps/web
./node_modules/.bin/vitest run src/features/dashboard/FloatingCoach.test.tsx
```

The test may pass immediately because rendering is already text-safe. If it passes, keep it as
a contract regression; do not add production code just to force a RED.

- [ ] **Step 2: Update documentation**

README:

- Assistant sees intake, plans, workout plans, menu, and venues.
- Safe filtering occurs server-side.
- Short answers are two to four conversational sentences.
- Seven-day demo activity seed runs in Compose.

API contracts:

- Answer maximum is 1000 characters.
- Context sections and safety conditions.
- One request, no retry, no persistence.

Architecture:

- Eligibility helper and context boundaries.
- Real venue place-only rule.
- Planned vs consumed distinction.

Operations:

- Seed runs automatically in development Compose.
- Seed is per-local-day idempotent.
- Activity data is fictional and intended only for the current demo user.

Product roadmap:

- Replace the generic short-answer description with the specific safe menu/venue behavior and
  seven-day demo scenario.

- [ ] **Step 3: Verify generated artifacts**

```bash
.venv/bin/python -m scripts.generate_api_types
git diff --exit-code packages/api-client/src/openapi.json packages/api-client/src/schema.ts
```

Expected: no diff because Task 2 already committed generated changes.

- [ ] **Step 4: Run full backend verification**

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider tests/unit tests/integration
.venv/bin/python -m ruff check --no-cache apps/api/modules/assistant \
  apps/api/demo_activity.py scripts/seed_demo_activity.py \
  tests/unit/test_assistant_eligibility.py \
  tests/integration/test_assistant_context.py \
  tests/integration/test_demo_activity_seed.py
```

Expected: tests pass and changed Python files are Ruff-clean.

- [ ] **Step 5: Run full frontend verification**

From `apps/web`:

```bash
./node_modules/.bin/vitest run
./node_modules/.bin/tsc --noEmit --incremental false
./node_modules/.bin/eslint .
./node_modules/.bin/next build
```

Expected: all commands exit 0.

- [ ] **Step 6: Validate Compose and run a live demonstration**

```bash
docker compose config -q
API_HOST_PORT=8011 POSTGRES_HOST_PORT=5434 \
  docker compose --env-file /Users/wzy/homework/MAIE6000C/.env \
  -p nourishloop-wzy5534 up -d --build db api worker
```

Wait for `/api/v1/health`, then:

```bash
curl -sS --max-time 90 -X POST http://localhost:8011/api/v1/assistant/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What should I eat for lunch today?"}'
```

Expected:

- HTTP 200
- Natural prose, no heading/bullet/Markdown syntax
- One named nutrient focus
- At least one eligible demo meal with venue, price, calories, and protein
- No invented real-venue menu

```bash
curl -sS --max-time 90 -X POST http://localhost:8011/api/v1/assistant/daily-report
```

Expected: HTTP 200 and the existing complete JSON report shape.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/features/dashboard/FloatingCoach.test.tsx \
  README.md docs/api/contracts.md docs/architecture/overview.md \
  docs/architecture/modules.md docs/operations.md docs/product/roadmap.md
git commit -m "docs: document rich assistant context and demo activity"
```

---

## Completion Checklist

- [ ] Assistant context includes intake, plans, completed workouts, unfinished workout plans,
  menu catalog, and venue directory.
- [ ] Hard allergy and vegan/vegetarian filtering is server-side and tested.
- [ ] Soft preferences do not remove eligibility.
- [ ] Real venues contain place data only.
- [ ] Prompt uses the four structured sections.
- [ ] Answers are natural two-to-four-sentence prose without formatted output.
- [ ] Answer contract allows up to 1000 characters.
- [ ] Seven-day activity seed is development-only, idempotent, and touches only
  `demo-student`.
- [ ] Compose loads demo activity after the base seed.
- [ ] Existing tests, generated API files, typecheck, lint, build, Compose config, and live
  DeepSeek ask/report calls pass.
