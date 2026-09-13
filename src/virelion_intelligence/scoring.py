from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


RELEVANCE_WEIGHTS: Mapping[str, float] = {
    "cardiovascular": 0.25,
    "scientific": 0.20,
    "virelion": 0.15,
    "novelty": 0.10,
    "dataset": 0.10,
    "translation": 0.10,
    "reproducibility": 0.10,
}

OPPORTUNITY_WEIGHTS: Mapping[str, float] = {
    "scientific_importance": 0.20,
    "evidence_strength": 0.20,
    "reproducibility": 0.15,
    "data_availability": 0.15,
    "computational_feasibility": 0.10,
    "virelion_relevance": 0.10,
    "differentiation": 0.05,
    "translational_potential": 0.05,
}


def weighted_score(values: Mapping[str, float], weights: Mapping[str, float], maximum: float) -> float:
    missing = set(weights) - set(values)
    if missing:
        raise ValueError(f"missing scoring components: {sorted(missing)}")
    score = sum(float(values[k]) * weights[k] for k in weights) / maximum
    return round(score * 100, 2)


def relevance_score(values: Mapping[str, float]) -> float:
    return weighted_score(values, RELEVANCE_WEIGHTS, 100.0)


def opportunity_score(values: Mapping[str, float]) -> float:
    if any(v < 0 or v > 5 for v in values.values()):
        raise ValueError("opportunity dimensions must be within 0..5")
    return round(sum(float(values[k]) * OPPORTUNITY_WEIGHTS[k] for k in OPPORTUNITY_WEIGHTS) * 2, 2)


def opportunity_action(score: float) -> str:
    if score >= 9:
        return "STRATEGIC"
    if score >= 7.5:
        return "HIGH_PRIORITY"
    if score >= 6:
        return "INVESTIGATE"
    if score >= 4:
        return "INTERESTING"
    return "WATCH"


@dataclass(frozen=True)
class ScoreBreakdown:
    score: float
    components: dict[str, float]
