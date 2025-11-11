# Development Guide Template

## Getting Started

This guide helps new developers set up their development environment and understand the FineHero project structure.

## Project Overview

FineHero is an AI-powered system for automating traffic fine contestation in Portugal. The system combines:

- **FastAPI Backend**: RESTful API for processing fines and generating defenses
- **CLI Interface**: Command-line tool for advanced users and testing
- **RAG System**: Knowledge base with Portuguese legal documents and precedents
- **OCR Processing**: Advanced document processing for PDF fine notifications
- **AI Generation**: Using Google Generative AI for defense letter generation

## Development Environment Setup

### Prerequisites

#### Required Software
```bash
# Python 3.8 or higher
python --version

# Git
git --version

# Code Editor (VS Code recommended)
code --version

# Docker (optional, for containerized development)
docker --version
```

#### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-por
```

**macOS:**
```bash
brew install python@3.8 git tesseract
```

**Windows:**
```powershell
# Install Python from python.org
# Install Git from git-scm.com
# Install Tesseract from UB-Mannheim/tesseract repository
```

### Initial Setup

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/finehero-ai.git
cd finehero-ai
```

#### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

#### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Environment Variables:**
```bash
# Application
APP_NAME=FineHero AI
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./finehero.db

# External APIs
GOOGLE_API_KEY=your_google_api_key_here

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract
```

#### 5. Initialize Database
```bash
python backend/database_migrations.py
python -c "from backend.app.models import Base; Base.metadata.create_all(bind=database.engine)"
```

#### 6. Download Initial Data
```bash
# Initialize knowledge base
python -c "from rag.ingest import ingest_documents_from_directory; ingest_documents_from_directory()"
```

## Project Structure

```
finehero-ai/
├── backend/                 # FastAPI application
│   ├── app/                # Main application code
│   │   ├── api/            # API routes and controllers
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── crud.py         # Database operations
│   │   └── main.py         # FastAPI application
│   ├── services/           # Business logic services
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── cli/                    # Command-line interface
│   ├── main.py            # CLI entry point
│   └── commands/          # CLI commands
├── rag/                    # RAG system
│   ├── ingest.py          # Document ingestion
│   ├── retriever.py       # Document retrieval
│   └── README.md         # RAG documentation
├── docs/                   # Documentation
│   ├── api/               # API documentation
│   ├── architecture/      # Architecture docs
│   └── templates/         # Documentation templates
├── knowledge_base/         # Legal documents
│   └── legal_articles/
├── vector_store/          # FAISS vector store
├── rules/                 # AI prompt templates
└── scripts/               # Utility scripts
```

## Development Workflow

### Git Workflow

#### Branch Strategy
```bash
# Feature branches
feature/pdf-processing-improvements
feature/rag-enhancement
feature/api-optimization

# Bug fix branches
bugfix/ocr-error-handling
bugfix/database-connection-issue

# Release branches
release/v1.0.0
release/v1.1.0
```

#### Development Process
```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add new feature description"

# 3. Push and create PR
git push origin feature/your-feature-name

# 4. After review and testing, merge to main
```

#### Commit Message Convention
```bash
# Format: type(scope): description

# Features
feat(api): add defense generation endpoint
feat(ocr): implement multiple OCR engines

# Bug fixes
fix(database): resolve connection timeout issue
fix(ocr): handle corrupted PDF files

# Documentation
docs(api): update endpoint documentation
docs(readme): add installation instructions

# Refactoring
refactor(backend): simplify PDF processing logic
refactor(database): optimize query performance

# Testing
test(api): add unit tests for fine endpoints
test(ocr): add integration tests for document processing
```

### Code Style and Standards

#### Python Code Style
We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format code
black .

# Sort imports
isort .

# Check code style
flake8 .
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### Code Quality Tools

**Black Configuration (.black):**
```ini
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
```

**Flake8 Configuration (.flake8):**
```ini
[flake8]
max-line-length = 88
exclude = [
    ".git",
    "__pycache__",
    "venv",
    "node_modules"
]
```

#### Docstring Style
We use **Google-style** docstrings:

```python
def process_fine_pdf(pdf_file: UploadFile) -> FineResponse:
    """
    Process a PDF file containing traffic fine information.
    
    This function extracts text from the PDF using OCR, parses the
    information, and creates a new fine record in the database.
    
    Args:
        pdf_file: The uploaded PDF file containing fine details
        
    Returns:
        FineResponse: Object containing parsed fine data and metadata
        
    Raises:
        ValueError: If the PDF contains invalid or missing data
        OCRProcessingError: If text extraction fails
    """
    pass
```

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                   # Unit tests
│   ├── test_models.py     # Database model tests
│   ├── test_services.py   # Service layer tests
│   └── test_ocr.py        # OCR processing tests
├── integration/           # Integration tests
│   ├── test_api.py        # API endpoint tests
│   ├── test_database.py   # Database integration tests
│   └── test_rag.py        # RAG system tests
└── conftest.py           # Test configuration
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from backend.services.pdf_processor import PDFProcessor
from backend.app.models import Fine

def test_pdf_processor_initialization():
    """Test PDF processor initialization."""
    with open("test_fine.pdf", "rb") as f:
        processor = PDFProcessor(f)
        assert processor.pdf_file is not None
        assert processor.extracted_data == {}

def test_pdf_text_extraction():
    """Test text extraction from PDF."""
    with open("test_fine.pdf", "rb") as f:
        processor = PDFProcessor(f)
        text = processor.extract_text()
        assert isinstance(text, str)
        assert len(text) > 0

@pytest.mark.integration
def test_create_fine_api_endpoint():
    """Test creating a fine through API endpoint."""
    client = TestClient(app)
    fine_data = {
        "date": "2025-11-11",
        "location": "Lisbon",
        "infractor": "John Doe",
        "fine_amount": 150.00,
        "infraction_code": "A123"
    }
    
    response = client.post("/api/v1/fines/", json=fine_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["fine_amount"] == 150.00
    assert data["location"] == "Lisbon"
```

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_ocr.py

# Run tests with coverage
pytest --cov=backend tests/

# Run tests in parallel
pytest -n auto

# Run integration tests only
pytest -m integration
```

### Mocking and Fixtures

#### Database Testing
```python
@pytest.fixture
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=test_engine)
    yield test_session
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_fine(test_db):
    """Create test fine record."""
    fine = Fine(
        date=datetime.date.today(),
        location="Test City",
        infractor="Test User",
        fine_amount=100.00,
        infraction_code="TEST001"
    )
    test_db.add(fine)
    test_db.commit()
    test_db.refresh(fine)
    return fine
```

#### External Service Mocking
```python
from unittest.mock import patch, Mock

@patch('backend.services.ai_service.generate_defense')
def test_defense_generation(mock_generate):
    """Test AI defense generation."""
    # Mock the AI service response
    mock_generate.return_value = "Generated defense text"
    
    # Test the service
    defense_generator = DefenseGenerator(test_fine)
    defense = defense_generator.generate()
    
    assert defense == "Generated defense text"
    mock_generate.assert_called_once()
```

## API Development

### FastAPI Development Patterns

#### Endpoint Structure
```python
# backend/app/api/v1/endpoints/fines.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from ... import schemas, models, crud
from ...database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Fine)
async def create_fine(
    fine: schemas.FineCreate,
    db: Session = Depends(get_db)
):
    """Create a new fine record."""
    return crud.create_fine(db=db, fine=fine)

@router.get("/{fine_id}", response_model=schemas.Fine)
async def read_fine(
    fine_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve a specific fine by ID."""
    db_fine = crud.get_fine(db, fine_id=fine_id)
    if db_fine is None:
        raise HTTPException(status_code=404, detail="Fine not found")
    return db_fine
```

#### Request/Response Models
```python
# backend/app/schemas/fine.py
from pydantic import BaseModel, validator
from datetime import date
from typing import Optional

class FineBase(BaseModel):
    date: date
    location: str
    infractor: str
    fine_amount: float
    infraction_code: str
    pdf_reference: Optional[str] = None

class FineCreate(FineBase):
    """Schema for creating a fine."""
    pass

class Fine(FineBase):
    """Schema for fine responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FineUpdate(BaseModel):
    """Schema for updating a fine."""
    location: Optional[str] = None
    fine_amount: Optional[float] = None
```

#### Error Handling
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@router.post("/", response_model=schemas.Fine)
async def create_fine(
    fine: schemas.FineCreate,
    db: Session = Depends(get_db)
):
    """Create a new fine with proper error handling."""
    try:
        return crud.create_fine(db=db, fine=fine)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Database Operations

#### CRUD Operations Pattern
```python
# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas

def create_fine(db: Session, fine: schemas.FineCreate):
    """Create a new fine in the database."""
    db_fine = models.Fine(**fine.dict())
    db.add(db_fine)
    db.commit()
    db.refresh(db_fine)
    return db_fine

def get_fine(db: Session, fine_id: int):
    """Retrieve a fine by ID."""
    return db.query(models.Fine).filter(models.Fine.id == fine_id).first()

def get_fines(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve multiple fines with pagination."""
    return db.query(models.Fine).offset(skip).limit(limit).all()
```

## CLI Development

### Command Structure
```python
# cli/main.py
import argparse

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FineHero AI CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add subcommands
    process_pdf_parser = subparsers.add_parser("process-pdf")
    process_pdf_parser.add_argument("pdf_path")
    
    args = parser.parse_args()
    
    if args.command == "process-pdf":
        process_pdf(args.pdf_path)

def process_pdf(pdf_path: str):
    """Process a PDF fine."""
    # Implementation here
    pass
```

### CLI Commands Reference

#### Processing PDFs
```bash
# Process a single PDF
python cli/main.py process-pdf /path/to/fine.pdf

# Process with verbose output
python cli/main.py process-pdf /path/to/fine.pdf --verbose

# Output to specific directory
python cli/main.py process-pdf /path/to/fine.pdf --output-dir ./defenses/
```

#### Knowledge Base Management
```bash
# Ingest documents from directory
python cli/main.py ingest dir --path ./knowledge_base/legal_articles/

# Ingest single document
python cli/main.py ingest single --document-json '{"content": "...", "title": "..."}'

# Web scraping
python cli/main.py scrape ansr --max-pages 5
python cli/main.py scrape diario-da-republica --start-url "https://dre.pt/..."
```

## RAG System Development

### Document Ingestion
```python
# rag/ingest.py
def ingest_document_with_metadata(document_data: Dict[str, Any]):
    """Ingest document with metadata into knowledge base."""
    # Calculate quality scores
    quality_scores = calculate_quality_scores(
        document_data['content'], 
        document_data
    )
    
    # Create database record
    db_document = create_document_record(document_data, quality_scores)
    
    # Process for vector storage
    chunks = split_document_into_chunks(document_data['content'])
    embeddings = generate_embeddings(chunks)
    
    # Store in vector database
    save_to_vector_store(chunks, embeddings, db_document.id)
```

### Retrieval System
```python
# rag/retriever.py
class DocumentRetriever:
    """Handles document retrieval from the knowledge base."""
    
    def __init__(self, vector_store_path: str):
        self.vector_store = FAISS.load_local(vector_store_path, embeddings)
        self.db_session = get_database_session()
    
    def retrieve_similar_documents(
        self, 
        query: str, 
        n_results: int = 5
    ) -> List[Dict]:
        """Retrieve documents similar to the query."""
        # Generate query embedding
        query_embedding = generate_embeddings([query])
        
        # Search vector store
        results = self.vector_store.similarity_search_by_vector(
            query_embedding[0], 
            k=n_results
        )
        
        # Enrich with database metadata
        return self._enrich_with_metadata(results)
```

## Debugging and Troubleshooting

### Common Development Issues

#### 1. OCR Processing Errors
**Problem:** PDF text extraction fails  
**Debug Steps:**
```python
# Test OCR directly
import pytesseract
from PIL import Image

# Check if Tesseract is installed
pytesseract.get_tesseract_version()

# Test image processing
image = Image.open("test_image.png")
text = pytesseract.image_to_string(image, lang='por')
print(text)
```

#### 2. Database Connection Issues
**Problem:** Database connection failures  
**Debug Steps:**
```bash
# Check database file
ls -la finehero.db

# Test database connection
python -c "
from backend.database import engine
try:
    connection = engine.connect()
    print('Database connection successful')
    connection.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Reset database
rm finehero.db
python backend/database_migrations.py
```

#### 3. Vector Store Issues
**Problem:** RAG queries return no results  
**Debug Steps:**
```python
# Check vector store files
import os
print("Vector store files:", os.listdir("vector_store"))

# Test vector store loading
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.load_local("vector_store", embeddings)

# Test query
results = vector_store.similarity_search("test query", k=3)
print("Search results:", len(results))
```

### Logging and Monitoring

#### Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finehero.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use in code
logger.info("Starting PDF processing")
logger.error(f"OCR failed: {error}")
logger.debug(f"Extracted text length: {len(text)}")
```

#### Development Tools
```bash
# Monitor logs in real-time
tail -f finehero.log

# Profile performance
python -m cProfile -o profile_output.prof script.py

# Memory usage analysis
python -m memory_profiler script.py
```

## Performance Optimization

### Database Optimization
```python
# Use indexes for frequently queried fields
# In models.py
class Fine(Base):
    __tablename__ = "fines"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)  # Index for location queries
    infraction_code = Column(String, index=True)  # Index for code queries
    fine_amount = Column(Float)
    date = Column(Date, index=True)  # Index for date range queries

# Use pagination for large datasets
def get_fines_with_pagination(db: Session, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    return db.query(models.Fine)\
             .offset(offset)\
             .limit(per_page)\
             .all()
```

### Memory Management
```python
# Process large documents in chunks
def process_large_pdf(pdf_path: str):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                yield text  # Yield instead of storing all

# Use context managers for resource cleanup
def process_documents(documents):
    with DatabaseSession() as db:
        for doc in documents:
            process_single_document(doc, db)
```

## Contributing Guidelines

### Code Review Process
1. Create feature branch
2. Write tests for new functionality
3. Run all tests locally
4. Submit pull request with description
5. Address review feedback
6. Merge after approval

### Documentation Updates
- Update README.md for new features
- Add API documentation for new endpoints
- Update deployment guides for environment changes
- Include code examples in docstrings

### Release Process
1. Update version numbers
2. Create release notes
3. Run full test suite
4. Tag release in Git
5. Deploy to staging
6. Deploy to production

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Review Frequency:** Monthly  
**Owner:** Development Team