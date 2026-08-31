from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import ChatQueryRequest, ChatQueryResponse, EvidenceSnippetSchema, RiskAssessmentSchema
from backend.intelligence.rag_engine import StrategicRAGEngine

router = APIRouter(prefix="/api/chat", tags=["Strategic AI Natural Language Q&A"])

@router.post("/", response_model=ChatQueryResponse)
def ask_strategic_ai(req: ChatQueryRequest, db: Session = Depends(get_db)):
    result = StrategicRAGEngine.answer_query(db, req.query)
    
    ev_schemas = [
        EvidenceSnippetSchema(
            id=ev.id,
            signal_id=ev.signal_id,
            snippet=ev.snippet,
            source_name=ev.source_name,
            publication_date=ev.publication_date,
            confidence_score=ev.confidence_score
        ) for ev in result["evidence"]
    ]

    risk_schemas = [
        RiskAssessmentSchema(
            id=r.id,
            signal_id=r.signal_id or "",
            dependency_id=r.dependency_id or "",
            process_id=r.process_id or "",
            risk_title=r.risk_title,
            risk_category=r.risk_category or "Geopolitical",
            likelihood=r.likelihood,
            impact=r.impact,
            exposure=r.exposure,
            dependency_weight=r.dependency_weight,
            evidence_confidence=r.evidence_confidence,
            normalized_score=r.normalized_score,
            risk_level=r.risk_level,
            description=r.description or ""
        ) for r in result["related_risks"]
    ]

    return ChatQueryResponse(
        answer=result["answer"],
        evidence=ev_schemas,
        related_risks=risk_schemas,
        related_nodes=result["related_nodes"]
    )
