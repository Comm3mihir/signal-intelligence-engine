from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.models.database import get_db, ExternalSignalModel, EvidenceSnippetModel, DependencyModel, BusinessProcessModel, RiskAssessmentModel, TransformationOpportunityModel, InitiativeModel
from backend.models.schemas import ExternalSignalSchema, IngestSignalRequest, DynamicAnalysisResponse, EvidenceSnippetSchema, RiskAssessmentSchema, TransformationOpportunitySchema, InitiativeSchema, DependencySchema, BusinessProcessSchema
from backend.research.osint_collector import OSINTCollector
from backend.intelligence.extractor import DynamicIntelligenceExtractor
from backend.intelligence.transformation_engine import TransformationEngine

router = APIRouter(prefix="/api/signals", tags=["OSINT Signals & Dynamic Surprise Ingestion"])

@router.get("/", response_model=List[ExternalSignalSchema])
def get_signals(db: Session = Depends(get_db)):
    return db.query(ExternalSignalModel).order_by(ExternalSignalModel.created_at.desc()).all()

@router.post("/ingest-dynamic", response_model=DynamicAnalysisResponse)
def ingest_dynamic_signal(req: IngestSignalRequest, db: Session = Depends(get_db)):
    """
    DYNAMIC PROCESSING SURPRISE RECORD TEST PIPELINE
    In-gests unseen signal/event -> Entity Extraction -> Impact Traversal -> Risk Calculation -> Evidence Storage -> Transformation Plan.
    """
    # 1. Collect OSINT Signal & Store Evidence
    collected = OSINTCollector.create_signal_from_raw(
        db=db,
        title=req.title,
        country_name=req.country_name,
        signal_type=req.signal_type,
        source_name=req.source_name,
        content=req.content
    )
    sig_obj = collected["signal"]
    evidence_obj = collected["evidence"]

    # 2. Dynamic Entity Extraction & Risk Generation
    analysis = DynamicIntelligenceExtractor.extract_and_analyze(db, sig_obj.id)
    
    # 3. Generate Transformation Opportunities for created risks
    generated_opps = []
    generated_inits = []
    for r in analysis["risks"]:
        plan = TransformationEngine.generate_transformation_plan(db, r.id)
        if plan:
            generated_opps.append(plan["opportunity"])
            generated_inits.append(plan["initiative"])

    # Prepare response schemas
    sig_schema = ExternalSignalSchema(
        id=sig_obj.id,
        title=sig_obj.title,
        signal_type=sig_obj.signal_type,
        country_id=sig_obj.country_id,
        source_name=sig_obj.source_name,
        source_url=sig_obj.source_url or "",
        published_date=sig_obj.published_date,
        summary=sig_obj.summary,
        content=sig_obj.content
    )

    ev_schema = EvidenceSnippetSchema(
        id=evidence_obj.id,
        signal_id=evidence_obj.signal_id,
        snippet=evidence_obj.snippet,
        source_name=evidence_obj.source_name,
        publication_date=evidence_obj.publication_date,
        confidence_score=evidence_obj.confidence_score
    )

    deps_schemas = [
        DependencySchema(
            id=d.id,
            organisation_id=d.organisation_id,
            supplier_id=d.supplier_id,
            process_id=d.process_id,
            component_name=d.component_name,
            dependency_type=d.dependency_type,
            substitutability=d.substitutability,
            lead_time_weeks=d.lead_time_weeks
        ) for d in analysis["impacted_dependencies"]
    ]

    procs_db = db.query(BusinessProcessModel).all()
    procs_schemas = [
        BusinessProcessSchema(
            id=p.id,
            organisation_id=p.organisation_id,
            name=p.name,
            criticality=p.criticality,
            revenue_impact_per_day=p.revenue_impact_per_day
        ) for p in procs_db[:2]
    ]

    risks_schemas = [
        RiskAssessmentSchema(
            id=r.id,
            signal_id=r.signal_id,
            dependency_id=r.dependency_id or "",
            process_id=r.process_id or "",
            risk_title=r.risk_title,
            risk_category=r.risk_category,
            likelihood=r.likelihood,
            impact=r.impact,
            exposure=r.exposure,
            dependency_weight=r.dependency_weight,
            evidence_confidence=r.evidence_confidence,
            normalized_score=r.normalized_score,
            risk_level=r.risk_level,
            description=r.description,
            evidence_snippets=[ev_schema]
        ) for r in analysis["risks"]
    ]

    opps_schemas = [
        TransformationOpportunitySchema(
            id=o.id,
            risk_id=o.risk_id,
            title=o.title,
            category=o.category,
            description=o.description,
            estimated_cost_reduction=o.estimated_cost_reduction,
            implementation_complexity=o.implementation_complexity,
            priority=o.priority
        ) for o in generated_opps
    ]

    inits_schemas = [
        InitiativeSchema(
            id=i.id,
            opportunity_id=i.opportunity_id,
            title=i.title,
            status=i.status,
            owner=i.owner,
            timeline_months=i.timeline_months
        ) for i in generated_inits
    ]

    return DynamicAnalysisResponse(
        signal=sig_schema,
        extracted_entities=analysis["entities"],
        impacted_dependencies=deps_schemas,
        impacted_processes=procs_schemas,
        risks_generated=risks_schemas,
        transformation_opportunities=opps_schemas,
        initiatives=inits_schemas,
        evidence_chain=[ev_schema]
    )
