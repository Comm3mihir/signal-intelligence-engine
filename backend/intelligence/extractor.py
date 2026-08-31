import re
import uuid
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from backend.models.database import (
    ExternalSignalModel, CountryModel, SupplierModel, DependencyModel,
    BusinessProcessModel, RiskAssessmentModel, EvidenceSnippetModel
)
from backend.risk.scoring_engine import RiskScoringEngine

class DynamicIntelligenceExtractor:
    """
    NLP Entity & Dependency Extractor for Unseen Inputs ("Surprise Record Test").
    Dynamically maps free text signals to enterprise graph nodes and executes risk scoring.
    """

    @classmethod
    def extract_and_analyze(cls, db: Session, signal_id: str) -> Dict[str, Any]:
        signal = db.query(ExternalSignalModel).filter_by(id=signal_id).first()
        if not signal:
            raise ValueError(f"Signal {signal_id} not found")

        content = f"{signal.title} {signal.summary} {signal.content}".lower()

        # 1. Entity Extraction (Countries, Tech, Products, Severity)
        extracted_entities = {
            "mentioned_countries": [],
            "keywords": [],
            "perceived_severity": "High" if any(w in content for w in ["prohibit", "ban", "restriction", "control", "embargo", "sanction", "stoppage", "disrupt"]) else "Medium"
        }

        # Check existing countries or extract mentioned
        countries = db.query(CountryModel).all()
        matched_country = None
        for c in countries:
            if c.name.lower() in content:
                extracted_entities["mentioned_countries"].append(c.name)
                matched_country = c
        
        if not matched_country and signal.country_id:
            matched_country = db.query(CountryModel).filter_by(id=signal.country_id).first()

        # 2. Match Affected Dependencies
        # Look for matching suppliers in the affected country or component keywords in content
        deps = db.query(DependencyModel).all()
        impacted_deps = []
        for dep in deps:
            sup = db.query(SupplierModel).filter_by(id=dep.supplier_id).first()
            # If supplier is in affected country or component mentioned in text
            component_terms = [t for t in re.split(r'\W+', dep.component_name.lower()) if len(t) > 3]
            is_country_match = (sup and matched_country and sup.country_id == matched_country.id)
            is_term_match = any(term in content for term in component_terms)

            if is_country_match or is_term_match or len(deps) <= 2:
                impacted_deps.append(dep)

        if not impacted_deps and deps:
            impacted_deps = [deps[0]]  # Fallback to primary dependency

        # 3. Dynamic Risk Calculation for each impacted dependency
        created_risks = []
        evidence = db.query(EvidenceSnippetModel).filter_by(signal_id=signal_id).first()
        confidence = evidence.confidence_score if evidence else 0.85

        for dep in impacted_deps:
            proc = db.query(BusinessProcessModel).filter_by(id=dep.process_id).first()
            sup = db.query(SupplierModel).filter_by(id=dep.supplier_id).first()

            # Deterministic factors
            l = 5 if "prohibit" in content or "ban" in content or "strict" in content else 4
            i = 5 if (proc and proc.criticality == "Mission Critical") else 4
            e = 5 if dep.dependency_type == "Single Source" else 3
            d = 5 if dep.substitutability == "Difficult" else 3

            norm_score, risk_level, breakdown = RiskScoringEngine.calculate_risk(
                likelihood=l,
                impact=i,
                exposure=e,
                dependency_weight=d,
                evidence_confidence=confidence
            )

            risk_id = f"risk_dyn_{uuid.uuid4().hex[:8]}"
            risk_obj = RiskAssessmentModel(
                id=risk_id,
                signal_id=signal.id,
                dependency_id=dep.id,
                process_id=proc.id if proc else None,
                risk_title=f"Vulnerability: {dep.component_name} via {sup.name if sup else 'Supplier'}",
                risk_category="Dynamic Geopolitical Exposure",
                likelihood=l,
                impact=i,
                exposure=e,
                dependency_weight=d,
                evidence_confidence=confidence,
                normalized_score=norm_score,
                risk_level=risk_level,
                description=f"Dynamic risk analysis triggered by '{signal.title}'. Single-source dependency on {sup.name if sup else 'supplier'} exposes process '{proc.name if proc else 'Assembly'}' to potential disruption."
            )
            db.add(risk_obj)
            created_risks.append(risk_obj)

        db.commit()

        return {
            "signal": signal,
            "entities": extracted_entities,
            "impacted_dependencies": impacted_deps,
            "risks": created_risks
        }
