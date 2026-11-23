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


def test_vegetarian_preference_accepts_vegan_menu_items():
    assert menu_eligibility(["vegan"], [], ["vegetarian"], []) == (True, [])


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


def test_eligibility_normalizes_case_and_whitespace():
    assert menu_eligibility(
        [" Vegetarian "], [" Egg "], ["VEGETARIAN"], ["egg"]
    ) == (False, ["allergen_match"])
