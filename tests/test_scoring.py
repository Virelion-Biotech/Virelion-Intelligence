import pytest

from virelion_intelligence.scoring import opportunity_band, opportunity_score, weighted_relevance


def test_relevance_weights_sum_to_one_by_default():
    scores = {
        "cardiovascular": 100,
        "scientific": 100,
        "virelion": 100,
        "novelty": 100,
        "dataset": 100,
        "translation": 100,
        "reproducibility": 100,
    }
    assert weighted_relevance(scores) == 100


def test_opportunity_score_and_band():
    scores = {name: 5 for name in (
        "scientific_importance", "evidence_strength", "reproducibility",
        "data_availability", "computational_feasibility", "virelion_relevance",
        "differentiation", "translational_potential")}
    score = opportunity_score(scores)
    assert score == 10
    assert opportunity_band(score) == "STRATEGIC"


def test_bad_component_fails():
    with pytest.raises(ValueError):
        weighted_relevance({"cardiovascular": 101})
