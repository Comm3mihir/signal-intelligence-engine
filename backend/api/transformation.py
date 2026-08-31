from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.models.database import get_db, TransformationOpportunityModel, InitiativeModel
from backend.models.schemas import TransformationOpportunitySchema, InitiativeSchema

router = APIRouter(prefix="/api/transformation", tags=["AI Transformation & Initiatives"])

@router.get("/opportunities", response_model=List[TransformationOpportunitySchema])
def get_opportunities(db: Session = Depends(get_db)):
    opps = db.query(TransformationOpportunityModel).all()
    return [
        TransformationOpportunitySchema(
            id=o.id,
            risk_id=o.risk_id or "",
            title=o.title,
            category=o.category or "Strategic Resilience",
            description=o.description or "",
            estimated_cost_reduction=o.estimated_cost_reduction or 15.0,
            implementation_complexity=o.implementation_complexity or "Medium",
            priority=o.priority or "High"
        ) for o in opps
    ]

@router.get("/initiatives", response_model=List[InitiativeSchema])
def get_initiatives(db: Session = Depends(get_db)):
    inits = db.query(InitiativeModel).all()
    return [
        InitiativeSchema(
            id=i.id,
            opportunity_id=i.opportunity_id or "",
            title=i.title,
            status=i.status or "Proposed",
            owner=i.owner or "VP Operations",
            timeline_months=i.timeline_months or 4
        ) for i in inits
    ]
