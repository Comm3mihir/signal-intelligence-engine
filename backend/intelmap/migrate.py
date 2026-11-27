"""Add the IntelMap tables to the configured database. Existing rows are preserved."""

from sqlalchemy import text

from backend.intelmap import models  # Register the new tables.
from backend.models.database import Base, init_db, engine


def migrate():
    postgres = engine.dialect.name == "postgresql"
    if postgres:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    init_db()
    if not postgres:
        return
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION intel_prevent_immutable_change() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'IntelMap historical records are immutable';
            END;
            $$;
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS intel_embeddings_forecast_cosine
            ON intel_embeddings USING hnsw (vector vector_cosine_ops)
            WHERE model = 'gemini-embedding-001' AND id LIKE 'forecast:%'
        """))
        # The backend owns the tables. Keep Supabase's public Data API roles out.
        for table in Base.metadata.tables.values():
            name = connection.dialect.identifier_preparer.quote(table.name)
            connection.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
        for table in ("intel_maps", "intel_forecasts", "intel_probability_revisions", "intel_resolutions"):
            connection.execute(text(f"DROP TRIGGER IF EXISTS immutable_history ON {table}"))
            connection.execute(text(f"CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} "
                                    "FOR EACH ROW EXECUTE FUNCTION intel_prevent_immutable_change()"))


if __name__ == "__main__":
    migrate()
