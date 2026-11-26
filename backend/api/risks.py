from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import HttpUrl, ValidationError
from sqlalchemy.orm import Session

from backend.models.database import EvidenceSnippetModel, ExternalSignalModel, RiskAssessmentModel, get_db
from backend.models.schemas import CreateRiskRequest, EvidenceSnippetSchema, RiskAssessmentSchema
from backend.risk.scoring_engine import MANUAL_CATEGORY, RiskScoringEngine


router = APIRouter(prefix="/api/risks", tags=["Risk Assessments & Evidence Traceability"])
DEMO_SIGNALS = {"sig_china_export_2026", "sig_taiwan_strait_shipping"}


def evidence_for(db: Session, signal_id: str | None) -> list[EvidenceSnippetSchema]:
    return [EvidenceSnippetSchema.model_validate(row, from_attributes=True)
            for row in db.query(EvidenceSnippetModel).filter_by(signal_id=signal_id).all()]


def serialize_risk(db: Session, risk: RiskAssessmentModel) -> RiskAssessmentSchema:
    signal = db.get(ExternalSignalModel, risk.signal_id) if risk.signal_id else None
    source_url = None
    if (signal and signal.id not in DEMO_SIGNALS and signal.source_url
            and not signal.source_url.startswith("https://osint-wire.org/reports/")):
        try:
            source_url = str(HttpUrl(signal.source_url))
        except ValidationError:
            pass
    return RiskAssessmentSchema(
        id=risk.id, signal_id=risk.signal_id or "", dependency_id=risk.dependency_id or "",
        process_id=risk.process_id or "", risk_title=risk.risk_title,
        risk_category=risk.risk_category or "Geopolitical Exposure",
        likelihood=risk.likelihood, impact=risk.impact, exposure=risk.exposure,
        dependency_weight=risk.dependency_weight, evidence_confidence=risk.evidence_confidence,
        normalized_score=risk.normalized_score, risk_level=risk.risk_level,
        description=risk.description or "", evidence_snippets=evidence_for(db, risk.signal_id),
        signal_title=signal.title if signal else None, source_url=source_url,
    )


@router.get("/", response_model=list[RiskAssessmentSchema])
def get_risks(db: Session = Depends(get_db)):
    risks = db.query(RiskAssessmentModel).order_by(RiskAssessmentModel.normalized_score.desc()).all()
    return [serialize_risk(db, risk) for risk in risks]


@router.post("/", response_model=RiskAssessmentSchema, status_code=201)
def create_risk(req: CreateRiskRequest, db: Session = Depends(get_db)):
    if db.get(ExternalSignalModel, req.signal_id) is None:
        raise HTTPException(status_code=404, detail="The selected signal no longer exists.")
    factors = req.model_dump(exclude={"signal_id", "title", "description"})
    score, level, _ = RiskScoringEngine.calculate_risk(**factors)
    risk = RiskAssessmentModel(
        id=f"risk_manual_{uuid4().hex}", signal_id=req.signal_id, risk_title=req.title,
        risk_category=MANUAL_CATEGORY, description=req.description,
        normalized_score=score, risk_level=level, **factors,
    )
    db.add(risk)
    result = serialize_risk(db, risk)
    db.commit()
    return result


@router.get("/{risk_id}/evidence", response_model=list[EvidenceSnippetSchema])
def get_risk_evidence(risk_id: str, db: Session = Depends(get_db)):
    risk = db.get(RiskAssessmentModel, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return evidence_for(db, risk.signal_id)
