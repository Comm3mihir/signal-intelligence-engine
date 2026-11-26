"""Record a forecast review against a dated source from the operator's terminal."""

import argparse
import json
from datetime import datetime, timezone

from pydantic import HttpUrl, ValidationError

from backend.models.database import IntelligenceRecord, SessionLocal, init_db
from backend.research.world_intelligence import article_date, read_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("forecast_id")
    parser.add_argument("outcome", choices=["confirmed", "refuted", "inconclusive"])
    parser.add_argument("evidence_url")
    parser.add_argument("note", help="Explain how the source bears on the indicator")
    args = parser.parse_args()
    try:
        url = str(HttpUrl(args.evidence_url))
    except ValidationError:
        parser.error("Provide an HTTP or HTTPS evidence URL.")
    if not args.note.strip():
        parser.error("Describe the evidence in the review note.")
    init_db()
    with SessionLocal() as db:
        forecast = read_record(db, f"forecast:{args.forecast_id}", None)
        if not forecast:
            parser.error("Forecast ID does not exist in this database.")
        now = datetime.now(timezone.utc)
        if args.outcome == "inconclusive" and now < article_date(forecast["deadline"]):
            parser.error("Review as inconclusive after the forecast deadline.")
        review = {"outcome": args.outcome, "evidence_url": url, "note": args.note.strip(),
                  "reviewed_at": now.isoformat()}
        db.merge(IntelligenceRecord(id=f"review:{args.forecast_id}", payload=json.dumps(review)))
        db.commit()
    print(f"Recorded {args.outcome} for {args.forecast_id}")


if __name__ == "__main__":
    main()
