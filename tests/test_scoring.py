import pytest

from virelion_intelligence.opportunities import make_opportunity
from virelion_intelligence.scoring import opportunity_action, opportunity_score, relevance_score


def test_relevance_score_is_bounded():
    values = {"cardiovascular": 100, "scientific": 100, "virelion": 100, "novelty": 100, "dataset": 100, "translation": 100, "reproducibility": 100}
    assert relevance_score(values) == 100


def test_opportunity_score_and_action():
    values = {
        "scientific_importance": 5,
        "evidence_strength": 5,
        "reproducibility": 5,
        "data_availability": 5,
        "computational_feasibility": 5,
        "virelion_relevance": 5,
        "differentiation": 5,
        "translational_potential": 5,
    }
    score = opportunity_score(values)
    assert score == 10
    assert opportunity_action(score) == "STRATEGIC"


def test_opportunity_rejects_out_of_range():
    values = {"scientific_importance": 6, "evidence_strength": 0, "reproducibility": 0, "data_availability": 0, "computational_feasibility": 0, "virelion_relevance": 0, "differentiation": 0, "translational_potential": 0}
    with pytest.raises(ValueError):
        opportunity_score(values)


def test_make_opportunity():
    item = make_opportunity("Test", "Description", "INVESTIGATION", scientific_importance=5, evidence_strength=4, reproducibility=4, data_availability=4, computational_feasibility=4, virelion_relevance=5, differentiation=3, translational_potential=3)
    assert item.overall_score > 0
    assert item.recommended_action in {"WATCH", "INTERESTING", "INVESTIGATE", "HIGH_PRIORITY", "STRATEGIC"}
