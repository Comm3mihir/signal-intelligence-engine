import datetime
import uuid
from typing import Dict, Any
from sqlalchemy import func
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
        source_url: str = "",
        published_date: datetime.date | None = None,
        *, commit: bool = True
    ) -> Dict[str, Any]:
        # Match or create country
        country = db.query(CountryModel).filter(func.lower(CountryModel.name) == country_name.lower()).first()
        if not country:
            country_id = f"cnt_{uuid.uuid4().hex}"
            country = CountryModel(id=country_id, name=country_name, region="Global", risk_rating="Medium")
            db.add(country)
            db.flush()

        signal_id = f"sig_{uuid.uuid4().hex[:8]}"
        pub_date = (published_date or datetime.datetime.now(datetime.timezone.utc).date()).isoformat()

        signal = ExternalSignalModel(
            id=signal_id,
            title=title,
            signal_type=signal_type,
            country_id=country.id,
            source_name=source_name,
            source_url=source_url,
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
            confidence_score=0.50
        )
        db.add(evidence)
        if commit:
            db.commit()
        else:
            db.flush()

        return {
            "signal": signal,
            "evidence": evidence,
            "country": country
        }
