from sqlalchemy.orm import Session
from typing import Dict, List, Any
from backend.models.database import (
    OrganisationModel, CountryModel, SupplierModel, BusinessProcessModel,
    DependencyModel, ExternalSignalModel, RiskAssessmentModel, EvidenceSnippetModel
)

class GraphService:
    @staticmethod
    def build_enterprise_graph(db: Session, organisation_id: str = "org_auratech") -> Dict[str, List[Dict[str, Any]]]:
        nodes = []
        edges = []
        node_ids = set()

        org = db.query(OrganisationModel).filter_by(id=organisation_id).first()
        if not org:
            orgs = db.query(OrganisationModel).all()
            if orgs:
                org = orgs[0]

        if org:
            nodes.append({
                "id": org.id,
                "label": org.name,
                "type": "Organisation",
                "data": {"industry": org.industry, "headquarters": org.headquarters}
            })
            node_ids.add(org.id)

        # Business Processes
        processes = db.query(BusinessProcessModel).filter_by(organisation_id=organisation_id).all()
        for proc in processes:
            if proc.id not in node_ids:
                nodes.append({
                    "id": proc.id,
                    "label": proc.name,
                    "type": "Process",
                    "data": {"criticality": proc.criticality, "revenue_impact": proc.revenue_impact_per_day}
                })
                node_ids.add(proc.id)
            edges.append({
                "id": f"edge_{org.id}_{proc.id}",
                "source": org.id,
                "target": proc.id,
                "relationship": "OWNS_PROCESS"
            })

        # Dependencies & Suppliers
        deps = db.query(DependencyModel).filter_by(organisation_id=organisation_id).all()
        for dep in deps:
            if dep.id not in node_ids:
                nodes.append({
                    "id": dep.id,
                    "label": dep.component_name,
                    "type": "Component",
                    "data": {"dependency_type": dep.dependency_type, "lead_time_weeks": dep.lead_time_weeks}
                })
                node_ids.add(dep.id)

            edges.append({
                "id": f"edge_{dep.id}_{dep.process_id}",
                "source": dep.id,
                "target": dep.process_id,
                "relationship": "REQUIRED_BY"
            })

            supplier = db.query(SupplierModel).filter_by(id=dep.supplier_id).first()
            if supplier:
                if supplier.id not in node_ids:
                    nodes.append({
                        "id": supplier.id,
                        "label": supplier.name,
                        "type": "Supplier",
                        "data": {"tier": supplier.tier, "risk_level": supplier.risk_level}
                    })
                    node_ids.add(supplier.id)

                edges.append({
                    "id": f"edge_{supplier.id}_{dep.id}",
                    "source": supplier.id,
                    "target": dep.id,
                    "relationship": "SUPPLIES"
                })

                country = db.query(CountryModel).filter_by(id=supplier.country_id).first()
                if country:
                    if country.id not in node_ids:
                        nodes.append({
                            "id": country.id,
                            "label": country.name,
                            "type": "Country",
                            "data": {"region": country.region, "risk_rating": country.risk_rating}
                        })
                        node_ids.add(country.id)

                    edges.append({
                        "id": f"edge_{supplier.id}_{country.id}",
                        "source": supplier.id,
                        "target": country.id,
                        "relationship": "LOCATED_IN"
                    })

        # External Signals & Risks
        signals = db.query(ExternalSignalModel).all()
        for sig in signals:
            if sig.id not in node_ids:
                nodes.append({
                    "id": sig.id,
                    "label": sig.title,
                    "type": "Signal",
                    "data": {"signal_type": sig.signal_type, "published_date": sig.published_date}
                })
                node_ids.add(sig.id)

            if sig.country_id and sig.country_id in node_ids:
                edges.append({
                    "id": f"edge_{sig.id}_{sig.country_id}",
                    "source": sig.id,
                    "target": sig.country_id,
                    "relationship": "AFFECTS_REGION"
                })

        risks = db.query(RiskAssessmentModel).all()
        for risk in risks:
            if risk.id not in node_ids:
                nodes.append({
                    "id": risk.id,
                    "label": risk.risk_title,
                    "type": "Risk",
                    "data": {"score": risk.normalized_score, "level": risk.risk_level}
                })
                node_ids.add(risk.id)

            if risk.signal_id and risk.signal_id in node_ids:
                edges.append({
                    "id": f"edge_{risk.signal_id}_{risk.id}",
                    "source": risk.signal_id,
                    "target": risk.id,
                    "relationship": "TRIGGERS_RISK"
                })

            if risk.dependency_id and risk.dependency_id in node_ids:
                edges.append({
                    "id": f"edge_{risk.id}_{risk.dependency_id}",
                    "source": risk.id,
                    "target": risk.dependency_id,
                    "relationship": "THREATENS_COMPONENT"
                })

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def get_impacted_path(db: Session, signal_id: str) -> Dict[str, Any]:
        """
        Traverse graph from signal -> country -> affected suppliers -> dependencies -> processes
        """
        sig = db.query(ExternalSignalModel).filter_by(id=signal_id).first()
        if not sig:
            return {}

        country = db.query(CountryModel).filter_by(id=sig.country_id).first()
        suppliers = db.query(SupplierModel).filter_by(country_id=sig.country_id).all() if country else []
        
        supplier_ids = [s.id for s in suppliers]
        dependencies = db.query(DependencyModel).filter(DependencyModel.supplier_id.in_(supplier_ids)).all() if supplier_ids else []
        
        process_ids = [d.process_id for d in dependencies]
        processes = db.query(BusinessProcessModel).filter(BusinessProcessModel.id.in_(process_ids)).all() if process_ids else []

        return {
            "signal": sig,
            "country": country,
            "affected_suppliers": suppliers,
            "affected_dependencies": dependencies,
            "affected_processes": processes
        }
