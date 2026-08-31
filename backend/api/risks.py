from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.models.database import get_db, RiskAssessmentModel, EvidenceSnippetModel
from backend.models.schemas import RiskAssessmentSchema, EvidenceSnippetSchema

router = APIRouter(prefix="/api/risks", tags=["Risk Assessments & Evidence Traceability"])

@router.get("/", response_model=List[RiskAssessmentSchema])
def get_risks(db: Session = Depends(get_db)):
    risks = db.query(RiskAssessmentModel).order_by(RiskAssessmentModel.normalized_score.desc()).all()
    results = []
    for r in risks:
        evs = db.query(EvidenceSnippetModel).filter_by(signal_id=r.signal_id).all()
        ev_schemas = [
            EvidenceSnippetSchema(
                id=ev.id,
                signal_id=ev.signal_id,
                snippet=ev.snippet,
                source_name=ev.source_name,
                publication_date=ev.publication_date,
                confidence_score=ev.confidence_score
            ) for ev in evs
        ]
        results.append(
            RiskAssessmentSchema(
                id=r.id,
                signal_id=r.signal_id or "",
                dependency_id=r.dependency_id or "",
                process_id=r.process_id or "",
                risk_title=r.risk_title,
                risk_category=r.risk_category or "Geopolitical Exposure",
                likelihood=r.likelihood,
                impact=r.impact,
                exposure=r.exposure,
                dependency_weight=r.dependency_weight,
                evidence_confidence=r.evidence_confidence,
                normalized_score=r.normalized_score,
                risk_level=r.risk_level,
                description=r.description or "",
                evidence_snippets=ev_schemas
            )
        )
    return results

@router.get("/{risk_id}/evidence", response_model=List[EvidenceSnippetSchema])
def get_risk_evidence(risk_id: str, db: Session = Depends(get_db)):
    risk = db.query(RiskAssessmentModel).filter_by(id=risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    evs = db.query(EvidenceSnippetModel).filter_by(signal_id=risk.signal_id).all()
    return [
        EvidenceSnippetSchema(
            id=ev.id,
            signal_id=ev.signal_id,
            snippet=ev.snippet,
            source_name=ev.source_name,
            publication_date=ev.publication_date,
            confidence_score=ev.confidence_score
        ) for ev in evs
    ]
