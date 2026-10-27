from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from typing import Protocol


@dataclass(frozen=True)
class RecommendationWeights:
    calorie_fit: float = 0.55
    protein_fit: float = 0.25
    preference_fit: float = 0.20
    version: str = "rules-v1"


WEIGHTS = RecommendationWeights()


@dataclass(frozen=True)
class Candidate:
    item_id: str
    name: str
    tags: tuple[str, ...]
    allergens: tuple[str, ...]
    calories_kcal: float
    protein_g: float


@dataclass(frozen=True)
class RankedCandidate:
    candidate: Candidate
    score: float
    explanation: str


class RecommendationEngine(Protocol):
    def rank(
        self,
        candidates: list[Candidate],
        goal: str,
        daily_calorie_target: float | None,
        preferences: list[str],
        allergies: list[str],
    ) -> list[RankedCandidate]: ...


class RuleBasedRecommendationEngine:
    def __init__(self, weights: RecommendationWeights = WEIGHTS):
        self.weights = weights

    def config(self) -> dict:
        return asdict(self.weights)

    def rank(self, candidates, goal, daily_calorie_target, preferences, allergies):
        preference_set = {value.lower().strip() for value in preferences}
        allergy_set = {value.lower().strip() for value in allergies}
        ranked = []
        meal_target = (daily_calorie_target or 2000) / 3
        for candidate in candidates:
            tags = {tag.lower() for tag in candidate.tags}
            allergens = {tag.lower() for tag in candidate.allergens}
            if allergy_set & allergens:
                continue
            if "vegan" in preference_set and "vegan" not in tags:
                continue
            if "vegetarian" in preference_set and not ({"vegetarian", "vegan"} & tags):
                continue
            calorie_fit = max(0.0, 1 - abs(candidate.calories_kcal - meal_target) / meal_target)
            protein_target = 30 if goal == "build_muscle" else 20
            protein_fit = min(candidate.protein_g / protein_target, 1.0)
            soft_preferences = preference_set - {"vegan", "vegetarian"}
            preference_fit = (
                len(soft_preferences & tags) / len(soft_preferences) if soft_preferences else 0.5
            )
            score = (
                self.weights.calorie_fit * calorie_fit
                + self.weights.protein_fit * protein_fit
                + self.weights.preference_fit * preference_fit
            )
            explanation = (
                f"Estimated {candidate.calories_kcal:.0f} kcal and "
                f"{candidate.protein_g:.0f} g protein per serving; "
                f"compared with an approximate {meal_target:.0f} kcal meal budget. "
                "Nutrition is an estimate, not a medical recommendation."
            )
            ranked.append(RankedCandidate(candidate, round(score, 4), explanation))
        return sorted(ranked, key=lambda result: (-result.score, result.candidate.item_id))


class OptionalExplanationProvider(Protocol):
    def explain(self, candidate: Candidate, baseline: str) -> str: ...


class DeterministicExplanationProvider:
    def explain(self, candidate: Candidate, baseline: str) -> str:
        return baseline


class ExternalLLMExplanationProvider:
    """Future adapter. Caller must catch provider errors and retain baseline text."""

    def explain(self, candidate: Candidate, baseline: str) -> str:
        raise NotImplementedError("No external LLM provider is configured")


def explain_with_fallback(
    provider: OptionalExplanationProvider, candidate: Candidate, baseline: str
) -> str:
    try:
        explanation = provider.explain(candidate, baseline)
        if not isinstance(explanation, str) or not explanation.strip() or len(explanation) > 600:
            raise ValueError("Provider explanation failed validation")
        return explanation.strip()
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "explanation_provider_fallback", extra={"error_type": type(exc).__name__}
        )
        return baseline
