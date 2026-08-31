from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.models.database import get_db, OrganisationModel, BusinessProcessModel, DependencyModel, SupplierModel, CountryModel
from backend.models.schemas import OrganisationSchema, BusinessProcessSchema, DependencySchema, EnterpriseGraphPayload
from backend.services.graph_service import GraphService

router = APIRouter(prefix="/api/organisations", tags=["Organisations & Graph Topology"])

@router.get("/", response_model=List[OrganisationSchema])
def get_organisations(db: Session = Depends(get_db)):
    return db.query(OrganisationModel).all()

@router.get("/{org_id}/processes", response_model=List[BusinessProcessSchema])
def get_processes(org_id: str, db: Session = Depends(get_db)):
    return db.query(BusinessProcessModel).filter_by(organisation_id=org_id).all()

@router.get("/{org_id}/dependencies", response_model=List[DependencySchema])
def get_dependencies(org_id: str, db: Session = Depends(get_db)):
    return db.query(DependencyModel).filter_by(organisation_id=org_id).all()

@router.get("/{org_id}/graph", response_model=EnterpriseGraphPayload)
def get_enterprise_graph(org_id: str = "org_auratech", db: Session = Depends(get_db)):
    return GraphService.build_enterprise_graph(db, organisation_id=org_id)
