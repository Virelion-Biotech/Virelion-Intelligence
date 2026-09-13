from __future__ import annotations

import uuid

from .models import Opportunity
from .scoring import opportunity_action, opportunity_score


def make_opportunity(
    title: str,
    description: str,
    opportunity_type: str,
    *,
    evidence_ids: list[str] | None = None,
    dataset_ids: list[str] | None = None,
    virelion_modules: list[str] | None = None,
    scientific_importance: float = 0,
    evidence_strength: float = 0,
    reproducibility: float = 0,
    data_availability: float = 0,
    computational_feasibility: float = 0,
    virelion_relevance: float = 0,
    differentiation: float = 0,
    translational_potential: float = 0,
) -> Opportunity:
    dims = {
        "scientific_importance": scientific_importance,
        "evidence_strength": evidence_strength,
        "reproducibility": reproducibility,
        "data_availability": data_availability,
        "computational_feasibility": computational_feasibility,
        "virelion_relevance": virelion_relevance,
        "differentiation": differentiation,
        "translational_potential": translational_potential,
    }
    score = opportunity_score(dims)
    return Opportunity(
        opportunity_id=f"O-{uuid.uuid4().hex[:12]}",
        opportunity_type=opportunity_type,
        title=title,
        description=description,
        evidence_ids=evidence_ids or [],
        dataset_ids=dataset_ids or [],
        virelion_modules=virelion_modules or [],
        **dims,
        overall_score=score,
        recommended_action=opportunity_action(score),
    )
