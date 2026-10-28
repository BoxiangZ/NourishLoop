"""Idempotent fictional demo catalog. Values are illustrative estimates."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, uuid5

from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.modules.catalog.models import ExternalNote, MenuItem, NutritionFact, Venue
from apps.api.modules.identity.models import User, UserConsent, UserGoal, UserProfile
from apps.api.modules.rewards.models import HabitDefinition, RewardItem
from apps.api.modules.workouts.models import Exercise, WorkoutProfile
from apps.api.modules.workouts.sources import EXERCISES
from apps.api.real_sources import (
    CHECKED_AT, HKUST_SOURCE, HKUST_VENUES, LOHAS_SOURCE, LOHAS_VENUES,
    PUBLIC_DISCUSSIONS,
)


def stable_id(name: str) -> str:
    return str(uuid5(NAMESPACE_DNS, f"nourishloop-demo:{name}"))


DEMO_MENU = [
    (
        "Harbour Kitchen (demo)",
        "South Campus (fictional)",
        [
            (
                "Grilled tofu rice bowl",
                "Tofu, brown rice and greens",
                "bowl",
                ["vegan", "high_protein"],
                ["soy"],
                48,
                560,
                25,
                72,
                18,
            ),
            (
                "Chicken grain bowl",
                "Chicken, grains and vegetables",
                "bowl",
                ["high_protein"],
                [],
                55,
                610,
                42,
                68,
                18,
            ),
            (
                "Vegetable noodle bowl",
                "Noodles and mixed vegetables",
                "noodles",
                ["vegan"],
                ["wheat"],
                45,
                520,
                14,
                83,
                12,
            ),
        ],
    ),
    (
        "Garden Counter (demo)",
        "North Campus (fictional)",
        [
            (
                "Chickpea salad",
                "Chickpeas, leaves and lemon dressing",
                "salad",
                ["vegan", "high_fibre"],
                [],
                49,
                470,
                18,
                56,
                19,
            ),
            (
                "Egg and avocado toast",
                "Egg, avocado and wholegrain toast",
                "toast",
                ["vegetarian"],
                ["egg", "wheat"],
                44,
                500,
                21,
                46,
                25,
            ),
            (
                "Salmon quinoa plate",
                "Salmon, quinoa and vegetables",
                "plate",
                ["high_protein"],
                ["fish"],
                68,
                640,
                39,
                58,
                25,
            ),
        ],
    ),
]


def seed(db: Session) -> None:
    settings = get_settings()
    if settings.app_env != "development":
        raise RuntimeError("Demo seed is available only in development")
    user_id = settings.demo_user_id
    if db.get(User, user_id) is None:
        db.add(User(id=user_id, is_moderator=True))
        db.flush()
    else:
        db.get(User, user_id).is_moderator = True
    if db.get(UserProfile, user_id) is None:
        db.add(
            UserProfile(
                user_id=user_id,
                display_name="Demo Student",
                dietary_preferences=[],
                allergies=[],
            )
        )
    if db.get(UserGoal, user_id) is None:
        db.add(UserGoal(user_id=user_id, goal="reduce_body_fat", daily_calorie_target=1900))
    if db.get(UserConsent, user_id) is None:
        db.add(
            UserConsent(
                user_id=user_id, analytics_opt_in=False, updated_at=datetime.now(timezone.utc)
            )
        )
    if db.get(User, "demo-peer") is None:
        db.add(User(id="demo-peer", is_moderator=False))
        db.flush()
    if db.get(UserProfile, "demo-peer") is None:
        db.add(UserProfile(
            user_id="demo-peer", display_name="Community Peer",
            dietary_preferences=[], allergies=[],
        ))
    if db.get(UserGoal, "demo-peer") is None:
        db.add(UserGoal(user_id="demo-peer", goal="eat_healthier"))
    for demo_user in (user_id, "demo-peer"):
        if db.get(WorkoutProfile, demo_user) is None:
            db.add(WorkoutProfile(
                user_id=demo_user, stage="beginner",
                equipment=["bodyweight", "machine", "dumbbell", "cable"],
                days_per_week=2,
            ))
    for habit_id, title, description, points, weekly_target in (
        ("confirm_meal", "Log a confirmed meal", "Confirm a meal you actually ate.", 5, 3),
        ("share_meal", "Share a meal", "Share one confirmed meal with Community.", 3, 3),
        ("complete_workout", "Complete a workout", "Log one completed training session.", 5, 2),
    ):
        if db.get(HabitDefinition, habit_id) is None:
            db.add(HabitDefinition(
                id=habit_id, title=title, description=description,
                points=points, weekly_target=weekly_target,
            ))
    for reward_id, title, description, cost in (
        ("starter_badge", "Starter badge", "A demo profile badge with no cash value.", 5),
        ("streak_badge", "Streak badge", "A demo habit badge with no cash value.", 24),
    ):
        if db.get(RewardItem, reward_id) is None:
            db.add(RewardItem(
                id=reward_id, title=title, description=description,
                cost=cost, active=True,
            ))
    for venue_name, area, items in DEMO_MENU:
        venue_id = stable_id(venue_name)
        if db.get(Venue, venue_id) is None:
            db.add(Venue(id=venue_id, name=venue_name, campus_area=area, is_demo=True))
            db.flush()
        for name, description, category, tags, allergens, price, kcal, protein, carbs, fat in items:
            item_id = stable_id(f"{venue_name}:{name}")
            if db.get(MenuItem, item_id) is None:
                db.add(
                    MenuItem(
                        id=item_id,
                        venue_id=venue_id,
                        name=name,
                        description=description,
                        category=category,
                        tags=tags,
                        allergen_tags=allergens,
                        price_hkd=price,
                        available=True,
                        source_label="NourishLoop fictional demo data",
                    )
                )
                db.flush()
            if db.get(NutritionFact, item_id) is None:
                db.add(
                    NutritionFact(
                        menu_item_id=item_id,
                        calories_kcal=kcal,
                        protein_g=protein,
                        carbs_g=carbs,
                        fat_g=fat,
                        basis="per_serving",
                        provenance="illustrative_estimate",
                        uncertainty_note=(
                            "Illustrative estimate for a fictional meal; "
                            "not verified nutrition data."
                        ),
                    )
                )
    for scope, source_url, rows in (
        ("hkust", HKUST_SOURCE, HKUST_VENUES),
        ("lohas", LOHAS_SOURCE, LOHAS_VENUES),
    ):
        for name, location in rows:
            venue_id = stable_id(f"real:{scope}:{name}")
            venue = db.get(Venue, venue_id)
            if venue is None:
                venue = Venue(id=venue_id, name=name)
                db.add(venue)
            venue.campus_area = location
            venue.is_demo = False
            venue.scope = scope
            venue.source_url = source_url
            venue.source_checked_at = CHECKED_AT
    for scope, title, summary, platform, source_url in PUBLIC_DISCUSSIONS:
        note_id = stable_id(f"note:{source_url}:{title}")
        if db.get(ExternalNote, note_id) is None:
            db.add(ExternalNote(
                id=note_id, scope=scope, title=title, summary=summary,
                source_platform=platform, source_url=source_url,
                source_checked_at=CHECKED_AT,
            ))
    for name, group, equipment, difficulty, instructions, source_url in EXERCISES:
        exercise_id = stable_id(f"exercise:{name}")
        if db.get(Exercise, exercise_id) is None:
            db.add(Exercise(
                id=exercise_id, name=name, muscle_group=group, equipment=equipment,
                difficulty=difficulty, instructions=instructions, source_url=source_url,
            ))
    db.commit()
