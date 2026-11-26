import re

from sqlalchemy.orm import Session

from backend.models.database import (
    BusinessProcessModel, DependencyModel, EvidenceSnippetModel, RiskAssessmentModel,
    SupplierModel, TransformationOpportunityModel,
)


class StrategicRAGEngine:
    """Answer supported enterprise queries from records in the configured database."""

    @classmethod
    def answer_query(cls, db: Session, query: str, organisation_id: str = "org_auratech") -> dict:
        text = query.lower()
        deps = db.query(DependencyModel).filter_by(organisation_id=organisation_id).all()
        risks = (db.query(RiskAssessmentModel)
                 .filter(RiskAssessmentModel.dependency_id.in_([dep.id for dep in deps]))
                 .order_by(RiskAssessmentModel.normalized_score.desc()).all())
        snippets = []
        selected_risks = []
        nodes = []

        if any(term in text for term in ("evidence", "source", "citation")):
            terms = set(re.findall(r"[a-z0-9]{3,}", text)) - {
                "the", "show", "behind", "our", "risk", "evidence", "source", "citation",
            }
            matched = [risk for risk in risks
                       if terms & set(re.findall(r"[a-z0-9]{3,}", f"{risk.risk_title} {risk.description}".lower()))]
            selected_risks = (matched if terms else risks)[:3]
            snippets = db.query(EvidenceSnippetModel).filter(
                EvidenceSnippetModel.signal_id.in_([risk.signal_id for risk in selected_risks])
            ).limit(3).all()
            answer = ("These are the saved excerpts for the matching assessments."
                      if snippets else "No saved evidence matches that query.")
        elif any(term in text for term in ("transformation", "initiative", "mitigat", "reduce")):
            opportunities = db.query(TransformationOpportunityModel).filter(
                TransformationOpportunityModel.risk_id.in_([risk.id for risk in risks])
            ).limit(3).all()
            answer = ("Saved proposals: " + "; ".join(row.title for row in opportunities) + "."
                      if opportunities else "There are no saved proposals for this organisation.")
        elif "process" in text:
            process_ids = list(dict.fromkeys(risk.process_id for risk in risks if risk.process_id))[:3]
            processes = {p.id: p for p in db.query(BusinessProcessModel)
                         .filter(BusinessProcessModel.id.in_(process_ids)).all()}
            names = [processes[pid].name for pid in process_ids if pid in processes]
            nodes = [{"name": name, "type": "Process"} for name in names]
            answer = ("Processes linked to the highest saved assessments: " + ", ".join(names) + "."
                      if names else "No assessed risks are linked to an enterprise process.")
        elif any(term in text for term in ("supplier", "dependency", "concentration")):
            ids = {dep.supplier_id for dep in deps if dep.dependency_type == "Single Source"}
            suppliers = db.query(SupplierModel).filter(SupplierModel.id.in_(ids)).order_by(SupplierModel.name).all()
            names = [supplier.name for supplier in suppliers]
            nodes = [{"name": name, "type": "Supplier"} for name in names]
            answer = ("Suppliers with saved single-source dependencies: " + ", ".join(names) + "."
                      if names else "No single-source suppliers are recorded for this organisation.")
        elif any(term in text for term in ("risk", "exposure")):
            selected_risks = risks[:3]
            answer = ("Highest saved risk scores: " + "; ".join(
                f"{risk.risk_title} ({risk.normalized_score}/100)" for risk in selected_risks
            ) + "." if selected_risks else "No risk assessments are recorded for this organisation.")
        else:
            answer = "Ask about saved risks, suppliers, business processes, evidence, or mitigation proposals."

        return {"answer": answer, "evidence": snippets, "related_risks": selected_risks, "related_nodes": nodes}
