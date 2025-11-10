from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Fine(Base):
    """
    Database model for a traffic fine.
    """
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    location = Column(String, index=True)
    infractor = Column(String, index=True)
    fine_amount = Column(Float)
    infraction_code = Column(String, index=True)
    pdf_reference = Column(String)

    defenses = relationship("Defense", back_populates="fine")

class Defense(Base):
    """
    Database model for a defense.
    """
    __tablename__ = "defenses"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    fine_id = Column(Integer, ForeignKey("fines.id"))

    fine = relationship("Fine", back_populates="defenses")

class LegalDocument(Base):
    """
    Database model for a scraped legal document.
    This replaces the previous 'Document' model with a more specific name.
    """
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    document_type = Column(String, index=True) # e.g., 'law', 'precedent', 'defense', 'regulation'
    jurisdiction = Column(String, index=True) # e.g., 'Portugal', 'Lisbon'
    publication_date = Column(Date, nullable=True)
    retrieval_date = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String, unique=True, index=True)
    file_path = Column(String, nullable=True) # Local path to the stored document (e.g., PDF)
    extracted_text = Column(Text)
    
    # Quality Scoring
    quality_score = Column(Float, default=0.0) # Overall quality score
    relevance_score = Column(Float, default=0.0) # Relevance to traffic fines
    freshness_score = Column(Float, default=0.0) # How recent the document is
    authority_score = Column(Float, default=0.0) # Authority level of the source

    # Relationships
    case_outcome_id = Column(Integer, ForeignKey("case_outcomes.id"), nullable=True)
    case_outcome = relationship("CaseOutcome", back_populates="legal_documents")

class CaseOutcome(Base):
    """
    Database model to store information about the outcome of a legal case.
    """
    __tablename__ = "case_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    outcome_type = Column(String, index=True) # e.g., 'successful defense', 'fine upheld', 'appeal granted'
    outcome_date = Column(Date, nullable=True)
    summary = Column(Text, nullable=True)
    citation = Column(String, nullable=True) # Legal citation for the case

    legal_documents = relationship("LegalDocument", back_populates="case_outcome")

class DefenseTemplate(Base):
    """
    Database model to store templates for generating defenses.
    """
    __tablename__ = "defense_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    template_content = Column(Text)
    document_type = Column(String, index=True) # e.g., 'traffic fine defense', 'appeal letter'
    jurisdiction = Column(String, index=True) # e.g., 'Portugal'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

