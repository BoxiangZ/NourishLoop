"""Pure stage-aware exercise selection. The language model cannot choose loads or movements."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apps.api.modules.workouts.models import Exercise

FOCI = ("back", "shoulders", "chest", "legs", "core")
STAGE_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def select_routine(
    exercises: list[Exercise], requested_focus: str, stage: str,
    equipment: list[str], days_per_week: int, minutes: int,
    recent: list[tuple[str, datetime]], now: datetime,
) -> tuple[str, list[dict], str]:
    focus = requested_focus
    recent = [
        (prior_focus, completed_at if completed_at.tzinfo else completed_at.replace(tzinfo=timezone.utc))
        for prior_focus, completed_at in recent
    ]
    recent_same = any(
        prior_focus == focus and now - completed_at < timedelta(hours=48)
        for prior_focus, completed_at in recent
    )
    available_groups = {item.muscle_group for item in exercises if item.equipment in equipment
                        and STAGE_ORDER[item.difficulty] <= STAGE_ORDER[stage]}
    if recent_same:
        # Avoid repeating the same muscle group too soon; choose the least recent alternative.
        last_by_focus = {group: max((when for prior, when in recent if prior == group), default=None)
                         for group in FOCI if group != focus and group in available_groups}
        alternatives = sorted(last_by_focus, key=lambda group: (
            last_by_focus[group] is not None, last_by_focus[group] or now, FOCI.index(group)
        ))
        if alternatives:
            focus = alternatives[0]
    eligible = sorted(
        (item for item in exercises if item.muscle_group == focus
         and item.equipment in equipment
         and STAGE_ORDER[item.difficulty] <= STAGE_ORDER[stage]),
        key=lambda item: (STAGE_ORDER[item.difficulty], item.name),
    )
    count = min(len(eligible), max(2, min(4, minutes // 12 + 1)))
    sets = {"beginner": 2, "intermediate": 3, "advanced": 3}[stage]
    hk = ZoneInfo("Asia/Hong_Kong")
    week_count = len({completed_at.astimezone(hk).date() for _, completed_at in recent
                      if now - completed_at < timedelta(days=7)})
    if week_count >= days_per_week:
        sets = max(1, sets - 1)
    prescription = [
        {"exercise_id": item.id, "sets": sets,
         "reps": "8–12 controlled reps" if stage != "advanced" else "6–12 controlled reps",
         "rest_seconds": 90 if stage == "beginner" else 120}
        for item in eligible[:count]
    ]
    if recent_same and focus != requested_focus:
        reason = (f"You logged {requested_focus} recently, so today's suggestion shifts to {focus} "
                  "to allow recovery.")
    elif recent_same:
        reason = (f"You logged {requested_focus} recently and no other focus matches your equipment. "
                  "Consider a rest day before repeating it.")
    else:
        reason = f"This {focus} session matches your declared {stage} stage and available equipment."
    if week_count >= days_per_week:
        reason += (f" You have met your {days_per_week}-day training target in the last week; "
                   "this optional session uses fewer sets.")
    reason += (" Start with a gentle warm-up, use a comfortable load and stop if an exercise "
               "causes pain. Build up gradually; you decide what to do.")
    return focus, prescription, reason
