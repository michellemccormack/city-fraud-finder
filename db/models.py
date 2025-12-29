from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, UniqueConstraint, Boolean, create_engine, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)

    city_key = Column(String, index=True)
    entity_type = Column(String, index=True)
    name = Column(String, index=True)
    normalized_name = Column(String, index=True)

    address = Column(String, index=True, nullable=True)
    normalized_address = Column(String, index=True, nullable=True)
    city = Column(String, index=True, nullable=True)
    state = Column(String, index=True, nullable=True)
    zip = Column(String, index=True, nullable=True)

    license_status = Column(String, nullable=True)
    license_capacity = Column(Integer, nullable=True)
    license_id = Column(String, index=True, nullable=True)

    npi = Column(String, index=True, nullable=True)

    score = Column(Float, default=0.0)
    score_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    aliases = relationship("Alias", back_populates="entity", cascade="all, delete-orphan")
    identifiers = relationship("Identifier", back_populates="entity", cascade="all, delete-orphan")
    evidence = relationship("EvidenceItem", back_populates="entity", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="entity", cascade="all, delete-orphan")
    foia_requests = relationship("FOIARequest", back_populates="entity", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("city_key", "entity_type", "normalized_name", "normalized_address", name="uq_entity"),
        Index("ix_entity_city_type_score", "city_key", "entity_type", "score"),
    )

class Alias(Base):
    __tablename__ = "aliases"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    alias = Column(String, index=True)
    normalized_alias = Column(String, index=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    entity = relationship("Entity", back_populates="aliases")
    __table_args__ = (UniqueConstraint("entity_id", "normalized_alias", name="uq_alias"),)

class Identifier(Base):
    __tablename__ = "identifiers"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    id_type = Column(String, index=True)
    value = Column(String, index=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    entity = relationship("Entity", back_populates="identifiers")
    __table_args__ = (UniqueConstraint("entity_id", "id_type", "value", name="uq_identifier"),)

class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)

    evidence_type = Column(String, index=True)
    source = Column(String, index=True)
    category = Column(String, index=True, nullable=True, default="Payees")  # "Payments" or "Payees"
    confidence = Column(Float, default=0.7)
    title = Column(String, nullable=True)
    url = Column(String, nullable=True)

    extracted_json = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("Entity", back_populates="evidence")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)

    source = Column(String, index=True)  # Upload filename
    data_source = Column(String, index=True, nullable=True)  # Original data provider (e.g., "ma-comptroller", "boston-open-data", "eec", "usa-spending")
    category = Column(String, index=True, nullable=True, default="Payer")  # "Payer" or "Payees"
    tag = Column(String, index=True, nullable=True)  # Sub-category like "mental", "healthcare"
    fiscal_year = Column(String, index=True, nullable=True)
    amount = Column(Float, default=0.0)
    payer = Column(String, nullable=True)
    program = Column(String, nullable=True)

    match_confidence = Column(Float, default=0.7)
    match_reason = Column(String, default="")
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("Entity", back_populates="payments")

class ReviewMatch(Base):
    __tablename__ = "review_matches"
    id = Column(Integer, primary_key=True)
    city_key = Column(String, index=True)
    candidate_name = Column(String, index=True)
    candidate_address = Column(String, index=True, nullable=True)
    candidate_source = Column(String, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True, nullable=True)
    confidence = Column(Float, default=0.0)
    reason = Column(String, default="")
    resolved = Column(Boolean, default=False)
    resolution = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FOIARequest(Base):
    __tablename__ = "foia_requests"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    city_key = Column(String, index=True)
    
    status = Column(String, index=True, default="draft")  # draft, sent, responded, denied, partial
    request_text = Column(Text, nullable=True)
    recipient = Column(String, nullable=True)  # Who we sent it to (email/address)
    
    sent_date = Column(DateTime, nullable=True)
    response_date = Column(DateTime, nullable=True)
    response_text = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)  # JSON data extracted from response
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entity = relationship("Entity", back_populates="foia_requests")

def make_engine(db_url: str):
    return create_engine(db_url, future=True)

def make_session(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()
