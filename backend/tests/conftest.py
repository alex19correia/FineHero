"""
Test utilities and fixtures for FineHero backend testing.

This module provides shared test utilities, database fixtures, and mock configurations
to support comprehensive testing across all backend components.
"""

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
from faker import Faker
from typing import Generator, Dict, Any

# Import app components for testing
from app import models, schemas
from core.config import settings
from database import SessionLocal, engine

fake = Faker('pt_PT')  # Portuguese locale for realistic test data

@pytest.fixture(scope="session")
def test_db():
    """Create a test database with in-memory SQLite for isolation."""
    # Create test database URL
    test_db_url = "sqlite:///:memory:"
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    models.Base.metadata.create_all(bind=test_engine)
    
    # Create test session
    TestSessionLocal = sessionmaker(bind=test_engine)
    
    yield TestSessionLocal
    
    # Cleanup
    models.Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db) -> Generator:
    """Create a database session for each test."""
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    """Create a test client for FastAPI endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides = {}
    app.dependency_overrides[app.dependency_overrides.get("get_db", lambda: None)] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def sample_fine_data() -> Dict[str, Any]:
    """Generate sample fine data for testing."""
    return {
        "date": date(2025, 11, 11),
        "location": "Avenida da Liberdade, Lisboa",
        "infractor": "João Silva",
        "fine_amount": 150.00,
        "infraction_code": "ART135-1-A",
        "pdf_reference": "MULT-2025-001234"
    }

@pytest.fixture
def sample_defense_data() -> Dict[str, Any]:
    """Generate sample defense data for testing."""
    return {
        "content": """
        Exmo. Senhor Presidente da Autoridade Nacional de Segurança Rodoviária,
        
        Eu, João Silva, venho por este meio apresentar a minha defesa em relação 
        ao auto de contraordenação mencionado, pelos fundamentos abaixo expostos.
        
        [Conteúdo da defesa aqui...]
        """,
        "fine_id": 1
    }

@pytest.fixture
def mock_ocr_processor():
    """Mock OCR processor for testing PDF processing."""
    mock_processor = MagicMock()
    mock_processor.extract_text.return_value = """
    Auto de Contraordenação
    Data: 11/11/2025
    Local: Avenida da Liberdade, Lisboa
    Infrator: João Silva
    Valor: 150,00 EUR
    Código: ART135-1-A
    """
    mock_processor.parse_text.return_value = {
        "date": "11/11/2025",
        "location": "Avenida da Liberdade, Lisboa", 
        "amount": "150,00",
        "infraction": "ART135-1-A"
    }
    mock_processor.validate_data.return_value = {
        "date": "2025-11-11",
        "location": "Avenida da Liberdade, Lisboa",
        "amount": "150.00",
        "infraction": "ART135-1-A"
    }
    return mock_processor

@pytest.fixture
def mock_rag_retriever():
    """Mock RAG retriever for testing."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        "Artigo 135º do Código da Estrada - Condução sob influência de álcool",
        "Artigo 27º da Constituição - Direito à saúde e vida",
        "Decisão do Tribunal Administrativo de Círculo de Lisboa"
    ]
    return mock_retriever

@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for testing."""
    mock_service = MagicMock()
    mock_service.track_event.return_value = {"success": True, "event_id": 1}
    mock_service.track_pdf_upload.return_value = {"success": True, "event_id": 2}
    mock_service.track_defense_generation.return_value = {"success": True, "event_id": 3}
    return mock_service

@pytest.fixture
def temp_vector_store():
    """Create a temporary vector store directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def temp_knowledge_base():
    """Create a temporary knowledge base directory for testing."""
    temp_dir = tempfile.mkdtemp()
    legal_articles_dir = os.path.join(temp_dir, "legal_articles")
    os.makedirs(legal_articles_dir, exist_ok=True)
    
    # Create sample legal documents
    sample_article = """
    Artigo 135º do Código da Estrada
    
    1. Constitui contraordenação muito grave a condução de veículo na via pública ou em terreno particular aberto ao público com taxa de álcool no sangue igual ou superior a 1,2 g/l.
    
    2. A contraordenação prevista no número anterior é punida com:
    a) Coima de € 250 a € 1250, se a taxa de álcool no sangue for igual ou superior a 1,2 g/l e inferior a 1,8 g/l;
    b) Coima de € 1250 a € 2500, se a taxa de álcool no sangue for igual ou superior a 1,8 g/l e inferior a 2,5 g/l;
    c) Coima de € 2500 a € 5000, se a taxa de álcool no sangue for igual ou superior a 2,5 g/l.
    """
    
    with open(os.path.join(legal_articles_dir, "artigo_135.txt"), "w", encoding="utf-8") as f:
        f.write(sample_article)
    
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

# Mock HuggingFaceEmbeddings to prevent model download during tests
@pytest.fixture
def mock_hf_embeddings():
    """Mock HuggingFace embeddings for testing."""
    with patch('langchain_huggingface.HuggingFaceEmbeddings') as mock_embeddings:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 384 for _ in range(5)]  # 5 documents, 384 dimensions
        mock_instance.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_instance
        yield mock_instance

class FineFactory:
    """Factory for creating fine objects for testing."""
    
    @staticmethod
    def create_fine(**overrides) -> models.Fine:
        """Create a fine object with default or overridden values."""
        defaults = {
            "date": date(2025, 11, 11),
            "location": "Avenida da Liberdade, Lisboa",
            "infractor": "João Silva",
            "fine_amount": 150.00,
            "infraction_code": "ART135-1-A",
            "pdf_reference": "MULT-2025-001234"
        }
        defaults.update(overrides)
        
        fine = models.Fine(**defaults)
        return fine

class DefenseFactory:
    """Factory for creating defense objects for testing."""
    
    @staticmethod
    def create_defense(fine_id: int = 1, **overrides) -> models.Defense:
        """Create a defense object with default or overridden values."""
        defaults = {
            "content": "Exemplo de defesa para contraordenação de trânsito.",
            "fine_id": fine_id
        }
        defaults.update(overrides)
        
        defense = models.Defense(**defaults)
        return defense

class LegalDocumentFactory:
    """Factory for creating legal document objects for testing."""
    
    @staticmethod
    def create_legal_document(**overrides) -> models.LegalDocument:
        """Create a legal document object with default or overridden values."""
        defaults = {
            "title": "Artigo 135º do Código da Estrada",
            "document_type": "law",
            "jurisdiction": "Portugal",
            "publication_date": date(2021, 1, 1),
            "source_url": "https://dre.pt/lei/135-codigo-estrada",
            "file_path": "/path/to/document.pdf",
            "extracted_text": "Conteúdo do documento legal...",
            "quality_score": 0.9,
            "relevance_score": 0.8,
            "freshness_score": 0.7,
            "authority_score": 0.95
        }
        defaults.update(overrides)
        
        document = models.LegalDocument(**defaults)
        return document

# Global test utilities
def assert_fine_data_matches(fine: models.Fine, expected_data: Dict[str, Any]):
    """Helper function to assert fine object matches expected data."""
    assert fine.date == expected_data.get("date")
    assert fine.location == expected_data.get("location")
    assert fine.infractor == expected_data.get("infractor")
    assert fine.fine_amount == expected_data.get("fine_amount")
    assert fine.infraction_code == expected_data.get("infraction_code")
    assert fine.pdf_reference == expected_data.get("pdf_reference")

def assert_defense_data_matches(defense: models.Defense, expected_data: Dict[str, Any]):
    """Helper function to assert defense object matches expected data."""
    assert defense.content == expected_data.get("content")
    assert defense.fine_id == expected_data.get("fine_id")

def create_test_db_session():
    """Create a test database session."""
    test_db = SessionLocal()
    try:
        yield test_db
    finally:
        test_db.rollback()
        test_db.close()