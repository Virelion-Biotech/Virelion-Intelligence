from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelevanceWeights:
    cardiovascular: float = 0.25
    scientific: float = 0.20
    virelion: float = 0.15
    novelty: float = 0.10
    dataset: float = 0.10
    translation: float = 0.10
    reproducibility: float = 0.10

    def validate(self) -> None:
        total = sum(self.__dict__.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"relevance weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class OpportunityWeights:
    scientific_importance: float = 0.20
    evidence_strength: float = 0.20
    reproducibility: float = 0.15
    data_availability: float = 0.15
    computational_feasibility: float = 0.10
    virelion_relevance: float = 0.10
    differentiation: float = 0.05
    translational_potential: float = 0.05

    def validate(self) -> None:
        total = sum(self.__dict__.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"opportunity weights must sum to 1.0, got {total}")


def weighted_relevance(scores: dict[str, float], weights: RelevanceWeights | None = None) -> float:
    weights = weights or RelevanceWeights()
    weights.validate()
    missing = [name for name in weights.__dict__ if name not in scores]
    if missing:
        raise ValueError(f"missing relevance components: {missing}")
    if any(not 0 <= scores[name] <= 100 for name in weights.__dict__):
        raise ValueError("relevance components must be in [0, 100]")
    return round(sum(scores[name] * weight for name, weight in weights.__dict__.items()), 3)


def opportunity_score(scores: dict[str, float], weights: OpportunityWeights | None = None) -> float:
    weights = weights or OpportunityWeights()
    weights.validate()
    missing = [name for name in weights.__dict__ if name not in scores]
    if missing:
        raise ValueError(f"missing opportunity components: {missing}")
    if any(not 0 <= scores[name] <= 5 for name in weights.__dict__):
        raise ValueError("opportunity components must be in [0, 5]")
    return round(sum((scores[name] / 5.0) * weight * 10 for name, weight in weights.__dict__.items()), 3)


def opportunity_band(score: float) -> str:
    if not 0 <= score <= 10:
        raise ValueError("opportunity score must be in [0, 10]")
    if score >= 9:
        return "STRATEGIC"
    if score >= 7.5:
        return "HIGH_PRIORITY"
    if score >= 6:
        return "INVESTIGATE"
    if score >= 4:
        return "INTERESTING"
    return "MONITOR"
