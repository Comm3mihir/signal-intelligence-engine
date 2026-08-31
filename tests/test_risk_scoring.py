import pytest
from backend.risk.scoring_engine import RiskScoringEngine

def test_risk_scoring_calculation():
    # Test maximum score
    score, level, breakdown = RiskScoringEngine.calculate_risk(
        likelihood=5, impact=5, exposure=5, dependency_weight=5, evidence_confidence=1.0
    )
    assert score == 100.0
    assert level == "Critical"
    assert breakdown["raw_score"] == 625.0

    # Test medium-high score
    score_high, level_high, _ = RiskScoringEngine.calculate_risk(
        likelihood=4, impact=4, exposure=5, dependency_weight=5, evidence_confidence=0.9
    )
    # (4*4*5*5*0.9) / 625 = 360 / 625 = 57.6%
    assert 50.0 < score_high < 65.0
    assert level_high in ["Medium", "High"]

def test_risk_scoring_bounds():
    # Enforces bounds when out of range values passed
    score, level, breakdown = RiskScoringEngine.calculate_risk(
        likelihood=10, impact=10, exposure=10, dependency_weight=10, evidence_confidence=2.0
    )
    assert score == 100.0
    assert level == "Critical"
