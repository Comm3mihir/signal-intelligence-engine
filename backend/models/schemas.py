from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base Schemas
class OrganisationSchema(BaseModel):
    id: str
    name: str
    industry: Optional[str] = "Electronics & Semiconductors"
    headquarters: Optional[str] = "Bengaluru, India"

class CountrySchema(BaseModel):
    id: str
    name: str
    region: Optional[str] = "Asia-Pacific"
    risk_rating: Optional[str] = "Medium"

class SupplierSchema(BaseModel):
    id: str
    name: str
    country_id: str
    tier: Optional[str] = "Tier 1"
    headquarters: Optional[str] = ""
    risk_level: Optional[str] = "Low"

class BusinessProcessSchema(BaseModel):
    id: str
    organisation_id: str
    name: str
    criticality: str = "Core"
    revenue_impact_per_day: float = 0.0

class DependencySchema(BaseModel):
    id: str
    organisation_id: str
    supplier_id: str
    process_id: str
    component_name: str
    dependency_type: str = "Single Source"
    substitutability: str = "Difficult"
    lead_time_weeks: int = 4

class ExternalSignalSchema(BaseModel):
    id: str
    title: str
    signal_type: str
    country_id: str
    source_name: str
    source_url: Optional[str] = ""
    published_date: str
    summary: str
    content: str

class EvidenceSnippetSchema(BaseModel):
    id: str
    signal_id: str
    snippet: str
    source_name: str
    publication_date: str
    confidence_score: float = 0.85

class RiskAssessmentSchema(BaseModel):
    id: str
    signal_id: str
    dependency_id: str
    process_id: str
    risk_title: str
    risk_category: str
    likelihood: int
    impact: int
    exposure: int
    dependency_weight: int
    evidence_confidence: float
    normalized_score: float
    risk_level: str
    description: str
    evidence_snippets: Optional[List[EvidenceSnippetSchema]] = []

class TransformationOpportunitySchema(BaseModel):
    id: str
    risk_id: str
    title: str
    category: str
    description: str
    estimated_cost_reduction: float
    implementation_complexity: str
    priority: str

class InitiativeSchema(BaseModel):
    id: str
    opportunity_id: str
    title: str
    status: str = "Proposed"
    owner: str = "Chief Supply Chain Officer"
    timeline_months: int = 6

# Dynamic Ingestion ("Surprise Record Test") Request / Response
class IngestSignalRequest(BaseModel):
    title: str
    country_name: str
    signal_type: str = "Geopolitical Policy / Export Control"
    source_name: str = "Global Trade Watch"
    published_date: Optional[str] = None
    content: str

class DynamicAnalysisResponse(BaseModel):
    signal: ExternalSignalSchema
    extracted_entities: Dict[str, Any]
    impacted_dependencies: List[DependencySchema]
    impacted_processes: List[BusinessProcessSchema]
    risks_generated: List[RiskAssessmentSchema]
    transformation_opportunities: List[TransformationOpportunitySchema]
    initiatives: List[InitiativeSchema]
    evidence_chain: List[EvidenceSnippetSchema]

# Chat Q&A Request / Response
class ChatQueryRequest(BaseModel):
    query: str
    organisation_id: Optional[str] = "org_auratech"

class ChatQueryResponse(BaseModel):
    answer: str
    evidence: List[EvidenceSnippetSchema]
    related_risks: List[RiskAssessmentSchema]
    related_nodes: List[Dict[str, str]]

# Enterprise Graph Topology Payload
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # Organisation, Country, Supplier, Component, Process, Risk, Signal
    data: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str

class EnterpriseGraphPayload(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
