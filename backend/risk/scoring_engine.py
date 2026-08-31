import math
from typing import Dict, Any, Tuple

class RiskScoringEngine:
    """
    Transparent Risk Scoring Engine for SIGNAL.
    
    Formula:
    Raw Score = Likelihood * Impact * Exposure * DependencyWeight * EvidenceConfidence
    Max Raw Score = 5 * 5 * 5 * 5 * 1.0 = 625
    Normalized Score = (Raw Score / 625.0) * 100.0
    """
    
    MAX_RAW_SCORE = 625.0
    
    @classmethod
    def calculate_risk(
        cls,
        likelihood: int,
        impact: int,
        exposure: int,
        dependency_weight: int,
        evidence_confidence: float
    ) -> Tuple[float, str, Dict[str, Any]]:
        # Enforce bounds
        l = max(1, min(5, likelihood))
        i = max(1, min(5, impact))
        e = max(1, min(5, exposure))
        d = max(1, min(5, dependency_weight))
        c = max(0.1, min(1.0, evidence_confidence))
        
        raw_score = l * i * e * d * c
        normalized_score = round((raw_score / cls.MAX_RAW_SCORE) * 100.0, 2)
        
        if normalized_score >= 80.0:
            risk_level = "Critical"
        elif normalized_score >= 60.0:
            risk_level = "High"
        elif normalized_score >= 35.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        breakdown = {
            "likelihood": l,
            "impact": i,
            "exposure": e,
            "dependency_weight": d,
            "evidence_confidence": c,
            "raw_score": raw_score,
            "max_possible_raw_score": cls.MAX_RAW_SCORE,
            "normalized_score": normalized_score,
            "risk_level": risk_level
        }
        
        return normalized_score, risk_level, breakdown
