"""
Seed Data Script for SIGNAL Enterprise Intelligence Engine
Populates SQLite/SQLAlchemy database with initial enterprise topology, suppliers, dependencies, signals, and evidence.
"""

from sqlalchemy.orm import Session
from backend.models.database import (
    OrganisationModel, CountryModel, SupplierModel, BusinessProcessModel,
    DependencyModel, ExternalSignalModel, EvidenceSnippetModel,
    RiskAssessmentModel, TransformationOpportunityModel, InitiativeModel
)
from backend.risk.scoring_engine import RiskScoringEngine

def populate_seed_data(db: Session):
    # Check if already seeded
    if db.query(OrganisationModel).filter_by(id="org_auratech").first():
        return

    # 1. Organisations
    org1 = OrganisationModel(
        id="org_auratech",
        name="AuraTech Electronics Pvt Ltd",
        industry="Electronics & Semiconductor Assembly",
        headquarters="Bengaluru, Karnataka, India"
    )
    org2 = OrganisationModel(
        id="org_biopharma",
        name="BioPharma Global India",
        industry="Active Pharmaceutical Ingredients (API)",
        headquarters="Hyderabad, Telangana, India"
    )
    db.add_all([org1, org2])

    # 2. Countries
    cn_cn = CountryModel(id="cnt_cn", name="China", region="East Asia", risk_rating="High")
    cn_tw = CountryModel(id="cnt_tw", name="Taiwan", region="East Asia", risk_rating="High")
    cn_us = CountryModel(id="cnt_us", name="United States", region="North America", risk_rating="Medium")
    cn_in = CountryModel(id="cnt_in", name="India", region="South Asia", risk_rating="Low")
    cn_de = CountryModel(id="cnt_de", name="Germany", region="Europe", risk_rating="Low")
    db.add_all([cn_cn, cn_tw, cn_us, cn_in, cn_de])

    # 3. Suppliers
    sup_smic = SupplierModel(id="sup_smic", name="SMIC Microelectronics", country_id="cnt_cn", tier="Tier 1", headquarters="Shanghai, China", risk_level="High")
    sup_tsmc = SupplierModel(id="sup_tsmc", name="TSMC Foundries", country_id="cnt_tw", tier="Tier 1", headquarters="Hsinchu, Taiwan", risk_level="High")
    sup_foxconn = SupplierModel(id="sup_foxconn", name="Foxconn Precision Interconnect", country_id="cnt_cn", tier="Tier 1", headquarters="Shenzhen, China", risk_level="Medium")
    sup_qualcomm = SupplierModel(id="sup_qualcomm", name="Qualcomm India R&D / US", country_id="cnt_us", tier="Tier 1", headquarters="San Diego, USA", risk_level="Low")
    sup_infineon = SupplierModel(id="sup_infineon", name="Infineon Tech", country_id="cnt_de", tier="Tier 2", headquarters="Munich, Germany", risk_level="Low")
    db.add_all([sup_smic, sup_tsmc, sup_foxconn, sup_qualcomm, sup_infineon])

    # 4. Business Processes
    proc_smt = BusinessProcessModel(id="proc_smt", organisation_id="org_auratech", name="Automated SMT PCB Assembly", criticality="Mission Critical", revenue_impact_per_day=450000.0)
    proc_testing = BusinessProcessModel(id="proc_testing", organisation_id="org_auratech", name="High-Frequency Chip Testing", criticality="Core", revenue_impact_per_day=180000.0)
    proc_packaging = BusinessProcessModel(id="proc_packaging", organisation_id="org_auratech", name="Final Product Packaging & Shipping", criticality="Core", revenue_impact_per_day=120000.0)
    db.add_all([proc_smt, proc_testing, proc_packaging])

    # 5. Dependencies
    dep1 = DependencyModel(
        id="dep_microcontrollers",
        organisation_id="org_auratech",
        supplier_id="sup_smic",
        process_id="proc_smt",
        component_name="28nm Automotive Microcontrollers (MCU)",
        dependency_type="Single Source",
        substitutability="Difficult",
        lead_time_weeks=16
    )
    dep2 = DependencyModel(
        id="dep_power_ic",
        organisation_id="org_auratech",
        supplier_id="sup_tsmc",
        process_id="proc_smt",
        component_name="High-Voltage Power Management ICs",
        dependency_type="Single Source",
        substitutability="Moderate",
        lead_time_weeks=12
    )
    dep3 = DependencyModel(
        id="dep_connectors",
        organisation_id="org_auratech",
        supplier_id="sup_foxconn",
        process_id="proc_smt",
        component_name="Multi-Pin PCB Interconnect Harnesses",
        dependency_type="Dual Source",
        substitutability="Easy",
        lead_time_weeks=4
    )
    db.add_all([dep1, dep2, dep3])

    # 6. External Signals
    sig1 = ExternalSignalModel(
        id="sig_china_export_2026",
        title="China MOFCOM Export Control Policy on Dual-Use Legacy Chips",
        signal_type="Geopolitical Policy / Export Control",
        country_id="cnt_cn",
        source_name="Ministry of Commerce of China (MOFCOM) Official Notice",
        source_url="https://mofcom.gov.cn/policy/2026/export-control-chips",
        published_date="2026-08-15",
        summary="China imposes strict licensing requirements on export of 28nm and legacy automotive microcontroller silicon components.",
        content="Notice No. 44 of 2026: Effective September 1, 2026, export of dual-use semiconductor wafers, 28nm microcontrollers, and related raw materials originating from mainland foundries will require end-user verification and explicit MOFCOM license clearance."
    )
    sig2 = ExternalSignalModel(
        id="sig_taiwan_strait_shipping",
        title="Taiwan Strait Naval Exercise Disrupts Freight & Shipping Lanes",
        signal_type="Supply Chain Disruption",
        country_id="cnt_tw",
        source_name="Maritime Defense & Asia Logistics Intelligence",
        source_url="https://maritime-intel.org/reports/2026/taiwan-strait-delay",
        published_date="2026-08-20",
        summary="Increased maritime drills cause 2-week delays in cargo container departures from Kaohsiung port.",
        content="Commercial shipping operators report temporary rerouting around Taiwan Strait maritime exclusion zones, extending container lead times for wafer shipments to South Asia by 10 to 14 days."
    )
    db.add_all([sig1, sig2])

    # 7. Evidence Snippets
    ev1 = EvidenceSnippetModel(
        id="ev_001",
        signal_id="sig_china_export_2026",
        snippet="Effective Sept 1, 2026, export of 28nm microcontrollers originating from mainland foundries requires MOFCOM export clearance.",
        source_name="Ministry of Commerce of China (MOFCOM)",
        publication_date="2026-08-15",
        confidence_score=0.95
    )
    ev2 = EvidenceSnippetModel(
        id="ev_002",
        signal_id="sig_taiwan_strait_shipping",
        snippet="Commercial operators report 10 to 14 days lead time extension for Taiwanese semiconductor shipments to South Asia.",
        source_name="Maritime Logistics Intelligence",
        publication_date="2026-08-20",
        confidence_score=0.88
    )
    db.add_all([ev1, ev2])

    # 8. Risk Assessments
    norm1, level1, _ = RiskScoringEngine.calculate_risk(
        likelihood=5, impact=5, exposure=5, dependency_weight=5, evidence_confidence=0.95
    )
    risk1 = RiskAssessmentModel(
        id="risk_smic_export_control",
        signal_id="sig_china_export_2026",
        dependency_id="dep_microcontrollers",
        process_id="proc_smt",
        risk_title="SMIC 28nm MCU Export Restriction & Production Line Stoppage",
        risk_category="Geopolitical / Export Control",
        likelihood=5,
        impact=5,
        exposure=5,
        dependency_weight=5,
        evidence_confidence=0.95,
        normalized_score=norm1,
        risk_level=level1,
        description="High dependency on single-sourced SMIC 28nm Automotive MCU creates critical exposure to MOFCOM export restriction, threatening SMT assembly shutdown valued at $450k/day."
    )

    norm2, level2, _ = RiskScoringEngine.calculate_risk(
        likelihood=4, impact=4, exposure=4, dependency_weight=4, evidence_confidence=0.88
    )
    risk2 = RiskAssessmentModel(
        id="risk_tsmc_shipping_delay",
        signal_id="sig_taiwan_strait_shipping",
        dependency_id="dep_power_ic",
        process_id="proc_smt",
        risk_title="TSMC Power IC Freight Delay & Buffer Depletion",
        risk_category="Supply Chain Congestion",
        likelihood=4,
        impact=4,
        exposure=4,
        dependency_weight=4,
        evidence_confidence=0.88,
        normalized_score=norm2,
        risk_level=level2,
        description="Shipping delays in Kaohsiung port risk exhausting local 3-week inventory buffer for Power ICs."
    )
    db.add_all([risk1, risk2])

    # 9. Transformation Opportunities
    trans1 = TransformationOpportunityModel(
        id="trans_dual_sourcing",
        risk_id="risk_smic_export_control",
        title="Qualcomm / Infineon Automotive MCU Dual-Sourcing Qualification",
        category="Supplier Diversification & Nearshoring",
        description="Qualify Infineon Germany or STMicroelectronics as secondary supplier for 28nm MCUs, reducing Chinese concentration risk.",
        estimated_cost_reduction=22.5,
        implementation_complexity="High",
        priority="Immediate"
    )
    trans2 = TransformationOpportunityModel(
        id="trans_ai_buffer_opt",
        risk_id="risk_tsmc_shipping_delay",
        title="AI Dynamic Safety Buffer & Predictive Route Optimization",
        category="AI Supply Chain Intelligence",
        description="Deploy predictive inventory reallocation models to automatically order 4 weeks in advance upon Kaohsiung port congestion alerts.",
        estimated_cost_reduction=14.0,
        implementation_complexity="Medium",
        priority="High"
    )
    db.add_all([trans1, trans2])

    # 10. Initiatives
    init1 = InitiativeModel(
        id="init_001",
        opportunity_id="trans_dual_sourcing",
        title="Initiate Secondary MCU Validation in Bengaluru R&D Lab",
        status="Active",
        owner="Head of Hardware Engineering",
        timeline_months=3
    )
    init2 = InitiativeModel(
        id="init_002",
        opportunity_id="trans_ai_buffer_opt",
        title="Integrate AI Maritime Freight Tracking API into SAP ERP",
        status="Planning",
        owner="VP of Supply Chain Operations",
        timeline_months=2
    )
    db.add_all([init1, init2])

    db.commit()
    print("Seed data successfully populated!")
