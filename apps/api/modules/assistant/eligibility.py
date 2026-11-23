from __future__ import annotations


def _normalize(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def menu_eligibility(
    tags: list[str],
    allergens: list[str],
    dietary_preferences: list[str],
    allergies: list[str],
) -> tuple[bool, list[str]]:
    normalized_tags = _normalize(tags)
    normalized_allergens = _normalize(allergens)
    preferences = _normalize(dietary_preferences)
    user_allergies = _normalize(allergies)

    reasons = []
    if normalized_allergens & user_allergies:
        reasons.append("allergen_match")
    if "vegan" in preferences and "vegan" not in normalized_tags:
        reasons.append("not_vegan")
    if "vegetarian" in preferences and not (
        {"vegan", "vegetarian"} & normalized_tags
    ):
        reasons.append("not_vegetarian")
    return not reasons, reasons
