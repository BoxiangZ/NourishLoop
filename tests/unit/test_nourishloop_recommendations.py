from __future__ import annotations

from apps.api.modules.recommendations.engine import (
    Candidate,
    RuleBasedRecommendationEngine,
    explain_with_fallback,
)


def test_rules_are_deterministic_and_exclude_hard_restrictions():
    engine = RuleBasedRecommendationEngine()
    candidates = [
        Candidate("a", "Tofu bowl", ("vegan",), ("soy",), 600, 25),
        Candidate("b", "Bean salad", ("vegan",), (), 500, 18),
        Candidate("c", "Chicken bowl", ("high_protein",), (), 610, 42),
    ]
    result = engine.rank(candidates, "eat_healthier", 1800, ["vegan"], ["soy"])
    assert [item.candidate.item_id for item in result] == ["b"]
    assert result == engine.rank(candidates, "eat_healthier", 1800, ["vegan"], ["soy"])
    assert 0 <= result[0].score <= 1
    assert "estimate" in result[0].explanation.lower()


def test_score_configuration_is_visible_and_has_no_commercial_signal():
    config = RuleBasedRecommendationEngine().config()
    assert config["version"] == "rules-v1"
    assert round(sum(value for key, value in config.items() if key != "version"), 2) == 1
    assert "commission" not in config


def test_invalid_optional_explanation_keeps_deterministic_text():
    class InvalidProvider:
        def explain(self, candidate, baseline):
            return ""

    candidate = Candidate("item", "Demo meal", (), (), 500, 20)
    assert explain_with_fallback(InvalidProvider(), candidate, "Baseline explanation") == (
        "Baseline explanation"
    )
