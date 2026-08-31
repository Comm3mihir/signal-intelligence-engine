import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base, init_db
from data.seed.seed_data import populate_seed_data
from backend.research.osint_collector import OSINTCollector
from backend.intelligence.extractor import DynamicIntelligenceExtractor

def test_dynamic_surprise_record_pipeline():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    populate_seed_data(db)

    # Ingest dynamic unseen event ("Surprise Record Test")
    unseen_title = "Taiwan Export Restriction on Advanced 3nm Lithography Equipment"
    unseen_country = "Taiwan"
    unseen_content = "Ministry of Economic Affairs issues emergency licensing restrictions prohibiting export of 3nm lithography components and power IC wafers to unauthorized overseas assemblers."

    collected = OSINTCollector.create_signal_from_raw(
        db=db,
        title=unseen_title,
        country_name=unseen_country,
        signal_type="Geopolitical Policy / Export Control",
        source_name="Taiwan Trade Gazette",
        content=unseen_content
    )
    sig = collected["signal"]
    assert sig.id.startswith("sig_")

    # Run dynamic entity extraction & risk generation
    analysis = DynamicIntelligenceExtractor.extract_and_analyze(db, sig.id)
    assert len(analysis["risks"]) > 0
    assert analysis["entities"]["perceived_severity"] == "High"
    assert analysis["risks"][0].normalized_score > 0
    
    db.close()
