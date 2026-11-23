from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.modules.assistant.eligibility import menu_eligibility
from apps.api.modules.assistant.schemas import (
    AssistantContext,
    DerivedIntakeContext,
    MenuCatalogItemContext,
    MenuMealContext,
    NutritionContext,
    PhotoMealContext,
    PlannedMealContext,
    PlannedWorkoutContext,
    VenueDirectoryContext,
    WorkoutContext,
    WorkoutProfileContext,
)
from apps.api.modules.catalog.models import MenuItem, NutritionFact, Venue
from apps.api.modules.catalog.service import list_menu_items, list_venues
from apps.api.modules.identity.models import User
from apps.api.modules.identity.service import get_goal, get_profile
from apps.api.modules.tracking.models import Decision, MealLog, PhotoMealRecord
from apps.api.modules.tracking.service import daily_summary
from apps.api.modules.workouts.models import WorkoutPlan, WorkoutProfile, WorkoutSession
from apps.api.modules.workouts.service import plan_read, session_read

HK_ZONE = ZoneInfo("Asia/Hong_Kong")
CONFIRMED_PHOTO_REVIEW_STATUSES = frozenset({"not_requested", "completed"})


def _day_bounds(day: date | None) -> tuple[date, datetime, datetime]:
    local_day = day or datetime.now(HK_ZONE).date()
    start_local = datetime.combine(local_day, time.min, tzinfo=HK_ZONE)
    end_local = start_local + timedelta(days=1)
    return (
        local_day,
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def _photo_food_names(foods: list) -> list[str]:
    return [
        food["name"] if isinstance(food, dict) else str(food)
        for food in foods
        if (not isinstance(food, dict)) or food.get("name")
    ]


def build_today_context(db: Session, user: User, day: date | None = None) -> AssistantContext:
    local_day, start, end = _day_bounds(day)
    goal = get_goal(db, user)
    profile = get_profile(db, user)

    menu_rows = db.execute(
        select(MealLog, MenuItem, Venue)
        .join(MenuItem, MenuItem.id == MealLog.menu_item_id)
        .join(Venue, Venue.id == MenuItem.venue_id)
        .where(
            MealLog.user_id == user.id,
            MealLog.consumed_at >= start,
            MealLog.consumed_at < end,
        )
        .order_by(MealLog.consumed_at, MealLog.id)
    ).all()
    menu_meals = [
        MenuMealContext(
            name=item.name,
            venue_name=venue.name,
            venue_area=venue.campus_area,
            price_hkd=item.price_hkd,
            servings=log.servings,
            consumed_at=log.consumed_at,
            nutrition=NutritionContext(**log.nutrition_snapshot),
        )
        for log, item, venue in menu_rows
    ]

    planned_rows = db.execute(
        select(Decision, MenuItem, Venue, NutritionFact)
        .join(MenuItem, MenuItem.id == Decision.menu_item_id)
        .join(Venue, Venue.id == MenuItem.venue_id)
        .join(NutritionFact, NutritionFact.menu_item_id == MenuItem.id)
        .where(
            Decision.user_id == user.id,
            Decision.status == "planned",
        )
        .order_by(Decision.created_at.desc(), Decision.id.desc())
        .limit(5)
    ).all()
    planned_meals = [
        PlannedMealContext(
            name=item.name,
            venue_name=venue.name,
            venue_area=venue.campus_area,
            price_hkd=item.price_hkd,
            tags=item.tags,
            allergens=item.allergen_tags,
            nutrition=NutritionContext(
                calories_kcal=nutrition.calories_kcal,
                protein_g=nutrition.protein_g,
                carbs_g=nutrition.carbs_g,
                fat_g=nutrition.fat_g,
            ),
            created_at=decision.created_at,
        )
        for decision, item, venue, nutrition in planned_rows
    ]

    workout_plans = []
    unfinished_plans = db.scalars(
        select(WorkoutPlan)
        .outerjoin(WorkoutSession, WorkoutSession.plan_id == WorkoutPlan.id)
        .where(
            WorkoutPlan.user_id == user.id,
            WorkoutSession.id.is_(None),
        )
        .order_by(WorkoutPlan.created_at.desc(), WorkoutPlan.id.desc())
        .limit(3)
    ).all()
    for plan in unfinished_plans:
        plan_context = plan_read(db, plan)
        workout_plans.append(
            PlannedWorkoutContext(
                id=plan.id,
                focus=plan.focus,
                stage=plan.stage,
                minutes=plan.minutes,
                exercise_names=[
                    prescribed.exercise.name for prescribed in plan_context.exercises
                ],
                created_at=plan.created_at,
            )
        )

    venue_rows = list_venues(db, limit=100)
    venue_by_id = {venue.id: venue for venue in venue_rows}
    menu_catalog = [
        MenuCatalogItemContext(
            name=item.name,
            venue_name=venue_by_id[item.venue_id].name,
            venue_area=venue_by_id[item.venue_id].campus_area,
            description=item.description,
            category=item.category,
            price_hkd=item.price_hkd,
            tags=item.tags,
            allergens=item.allergen_tags,
            nutrition=NutritionContext(
                calories_kcal=nutrition.calories_kcal,
                protein_g=nutrition.protein_g,
                carbs_g=nutrition.carbs_g,
                fat_g=nutrition.fat_g,
            ),
            provenance=nutrition.provenance,
            eligible=eligible,
            ineligibility_reasons=reasons,
        )
        for item, nutrition in list_menu_items(db, limit=100)
        for eligible, reasons in [
            menu_eligibility(
                item.tags,
                item.allergen_tags,
                profile.dietary_preferences,
                profile.allergies,
            )
        ]
    ]
    venue_directory = [
        VenueDirectoryContext(
            name=venue.name,
            campus_area=venue.campus_area,
            scope=venue.scope,
            is_demo=venue.is_demo,
            source_url=venue.source_url,
        )
        for venue in venue_rows
    ]

    photo_rows = db.scalars(
        select(PhotoMealRecord)
        .where(
            PhotoMealRecord.user_id == user.id,
            PhotoMealRecord.consumed_at >= start,
            PhotoMealRecord.consumed_at < end,
        )
        .order_by(PhotoMealRecord.consumed_at, PhotoMealRecord.id)
    ).all()
    photo_meals = []
    for row in photo_rows:
        is_confirmed = row.review_status in CONFIRMED_PHOTO_REVIEW_STATUSES
        photo_meals.append(
            PhotoMealContext(
                food_names=_photo_food_names(row.foods),
                notes=row.notes,
                review_status=row.review_status,
                nutrition_status=row.nutrition_status if is_confirmed else "none",
                nutrition=(
                    NutritionContext(**row.nutrition_snapshot)
                    if is_confirmed and row.nutrition_snapshot
                    else None
                ),
                unresolved_foods=row.unresolved_foods or [],
            )
        )

    workout_rows = db.execute(
        select(WorkoutSession, WorkoutPlan)
        .join(WorkoutPlan, WorkoutPlan.id == WorkoutSession.plan_id)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.completed_at >= start,
            WorkoutSession.completed_at < end,
        )
        .order_by(WorkoutSession.completed_at, WorkoutSession.id)
    ).all()
    workouts = []
    for workout_session, plan in workout_rows:
        session_context = session_read(db, workout_session, plan)
        workouts.append(
            WorkoutContext(
                focus=session_context.focus,
                stage=session_context.stage,
                duration_min=session_context.duration_min,
                exercise_names=session_context.exercise_names,
                completed_at=session_context.completed_at,
            )
        )

    workout_profile = db.get(WorkoutProfile, user.id)
    summary = daily_summary(db, user, local_day)
    planned_calories = sum(
        meal.nutrition.calories_kcal for meal in planned_meals
    )
    planned_protein = sum(meal.nutrition.protein_g for meal in planned_meals)
    remaining_calories = (
        goal.daily_calorie_target - summary.totals.calories_kcal
        if goal.daily_calorie_target is not None
        else None
    )

    return AssistantContext(
        date=local_day,
        goal=goal.goal,
        daily_calorie_target=goal.daily_calorie_target,
        dietary_preferences=profile.dietary_preferences,
        allergies=profile.allergies,
        nutrition_totals=NutritionContext(**summary.totals.model_dump()),
        meal_count=summary.meal_count,
        menu_meals=menu_meals,
        photo_meals=photo_meals,
        workouts=workouts,
        workout_profile=(
            WorkoutProfileContext(
                stage=workout_profile.stage,
                equipment=workout_profile.equipment,
                days_per_week=workout_profile.days_per_week,
            )
            if workout_profile is not None
            else None
        ),
        planned_meals=planned_meals,
        workout_plans=workout_plans,
        menu_catalog=menu_catalog,
        venue_directory=venue_directory,
        derived=DerivedIntakeContext(
            remaining_calories_kcal=remaining_calories,
            planned_calories_kcal=planned_calories,
            planned_protein_g=planned_protein,
        ),
    )
