from sqlalchemy import create_engine, Column, String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./signal.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrganisationModel(Base):
    __tablename__ = "organisations"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    headquarters = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CountryModel(Base):
    __tablename__ = "countries"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    region = Column(String(100))
    risk_rating = Column(String(20), default="Medium")

class SupplierModel(Base):
    __tablename__ = "suppliers"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country_id = Column(String(50), ForeignKey("countries.id"))
    tier = Column(String(20), default="Tier 1")
    headquarters = Column(String(100))
    risk_level = Column(String(20), default="Low")

class BusinessProcessModel(Base):
    __tablename__ = "business_processes"
    id = Column(String(50), primary_key=True, index=True)
    organisation_id = Column(String(50), ForeignKey("organisations.id"))
    name = Column(String(255), nullable=False)
    criticality = Column(String(50), default="Core")
    revenue_impact_per_day = Column(Float, default=0.0)

class DependencyModel(Base):
    __tablename__ = "dependencies"
    id = Column(String(50), primary_key=True, index=True)
    organisation_id = Column(String(50), ForeignKey("organisations.id"))
    supplier_id = Column(String(50), ForeignKey("suppliers.id"))
    process_id = Column(String(50), ForeignKey("business_processes.id"))
    component_name = Column(String(255), nullable=False)
    dependency_type = Column(String(100), default="Single Source")
    substitutability = Column(String(50), default="Difficult")
    lead_time_weeks = Column(Integer, default=4)

class ExternalSignalModel(Base):
    __tablename__ = "external_signals"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    signal_type = Column(String(100))
    country_id = Column(String(50), ForeignKey("countries.id"))
    source_name = Column(String(255))
    source_url = Column(Text)
    published_date = Column(String(50))
    summary = Column(Text)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EvidenceSnippetModel(Base):
    __tablename__ = "evidence_snippets"
    id = Column(String(50), primary_key=True, index=True)
    signal_id = Column(String(50), ForeignKey("external_signals.id"))
    snippet = Column(Text, nullable=False)
    source_name = Column(String(255))
    publication_date = Column(String(50))
    confidence_score = Column(Float, default=0.85)

class RiskAssessmentModel(Base):
    __tablename__ = "risk_assessments"
    id = Column(String(50), primary_key=True, index=True)
    signal_id = Column(String(50), ForeignKey("external_signals.id"))
    dependency_id = Column(String(50), ForeignKey("dependencies.id"))
    process_id = Column(String(50), ForeignKey("business_processes.id"))
    risk_title = Column(String(255), nullable=False)
    risk_category = Column(String(50))
    likelihood = Column(Integer)
    impact = Column(Integer)
    exposure = Column(Integer)
    dependency_weight = Column(Integer)
    evidence_confidence = Column(Float)
    normalized_score = Column(Float)
    risk_level = Column(String(20))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TransformationOpportunityModel(Base):
    __tablename__ = "transformation_opportunities"
    id = Column(String(50), primary_key=True, index=True)
    risk_id = Column(String(50), ForeignKey("risk_assessments.id"))
    title = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    estimated_cost_reduction = Column(Float)
    implementation_complexity = Column(String(50))
    priority = Column(String(20))

class InitiativeModel(Base):
    __tablename__ = "initiatives"
    id = Column(String(50), primary_key=True, index=True)
    opportunity_id = Column(String(50), ForeignKey("transformation_opportunities.id"))
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="Proposed")
    owner = Column(String(100))
    timeline_months = Column(Integer, default=6)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
