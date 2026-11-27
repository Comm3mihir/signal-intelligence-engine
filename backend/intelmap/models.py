from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

from backend.models.database import Base


def now():
    return datetime.now(timezone.utc)


def uid():
    return uuid4().hex


class Article(Base):
    __tablename__ = "intel_articles"
    id = Column(String(32), primary_key=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    data = Column(JSON, nullable=False)


class IntelMap(Base):
    __tablename__ = "intel_maps"
    id = Column(String(32), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    event = Column(JSON, nullable=False)
    article_ids = Column(JSON, nullable=False)


class Forecast(Base):
    __tablename__ = "intel_forecasts"
    id = Column(String(32), primary_key=True, default=uid)
    map_id = Column(ForeignKey("intel_maps.id"), nullable=False, index=True)
    parent_id = Column(ForeignKey("intel_forecasts.id"))
    issued_at = Column(DateTime(timezone=True), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False, index=True)
    domain = Column(String(40), nullable=False, index=True)
    original = Column(JSON, nullable=False)


class ForecastTerm(Base):
    __tablename__ = "intel_forecast_terms"
    term = Column(String(80), primary_key=True)
    forecast_id = Column(ForeignKey("intel_forecasts.id"), primary_key=True)


class Evidence(Base):
    __tablename__ = "intel_evidence"
    id = Column(String(32), primary_key=True, default=uid)
    forecast_id = Column(ForeignKey("intel_forecasts.id"), nullable=False, index=True)
    article_id = Column(ForeignKey("intel_articles.id"), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    stance = Column(String(32), nullable=False)
    reasoning = Column(Text, nullable=False)
    provenance = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (UniqueConstraint("forecast_id", "fingerprint"),)


class Revision(Base):
    __tablename__ = "intel_probability_revisions"
    id = Column(String(32), primary_key=True, default=uid)
    forecast_id = Column(ForeignKey("intel_forecasts.id"), nullable=False, index=True)
    evidence_id = Column(ForeignKey("intel_evidence.id"), unique=True)
    probability = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    provenance = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Resolution(Base):
    __tablename__ = "intel_resolutions"
    forecast_id = Column(ForeignKey("intel_forecasts.id"), primary_key=True)
    status = Column(String(32), nullable=False)
    truth_value = Column(Integer)
    article_id = Column(ForeignKey("intel_articles.id"))
    reasoning = Column(Text, nullable=False)
    credibility = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Job(Base):
    __tablename__ = "intel_jobs"
    id = Column(String(64), primary_key=True)
    kind = Column(String(24), nullable=False)
    payload = Column(JSON, nullable=False)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    ready_at = Column(DateTime(timezone=True), default=now, nullable=False, index=True)
    state = Column(String(16), default="queued", nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    lease = Column(String(32))
    error = Column(Text)


class ProviderDay(Base):
    __tablename__ = "intel_provider_days"
    id = Column(String(32), primary_key=True)
    reserved = Column(Integer, nullable=False, default=0)


class Inference(Base):
    __tablename__ = "intel_inference"
    id = Column(String(32), primary_key=True, default=uid)
    cache_key = Column(String(64), nullable=False, index=True)
    provider = Column(String(24), nullable=False, index=True)
    model = Column(String(90), nullable=False)
    task = Column(String(24), nullable=False)
    status = Column(String(24), nullable=False)
    milliseconds = Column(Integer, nullable=False)
    fallback_rank = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    response = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False, index=True)


class Embedding(Base):
    __tablename__ = "intel_embeddings"
    id = Column(String(48), primary_key=True)
    model = Column(String(50), nullable=False)
    vector = Column(Vector(768).with_variant(JSON, "sqlite"), nullable=False)


class Conversation(Base):
    __tablename__ = "intel_conversations"
    id = Column(String(32), primary_key=True, default=uid)
    title = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, nullable=False, index=True)
    messages = Column(JSON, nullable=False)
