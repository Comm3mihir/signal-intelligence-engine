-- DB Schema for SIGNAL Enterprise Strategic Intelligence Engine

CREATE TABLE IF NOT EXISTS organisations (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    headquarters VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS countries (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    risk_rating VARCHAR(20) DEFAULT 'Medium'
);

CREATE TABLE IF NOT EXISTS suppliers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country_id VARCHAR(50),
    tier VARCHAR(20) DEFAULT 'Tier 1',
    headquarters VARCHAR(100),
    risk_level VARCHAR(20) DEFAULT 'Low',
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS business_processes (
    id VARCHAR(50) PRIMARY KEY,
    organisation_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    criticality VARCHAR(50) DEFAULT 'Core',
    revenue_impact_per_day NUMERIC(12, 2) DEFAULT 0,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS dependencies (
    id VARCHAR(50) PRIMARY KEY,
    organisation_id VARCHAR(50),
    supplier_id VARCHAR(50),
    process_id VARCHAR(50),
    component_name VARCHAR(255) NOT NULL,
    dependency_type VARCHAR(100) DEFAULT 'Single Source',
    substitutability VARCHAR(50) DEFAULT 'Difficult',
    lead_time_weeks INT DEFAULT 4,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (process_id) REFERENCES business_processes(id)
);

CREATE TABLE IF NOT EXISTS external_signals (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    signal_type VARCHAR(100),
    country_id VARCHAR(50),
    source_name VARCHAR(255),
    source_url TEXT,
    published_date VARCHAR(50),
    summary TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS evidence_snippets (
    id VARCHAR(50) PRIMARY KEY,
    signal_id VARCHAR(50),
    snippet TEXT NOT NULL,
    source_name VARCHAR(255),
    publication_date VARCHAR(50),
    confidence_score NUMERIC(3,2) DEFAULT 0.85,
    FOREIGN KEY (signal_id) REFERENCES external_signals(id)
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id VARCHAR(50) PRIMARY KEY,
    signal_id VARCHAR(50),
    dependency_id VARCHAR(50),
    process_id VARCHAR(50),
    risk_title VARCHAR(255) NOT NULL,
    risk_category VARCHAR(50),
    likelihood INT,
    impact INT,
    exposure INT,
    dependency_weight INT,
    evidence_confidence NUMERIC(3,2),
    normalized_score NUMERIC(5,2),
    risk_level VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (signal_id) REFERENCES external_signals(id),
    FOREIGN KEY (dependency_id) REFERENCES dependencies(id),
    FOREIGN KEY (process_id) REFERENCES business_processes(id)
);

CREATE TABLE IF NOT EXISTS transformation_opportunities (
    id VARCHAR(50) PRIMARY KEY,
    risk_id VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    estimated_cost_reduction NUMERIC(5,2),
    implementation_complexity VARCHAR(50),
    priority VARCHAR(20),
    FOREIGN KEY (risk_id) REFERENCES risk_assessments(id)
);

CREATE TABLE IF NOT EXISTS initiatives (
    id VARCHAR(50) PRIMARY KEY,
    opportunity_id VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Proposed',
    owner VARCHAR(100),
    timeline_months INT DEFAULT 6,
    FOREIGN KEY (opportunity_id) REFERENCES transformation_opportunities(id)
);
