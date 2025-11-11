# Development Workflow Framework

## Overview

This framework establishes comprehensive development workflows, standards, and procedures for the FineHero project. It ensures consistency, quality, and efficiency across all development activities.

## Framework Components

### 1. Coding Standards and Style Guides

#### Python Coding Standards

**Code Formatting and Style:**
```python
# black --line-length 88 --target-version py38
# isort --profile black
# flake8 --max-line-length 88

from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

import fastapi
import sqlalchemy
from pydantic import BaseModel, validator

from backend.app.models import Fine, Defense
from backend.core.config import settings

logger = logging.getLogger(__name__)


class FineProcessingError(Exception):
    """Custom exception for fine processing errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class PDFProcessor:
    """Process PDF fine documents with OCR and text extraction."""
    
    def __init__(self, pdf_file_path: str) -> None:
        self.pdf_file_path = pdf_file_path
        self.extracted_data: Dict[str, str] = {}
        
    def extract_text(self) -> str:
        """Extract text using multiple OCR engines."""
        try:
            # Try pdfplumber first for text-based PDFs
            text = self._extract_with_pdfplumber()
            if text.strip():
                return text
                
            # Fallback to OCR engines
            return self._extract_with_ocr()
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise FineProcessingError(
                f"Failed to extract text from PDF: {e}",
                error_code="OCR_001"
            )
    
    def _extract_with_pdfplumber(self) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber
        
        with pdfplumber.open(self.pdf_file_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            return "\n".join(pages_text)
```

**Type Hints and Documentation:**
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DocumentProcessor(Protocol):
    """Protocol for document processing services."""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from document."""
        ...
    
    def parse_data(self, text: str) -> Dict[str, Union[str, float, int]]:
        """Parse structured data from extracted text."""
        ...


class FineData(BaseModel):
    """Structured fine data from PDF processing."""
    
    date: datetime
    location: str
    infractor: str
    fine_amount: float
    infraction_code: str
    
    @validator('fine_amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Fine amount must be positive')
        return v
    
    @validator('location')
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
```

#### Database Coding Standards

**SQLAlchemy Models:**
```python
from sqlalchemy import (
    Column, Integer, String, Float, Date, Text, 
    ForeignKey, DateTime, Boolean, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Fine(Base):
    """Traffic fine database model."""
    
    __tablename__ = "fines"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core fine data
    date = Column(Date, nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    infractor = Column(String(255), nullable=False)
    fine_amount = Column(Float(10, 2), nullable=False)
    infraction_code = Column(String(50), nullable=False, index=True)
    
    # PDF processing
    pdf_reference = Column(String(500))
    extracted_text = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    defenses = relationship("Defense", back_populates="fine")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fine_date_location', 'date', 'location'),
        Index('idx_fine_amount_code', 'fine_amount', 'infraction_code'),
    )
    
    def __repr__(self) -> str:
        return f"<Fine(id={self.id}, location='{self.location}', amount={self.fine_amount})>"


class LegalDocument(Base):
    """Legal document for RAG knowledge base."""
    
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    document_type = Column(String(100), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=False, index=True)
    publication_date = Column(Date, nullable=True)
    source_url = Column(String(1000), unique=True, index=True)
    
    # Content and metadata
    extracted_text = Column(Text, nullable=False)
    quality_score = Column(Float(3, 2), default=0.0)
    relevance_score = Column(Float(3, 2), default=0.0)
    freshness_score = Column(Float(3, 2), default=0.0)
    authority_score = Column(Float(3, 2), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    retrieval_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case_outcome_id = Column(Integer, ForeignKey("case_outcomes.id"), nullable=True)
    case_outcome = relationship("CaseOutcome", back_populates="legal_documents")
```

#### API Development Standards

**FastAPI Endpoints:**
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app import schemas, crud
from backend.core.database import get_db
from backend.services.pdf_processor import PDFProcessor, FineProcessingError

router = APIRouter()


@router.post(
    "/fines/",
    response_model=schemas.FineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new fine from PDF",
    tags=["fines"]
)
async def create_fine(
    *,
    db: Session = Depends(get_db),
    fine_in: schemas.FineCreate,
    current_user: Optional[schemas.User] = Depends(get_current_user)
) -> schemas.FineResponse:
    """
    Create a new fine record from processed PDF data.
    
    This endpoint accepts structured fine data extracted from PDF documents
    and creates a database record for further processing.
    
    Args:
        fine_in: Fine data including date, location, infractor details, etc.
        db: Database session dependency
        current_user: Current authenticated user (optional)
    
    Returns:
        Created fine record with ID and metadata
    
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Validate fine data
        fine_data = schemas.FineCreate(**fine_in.dict())
        
        # Create fine record
        db_fine = crud.create_fine(db=db, fine=fine_data)
        
        # Log creation event
        logger.info(
            f"Fine created: ID={db_fine.id}, location={db_fine.location}, "
            f"amount={db_fine.fine_amount}"
        )
        
        return schemas.FineResponse.from_orm(db_fine)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Database error creating fine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create fine record"
        )


@router.post(
    "/fines/{fine_id}/defense",
    response_model=schemas.DefenseResponse,
    summary="Generate defense for fine",
    tags=["defenses"]
)
async def generate_defense(
    fine_id: int,
    *,
    db: Session = Depends(get_db),
    defense_request: schemas.DefenseRequest,
    current_user: schemas.User = Depends(get_current_user)
) -> schemas.DefenseResponse:
    """
    Generate AI-powered defense for a specific fine.
    
    This endpoint uses the RAG knowledge base and AI services to generate
    a customized defense based on the fine details and legal precedents.
    
    Args:
        fine_id: ID of the fine to generate defense for
        defense_request: Defense generation parameters
        db: Database session dependency
        current_user: Authenticated user
    
    Returns:
        Generated defense content with metadata
    
    Raises:
        HTTPException: If fine not found or generation fails
    """
    # Check if fine exists
    fine = crud.get_fine(db=db, fine_id=fine_id)
    if not fine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fine not found"
        )
    
    try:
        # Generate defense using AI service
        defense_content = await defense_generator.generate(
            fine=fine,
            custom_arguments=defense_request.custom_arguments,
            defense_type=defense_request.defense_type
        )
        
        # Create defense record
        defense_data = schemas.DefenseCreate(
            fine_id=fine_id,
            content=defense_content,
            defense_type=defense_request.defense_type
        )
        
        db_defense = crud.create_defense(db=db, defense=defense_data)
        
        logger.info(
            f"Defense generated: fine_id={fine_id}, "
            f"defense_id={db_defense.id}, "
            f"user_id={current_user.id}"
        )
        
        return schemas.DefenseResponse.from_orm(db_defense)
        
    except Exception as e:
        logger.error(f"Defense generation failed for fine {fine_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate defense"
        )
```

### 2. Testing Standards and Quality Assurance

#### Test Structure and Organization

```
tests/
├── unit/                           # Unit tests
│   ├── test_models.py              # Database model tests
│   ├── test_services/              # Service layer tests
│   │   ├── test_pdf_processor.py   # PDF processing tests
│   │   ├── test_ocr_engine.py      # OCR engine tests
│   │   ├── test_ai_service.py      # AI service tests
│   │   └── test_rag_system.py      # RAG system tests
│   ├── test_api/                   # API endpoint tests
│   │   ├── test_fines.py           # Fine management tests
│   │   ├── test_defenses.py        # Defense generation tests
│   │   └── test_health.py          # Health check tests
│   └── conftest.py                 # Test configuration and fixtures
├── integration/                    # Integration tests
│   ├── test_database.py            # Database integration
│   ├── test_external_apis.py       # External API integration
│   └── test_pdf_pipeline.py        # End-to-end PDF processing
├── e2e/                           # End-to-end tests
│   ├── test_fine_processing.py     # Complete fine processing flow
│   └── test_defense_generation.py  # Complete defense generation
├── performance/                   # Performance and load tests
│   ├── test_api_performance.py     # API performance tests
│   ├── test_ocr_performance.py     # OCR performance tests
│   └── test_rag_performance.py     # RAG system performance
├── fixtures/                      # Test data and fixtures
│   ├── sample_pdfs/                # Sample PDF files
│   ├── sample_fines.py             # Sample fine data
│   └── sample_legal_docs.py        # Sample legal documents
└── utils/                         # Test utilities
    ├── test_helpers.py             # Helper functions
    ├── mock_data.py                # Mock data generators
    └── assertions.py               # Custom assertions
```

#### Test Implementation Standards

**Unit Test Example:**
```python
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import date

from backend.services.pdf_processor import PDFProcessor, FineProcessingError
from backend.app.models import Fine


class TestPDFProcessor:
    """Test suite for PDFProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return PDFProcessor("test_fine.pdf")
    
    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create sample PDF file for testing."""
        pdf_path = tmp_path / "test_fine.pdf"
        # Create minimal PDF content
        pdf_path.write_bytes(b"%PDF-1.4\n% Sample PDF content")
        return str(pdf_path)
    
    def test_extract_text_pdfplumber_success(self, processor):
        """Test successful text extraction with pdfplumber."""
        # Arrange
        mock_text = "Sample fine text content"
        with patch('pdfplumber.open') as mock_pdfplumber:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdfplumber.return_value.__enter__.return_value.pages = [mock_page]
            
            # Act
            result = processor.extract_text()
            
            # Assert
            assert result == mock_text
            mock_pdfplumber.assert_called_once()
    
    def test_extract_text_ocr_fallback(self, processor):
        """Test OCR fallback when pdfplumber fails."""
        # Arrange
        with patch('pdfplumber.open') as mock_pdfplumber:
            mock_pdfplumber.side_effect = Exception("PDF processing failed")
            
            with patch.object(processor, '_extract_with_ocr') as mock_ocr:
                mock_ocr.return_value = "OCR extracted text"
                
                # Act
                result = processor.extract_text()
                
                # Assert
                assert result == "OCR extracted text"
                mock_ocr.assert_called_once()
    
    def test_extract_text_no_content(self, processor):
        """Test handling of PDFs with no extractable content."""
        # Arrange
        with patch('pdfplumber.open') as mock_pdfplumber:
            mock_page = Mock()
            mock_page.extract_text.return_value = None
            mock_pdfplumber.return_value.__enter__.return_value.pages = [mock_page]
            
            with patch.object(processor, '_extract_with_ocr') as mock_ocr:
                mock_ocr.return_value = ""
                
                # Act & Assert
                with pytest.raises(FineProcessingError) as exc_info:
                    processor.extract_text()
                
                assert "No text content found" in str(exc_info.value)
    
    @patch('pytesseract.image_to_string')
    def test_ocr_extraction_with_tesseract(self, mock_tesseract, processor):
        """Test OCR extraction using Tesseract."""
        # Arrange
        mock_tesseract.return_value = "Tesseract extracted text"
        
        # Act
        result = processor._extract_with_ocr()
        
        # Assert
        assert result == "Tesseract extracted text"
        mock_tesseract.assert_called_once()
```

**Integration Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.models import Base
from backend.core.config import settings


class TestFineAPI:
    """Integration tests for Fine API endpoints."""
    
    @pytest.fixture(scope="session")
    def test_db(self):
        """Create test database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        yield engine
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_create_fine_success(self, client):
        """Test successful fine creation via API."""
        # Arrange
        fine_data = {
            "date": "2025-11-11",
            "location": "Lisbon",
            "infractor": "João Silva",
            "fine_amount": 150.00,
            "infraction_code": "A123"
        }
        
        # Act
        response = client.post("/api/v1/fines/", json=fine_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["location"] == "Lisbon"
        assert data["fine_amount"] == 150.00
        assert "id" in data
        assert "created_at" in data
    
    def test_create_fine_validation_error(self, client):
        """Test fine creation with invalid data."""
        # Arrange
        invalid_data = {
            "date": "2025-11-11",
            "location": "",  # Invalid: empty location
            "fine_amount": -50.00,  # Invalid: negative amount
            "infraction_code": "A123"
        }
        
        # Act
        response = client.post("/api/v1/fines/", json=invalid_data)
        
        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("location" in error["loc"] for error in errors)
        assert any("fine_amount" in error["loc"] for error in errors)
```

#### Test Quality Standards

**Coverage Requirements:**
- **Unit Tests**: > 90% code coverage
- **Integration Tests**: All API endpoints covered
- **Critical Paths**: 100% coverage for payment, security, data processing
- **Error Handling**: Test all error conditions and edge cases

**Test Data Management:**
```python
# tests/fixtures/sample_data.py
import json
from datetime import date, datetime
from decimal import Decimal


SAMPLE_FINE_DATA = {
    "date": "2025-11-11",
    "location": "Lisbon, Portugal",
    "infractor": "João da Silva",
    "fine_amount": Decimal("150.00"),
    "infraction_code": "ART135-1-A",
    "pdf_reference": "MULT_2025_001.pdf"
}

SAMPLE_LEGAL_DOCUMENT = {
    "title": "Artigo 135º do Código da Estrada",
    "document_type": "law",
    "jurisdiction": "Portugal",
    "publication_date": date(2021, 1, 1),
    "extracted_text": "Art. 135º - Condução sob influência do álcool...",
    "source_url": "https://dre.pt/lei/135-codigo-estrada",
    "quality_score": 0.95,
    "relevance_score": 0.90,
    "freshness_score": 0.85,
    "authority_score": 0.98
}
```

### 3. Git Workflow and Contribution Guidelines

#### Branch Strategy

```bash
# Branch naming conventions
main                    # Production branch
develop                 # Integration branch
feature/ocr-enhancement # New features
bugfix/ocr-error-fix    # Bug fixes
hotfix/security-patch   # Critical fixes
release/v1.0.0          # Release branches
docs/api-documentation  # Documentation updates
refactor/pdf-processing # Code refactoring
```

#### Commit Message Standards

```bash
# Conventional Commits format
type(scope): subject

[optional body]

[optional footer]

# Examples:
feat(api): add defense generation endpoint
- Implements POST /api/v1/defenses/{fine_id}
- Includes custom arguments support
- Adds comprehensive error handling
- Resolves #123

fix(ocr): resolve text extraction failures on scanned PDFs
- Adds fallback OCR engine support
- Improves error handling and logging
- Includes unit tests for new functionality
- Closes #456

docs: update API documentation with new endpoints
- Documents defense generation API
- Adds code examples and SDK integration
- Updates authentication section

refactor(database): optimize query performance for large datasets
- Adds indexes for frequently queried columns
- Implements connection pooling
- Improves memory usage for bulk operations
```

#### Pull Request Process

**PR Template:**
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Architecture & Design
- [ ] This change follows existing architecture patterns
- [ ] New ADR created (link to ADR if applicable)
- [ ] Architecture diagrams updated
- [ ] Security implications considered

## Testing
- [ ] Unit tests added/updated and passing
- [ ] Integration tests added/updated and passing
- [ ] End-to-end tests added/updated and passing
- [ ] Manual testing completed
- [ ] Test coverage meets requirements (>90%)

## Documentation
- [ ] API documentation updated
- [ ] README.md updated if applicable
- [ ] Deployment documentation updated
- [ ] Troubleshooting guide updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code builds successfully
- [ ] No merge conflicts
- [ ] Related issues linked (Closes #XXX)

## Screenshots/Demos
If applicable, add screenshots or demo videos.

## Additional Notes
Any additional information or context.
```

**Code Review Checklist:**
- [ ] **Functionality**: Code implements intended functionality correctly
- [ ] **Performance**: No obvious performance issues
- [ ] **Security**: Security considerations addressed
- [ ] **Error Handling**: Proper error handling implemented
- [ ] **Testing**: Appropriate tests included and passing
- [ ] **Documentation**: Code commented and documented
- [ ] **Style**: Follows project coding standards
- [ ] **Dependencies**: No unnecessary dependencies added
- [ ] **Breaking Changes**: Backward compatibility maintained
- [ ] **Architecture**: Follows established architectural patterns

### 4. Issue Tracking and Project Management

#### Issue Templates

**Bug Report Template:**
```markdown
## Bug Description
Clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- **OS**: [e.g., Ubuntu 20.04, Windows 10, macOS 12.0]
- **Python Version**: [e.g., 3.8.10]
- **FineHero Version**: [e.g., v1.0.0]
- **Browser**: [if applicable, e.g., Chrome 95.0]

## Additional Context
Screenshots, error logs, or any other context that helps understand the issue.

## Priority
- [ ] Critical - System down, no workaround
- [ ] High - Major functionality broken, workaround exists
- [ ] Medium - Minor functionality broken
- [ ] Low - Enhancement or cosmetic issue
```

**Feature Request Template:**
```markdown
## Feature Description
Clear and concise description of the feature you'd like to see implemented.

## Problem Statement
What problem does this feature solve? Is your feature request related to a problem?

## Proposed Solution
Describe the solution you'd like to see implemented.

## Alternatives Considered
Describe any alternative solutions or features you've considered.

## User Stories
As a [type of user], I want [goal] so that [benefit].

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Considerations
Any technical constraints, dependencies, or architectural considerations.

## Priority
- [ ] High - Core functionality enhancement
- [ ] Medium - Nice-to-have feature
- [ ] Low - Future enhancement
```

#### Project Board Structure

```yaml
# GitHub Project Board Columns
columns:
  - name: "Backlog"
    description: "Ideas and feature requests"
    
  - name: "To Do"
    description: "Ready for development"
    
  - name: "In Progress"
    description: "Currently being worked on"
    
  - name: "Review"
    description: "Awaiting code review"
    
  - name: "Testing"
    description: "QA testing phase"
    
  - name: "Done"
    description: "Completed and deployed"
```

#### Sprint Planning Template

```markdown
# Sprint Planning - [Sprint Number]

## Sprint Goals
1. [Primary goal]
2. [Secondary goal]
3. [Tertiary goal]

## Capacity Planning
- **Team Members**: [List with availability]
- **Total Story Points**: [Planned for sprint]
- **Team Velocity**: [Average points per sprint]

## Sprint Backlog

### Must Have (Priority 1)
| Issue | Story Points | Owner | Status |
|-------|--------------|-------|--------|
| #123 - Implement OCR fallback | 8 | Developer | To Do |
| #456 - Add API rate limiting | 5 | Developer | To Do |
| #789 - Fix database performance | 3 | Developer | To Do |

### Should Have (Priority 2)
| Issue | Story Points | Owner | Status |
|-------|--------------|-------|--------|
| #101 - Improve error messages | 3 | Developer | To Do |
| #112 - Add monitoring dashboard | 8 | Developer | To Do |

### Could Have (Priority 3)
| Issue | Story Points | Owner | Status |
|-------|--------------|-------|--------|
| #113 - Add unit test coverage | 5 | Developer | To Do |

## Dependencies
| Dependency | Owner | Due Date | Status |
|------------|-------|----------|--------|
| External API integration | Team | [Date] | In Progress |
| Database migration | Team | [Date] | To Do |

## Definition of Done
- [ ] Code written and reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Deployed to staging environment
- [ ] Acceptance criteria met
- [ ] No critical bugs
```

## Quality Assurance Process

### Continuous Integration

**GitHub Actions Workflow:**
```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.8'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run linting
      run: |
        black --check .
        isort --check-only .
        flake8 .
    
    - name: Run type checking
      run: mypy .
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=backend --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        GOOGLE_API_KEY: test_api_key
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        GOOGLE_API_KEY: test_api_key
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Quality Gates

**Pre-merge Requirements:**
- [ ] All CI checks passing
- [ ] Code coverage > 90%
- [ ] No critical security vulnerabilities
- [ ] Performance tests passing
- [ ] Documentation updated
- [ ] No breaking changes without migration plan

**Pre-release Requirements:**
- [ ] All automated tests passing
- [ ] Manual testing completed
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Rollback plan tested

## Success Metrics

### Development Metrics
- **Lead Time**: Time from feature request to production deployment
- **Cycle Time**: Time from development start to completion
- **Deployment Frequency**: How often we deploy to production
- **Mean Time to Recovery**: Time to recover from production issues
- **Change Failure Rate**: Percentage of deployments causing failures

### Quality Metrics
- **Code Coverage**: Percentage of code covered by tests
- **Bug Rate**: Number of bugs per KLOC
- **Technical Debt**: Estimated time to fix debt items
- **Code Complexity**: Cyclomatic complexity metrics
- **Security Issues**: Number of security vulnerabilities

### Process Metrics
- **Pull Request Review Time**: Average time to review PRs
- **Test Automation Rate**: Percentage of tests that are automated
- **Documentation Coverage**: Percentage of code documented
- **Knowledge Transfer**: New team member onboarding time

---

**Framework Version:** 1.0  
**Last Updated:** 2025-11-11T15:51:22.680Z  
**Owner:** Development Team  
**Review Frequency:** Quarterly