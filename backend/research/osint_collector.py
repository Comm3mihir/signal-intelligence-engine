import datetime
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.database import ExternalSignalModel, EvidenceSnippetModel, CountryModel

class OSINTCollector:
    """
    OSINT Collector and Ingestion Service.
    Parses web news, official gazettes, and user dynamic inputs ("Surprise Record Test").
    """
    
    @staticmethod
    def create_signal_from_raw(
        db: Session,
        title: str,
        country_name: str,
        signal_type: str,
        source_name: str,
        content: str,
        source_url: str = ""
    ) -> Dict[str, Any]:
        # Match or create country
        country = db.query(CountryModel).filter(CountryModel.name.ilike(f"%{country_name}%")).first()
        if not country:
            country_id = f"cnt_{country_name.lower().replace(' ', '_')}"
            country = CountryModel(id=country_id, name=country_name, region="Global", risk_rating="High")
            db.add(country)
            db.commit()

        signal_id = f"sig_{uuid.uuid4().hex[:8]}"
        pub_date = datetime.datetime.now().strftime("%Y-%m-%d")

        signal = ExternalSignalModel(
            id=signal_id,
            title=title,
            signal_type=signal_type,
            country_id=country.id,
            source_name=source_name,
            source_url=source_url or f"https://osint-wire.org/reports/{signal_id}",
            published_date=pub_date,
            summary=content[:200] + "..." if len(content) > 200 else content,
            content=content
        )
        db.add(signal)

        # Create Evidence Snippet
        snippet_id = f"ev_{uuid.uuid4().hex[:8]}"
        evidence = EvidenceSnippetModel(
            id=snippet_id,
            signal_id=signal_id,
            snippet=content[:300],
            source_name=source_name,
            publication_date=pub_date,
            confidence_score=0.90
        )
        db.add(evidence)
        db.commit()

        return {
            "signal": signal,
            "evidence": evidence,
            "country": country
        }
