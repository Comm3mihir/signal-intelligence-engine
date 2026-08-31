import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.database import (
    RiskAssessmentModel, DependencyModel, SupplierModel, BusinessProcessModel,
    TransformationOpportunityModel, InitiativeModel
)

class TransformationEngine:
    """
    Generates strategic transformation opportunities and actionable enterprise initiatives.
    """
    
    @classmethod
    def generate_transformation_plan(cls, db: Session, risk_id: str) -> Dict[str, Any]:
        risk = db.query(RiskAssessmentModel).filter_by(id=risk_id).first()
        if not risk:
            return {}

        dep = db.query(DependencyModel).filter_by(id=risk.dependency_id).first() if risk.dependency_id else None
        proc = db.query(BusinessProcessModel).filter_by(id=risk.process_id).first() if risk.process_id else None
        sup = db.query(SupplierModel).filter_by(id=dep.supplier_id).first() if dep else None

        opp_id = f"trans_{uuid.uuid4().hex[:8]}"
        opp_title = f"Dual-Sourcing & Resilient Substitution for {dep.component_name if dep else 'Component'}"
        opp_desc = f"Establish secondary supplier qualification outside high-risk region to mitigate reliance on {sup.name if sup else 'single source'}. Implement automated AI stock buffer monitoring for process '{proc.name if proc else 'Assembly'}'."
        
        opp = TransformationOpportunityModel(
            id=opp_id,
            risk_id=risk.id,
            title=opp_title,
            category="Strategic Supply Chain Resilience",
            description=opp_desc,
            estimated_cost_reduction=18.5,
            implementation_complexity="Medium",
            priority="Immediate" if risk.risk_level == "Critical" else "High"
        )
        db.add(opp)

        init_id = f"init_{uuid.uuid4().hex[:8]}"
        init = InitiativeModel(
            id=init_id,
            opportunity_id=opp.id,
            title=f"Execute Nearshore Vendor Qualification for {dep.component_name if dep else 'Component'}",
            status="Proposed",
            owner="VP Strategic Procurement",
            timeline_months=4
        )
        db.add(init)
        db.commit()

        return {
            "opportunity": opp,
            "initiative": init
        }
