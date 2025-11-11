# Troubleshooting Guide Template

## Overview

This guide provides solutions to common issues and problems encountered in the FineHero system.

## Quick Diagnosis

### System Health Check
```bash
# Check API status
curl http://localhost:8000/health

# Check database connectivity
python -c "from backend.database import engine; print('DB OK' if engine.connect() else 'DB FAILED')"

# Check vector store
python -c "import faiss; print('Vector store OK') if faiss.read_index('vector_store/index.faiss') else print('Vector store FAILED')"

# Check OCR service
docker-compose exec api tesseract --version
```

### Log Analysis
```bash
# Application logs
docker-compose logs -f api

# Database logs
docker-compose logs -f postgres

# System resources
docker stats
df -h
free -h
```

## Common Issues and Solutions

### OCR Processing Issues

#### Problem: PDF Text Extraction Fails
**Symptoms:**
- OCR returns empty or garbled text
- Processing timeout errors
- "No text found in PDF" messages

**Possible Causes:**
1. Tesseract not installed or configured incorrectly
2. PDF is image-based (scanned document)
3. Corrupted PDF file
4. Memory issues with large PDFs

**Solutions:**

**Solution 1: Verify Tesseract Installation**
```bash
# Check Tesseract installation
tesseract --version

# Check available languages
tesseract --list-langs

# Install Portuguese language data
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr-por

# macOS:
brew install tesseract-lang

# Verify language support
tesseract --list-langs | grep por
```

**Solution 2: Test OCR Directly**
```python
from PIL import Image
import pytesseract

# Test with a simple image
try:
    # Create test image with text
    from PIL import ImageDraw, ImageFont
    
    img = Image.new('RGB', (200, 50), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Teste de texto", fill='black')
    
    # Test OCR
    text = pytesseract.image_to_string(img, lang='por')
    print(f"OCR Test Result: '{text}'")
    
    if text.strip():
        print("✅ OCR is working correctly")
    else:
        print("❌ OCR is not returning text")
        
except Exception as e:
    print(f"❌ OCR test failed: {e}")
```

**Solution 3: Handle Large PDFs**
```python
import pdfplumber

def process_large_pdf_safely(pdf_path: str):
    """Process large PDFs with memory management."""
    with pdfplumber.open(pdf_path) as pdf:
        text_chunks = []
        total_pages = len(pdf.pages)
        
        for i, page in enumerate(pdf.pages):
            try:
                # Process pages individually
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_chunks.append(f"--- Page {i+1}/{total_pages} ---\n{page_text}")
                
                # Log progress for large PDFs
                if (i + 1) % 10 == 0:
                    print(f"Processed {i+1}/{total_pages} pages")
                    
            except Exception as e:
                print(f"Warning: Could not process page {i+1}: {e}")
                continue
        
        return "\n\n".join(text_chunks)
```

#### Problem: OCR Accuracy Issues
**Symptoms:**
- Extracted text has many errors
- Special characters not recognized
- Numbers or dates incorrectly parsed

**Solutions:**

**Solution: Use Multiple OCR Engines**
```python
import easyocr
import pytesseract
from PIL import Image
import numpy as np

class MultiOCR:
    def __init__(self):
        self.tesseract_reader = None
        self.easyocr_reader = easyocr.Reader(['en', 'pt'])
    
    def extract_text_with_fallback(self, image_path: str):
        """Try multiple OCR engines for better accuracy."""
        
        # Convert PDF page to image
        with pdfplumber.open(image_path) as pdf:
            first_page = pdf.pages[0]
            page_image = first_page.to_image()
            img_byte_arr = io.BytesIO()
            page_image.original.save(img_byte_arr, format='PNG')
            img = Image.open(img_byte_arr)
        
        results = []
        
        # Try Tesseract first
        try:
            tesseract_text = pytesseract.image_to_string(img, lang='por+eng')
            if tesseract_text.strip():
                results.append(('tesseract', tesseract_text))
        except Exception as e:
            print(f"Tesseract failed: {e}")
        
        # Try EasyOCR
        try:
            easyocr_results = self.easyocr_reader.readtext(np.array(img))
            easyocr_text = ' '.join([text for (_, text, _) in easyocr_results])
            if easyocr_text.strip():
                results.append(('easyocr', easyocr_text))
        except Exception as e:
            print(f"EasyOCR failed: {e}")
        
        return results

# Usage
ocr = MultiOCR()
results = ocr.extract_text_with_fallback("fine.pdf")
for engine, text in results:
    print(f"{engine}: {text[:100]}...")
```

### Database Issues

#### Problem: Database Connection Errors
**Symptoms:**
- "database is locked" errors
- Connection timeout messages
- SQLAlchemy operational errors

**Solutions:**

**Solution 1: Fix SQLite Lock Issues**
```python
import sqlite3
import time

def wait_for_database(db_path: str, max_retries: int = 30):
    """Wait for database to become available."""
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"Database locked, attempt {attempt + 1}/{max_retries}")
                time.sleep(1)
            else:
                raise e
    return False

# Use before database operations
if not wait_for_database("finehero.db"):
    raise Exception("Database is permanently locked")
```

**Solution 2: Database Migration Issues**
```python
# Reset database safely
def reset_database():
    """Safely reset the database."""
    import os
    
    # Backup existing database
    if os.path.exists("finehero.db"):
        os.rename("finehero.db", "finehero.db.backup")
    
    # Recreate database
    from backend.app.models import Base
    from backend.database import engine
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database recreated")
```

#### Problem: Data Integrity Issues
**Symptoms:**
- Inconsistent data in database
- Foreign key constraint violations
- Missing related records

**Solutions:**

**Solution: Data Validation and Cleanup**
```python
from sqlalchemy import text
from backend.database import SessionLocal

def validate_and_cleanup_data():
    """Validate and clean up database data."""
    db = SessionLocal()
    
    try:
        # Check for orphaned fine records
        orphaned_fines = db.execute(text("""
            SELECT f.id, f.location 
            FROM fines f 
            LEFT JOIN defenses d ON f.id = d.fine_id 
            WHERE d.fine_id IS NULL
        """)).fetchall()
        
        if orphaned_fines:
            print(f"Found {len(orphaned_fines)} orphaned fines")
            # Handle orphaned records appropriately
        
        # Check for missing required fields
        missing_data = db.execute(text("""
            SELECT id, location, infraction_code 
            FROM fines 
            WHERE location IS NULL OR infraction_code IS NULL
        """)).fetchall()
        
        if missing_data:
            print(f"Found {len(missing_data)} fines with missing required data")
            
    finally:
        db.close()
```

### RAG System Issues

#### Problem: Vector Store Corruption
**Symptoms:**
- FAISS index errors
- "Index not found" messages
- RAG queries return no results

**Solutions:**

**Solution 1: Rebuild Vector Store**
```python
import shutil
import os

def rebuild_vector_store():
    """Rebuild the vector store from scratch."""
    
    # Backup existing store
    if os.path.exists("vector_store"):
        shutil.move("vector_store", f"vector_store_backup_{int(time.time())}")
    
    # Recreate vector store
    from rag.ingest import ingest_documents_from_directory
    ingest_documents_from_directory()
    
    print("✅ Vector store rebuilt successfully")
```

**Solution 2: Check Vector Store Integrity**
```python
import faiss
import os

def check_vector_store_integrity():
    """Check if vector store files are intact."""
    
    required_files = ["index.faiss", "index.pkl"]
    vector_store_dir = "vector_store"
    
    if not os.path.exists(vector_store_dir):
        print("❌ Vector store directory not found")
        return False
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(vector_store_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing vector store files: {missing_files}")
        return False
    
    try:
        # Try to load index
        index = faiss.read_index(os.path.join(vector_store_dir, "index.faiss"))
        print(f"✅ Vector store loaded successfully, dimension: {index.d}")
        return True
    except Exception as e:
        print(f"❌ Vector store corrupted: {e}")
        return False
```

### API Issues

#### Problem: Slow API Responses
**Symptoms:**
- API timeouts (> 30 seconds)
- High response times
- Database query performance issues

**Solutions:**

**Solution 1: Database Query Optimization**
```python
from sqlalchemy import text

def optimize_slow_queries():
    """Optimize database queries for better performance."""
    db = SessionLocal()
    
    try:
        # Add missing indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_location 
            ON fines(location)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_date 
            ON fines(date)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fines_amount 
            ON fines(fine_amount)
        """))
        
        db.commit()
        print("✅ Database indexes created")
        
    finally:
        db.close()
```

**Solution 2: API Response Caching**
```python
from functools import lru_cache
from typing import Optional

class APICache:
    def __init__(self, maxsize: int = 1000):
        self.cache = {}
        self.maxsize = maxsize
    
    @lru_cache(maxsize=100)
    def get_fines_summary(self, date_filter: Optional[str] = None):
        """Cache expensive database queries."""
        db = SessionLocal()
        try:
            if date_filter:
                query = text("""
                    SELECT location, COUNT(*), AVG(fine_amount)
                    FROM fines 
                    WHERE date >= :date_filter
                    GROUP BY location
                """)
                result = db.execute(query, {"date_filter": date_filter}).fetchall()
            else:
                query = text("""
                    SELECT location, COUNT(*), AVG(fine_amount)
                    FROM fines 
                    GROUP BY location
                """)
                result = db.execute(query).fetchall()
            
            return dict(result)
        finally:
            db.close()

# Use in API endpoints
api_cache = APICache()

@app.get("/api/v1/fines/summary")
async def get_fines_summary(date_filter: Optional[str] = None):
    return api_cache.get_fines_summary(date_filter)
```

### Memory and Performance Issues

#### Problem: High Memory Usage
**Symptoms:**
- System becomes unresponsive
- Out of memory errors
- Slow processing speeds

**Solutions:**

**Solution 1: Memory-Efficient PDF Processing**
```python
import gc
from typing import Iterator

def process_pdfs_memory_efficient(pdf_paths: list) -> Iterator[str]:
    """Process PDFs one at a time to manage memory."""
    
    for pdf_path in pdf_paths:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        yield text
            
            # Force garbage collection after each file
            gc.collect()
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            continue
```

**Solution 2: Database Connection Pooling**
```python
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

# Configure connection pooling
DATABASE_URL = "sqlite:///./finehero.db"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600
)
```

## Error Codes and Meanings

### Application Error Codes

| Error Code | HTTP Status | Description | Solution |
|------------|-------------|-------------|----------|
| `OCR_001` | 422 | PDF text extraction failed | Check OCR service installation |
| `OCR_002` | 422 | No text found in PDF | Verify PDF is not corrupted |
| `DB_001` | 500 | Database connection failed | Check database service status |
| `DB_002` | 500 | Database locked | Wait and retry database operations |
| `VEC_001` | 500 | Vector store corrupted | Rebuild vector store |
| `VEC_002` | 404 | Vector store not found | Initialize knowledge base |
| `API_001` | 429 | Rate limit exceeded | Wait before making more requests |
| `API_002` | 422 | Invalid request format | Check request schema |

### Database Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `SQLITE_BUSY` | Database is locked | Wait and retry operations |
| `SQLITE_CORRUPT` | Database is corrupted | Restore from backup or recreate |
| `FK_VIOLATION` | Foreign key constraint violation | Check data consistency |
| `UNIQUE_VIOLATION` | Duplicate key constraint violation | Check for existing records |

## Diagnostic Commands

### System Diagnostics
```bash
#!/bin/bash
# diagnostics.sh - Comprehensive system check

echo "=== FineHero System Diagnostics ==="

# Check services
echo "Checking services..."
docker-compose ps

# Check disk space
echo "Disk usage:"
df -h

# Check memory usage
echo "Memory usage:"
free -h

# Check logs for errors
echo "Recent errors in API logs:"
docker-compose logs --tail=50 api | grep -i error || echo "No recent errors"

# Check database
echo "Testing database connection..."
python -c "
from backend.database import engine
try:
    conn = engine.connect()
    print('✅ Database connection OK')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Check vector store
echo "Testing vector store..."
python -c "
import faiss
import os
try:
    if os.path.exists('vector_store/index.faiss'):
        index = faiss.read_index('vector_store/index.faiss')
        print(f'✅ Vector store OK (dimension: {index.d})')
    else:
        print('❌ Vector store not found')
except Exception as e:
    print(f'❌ Vector store error: {e}')
"

echo "=== Diagnostics Complete ==="
```

### Performance Monitoring
```bash
# Monitor API performance
watch -n 5 'curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health'

# Monitor database performance
watch -n 10 "docker-compose exec postgres psql -U finehero_user -d finehero_prod -c 'SELECT * FROM pg_stat_activity;'"

# Monitor system resources
top -p $(pgrep -f "uvicorn\|python.*main.py")
```

## Emergency Procedures

### Complete System Reset
```bash
#!/bin/bash
# emergency_reset.sh - Complete system reset

echo "Starting emergency system reset..."

# Stop all services
docker-compose down

# Backup existing data
if [ -f "finehero.db" ]; then
    cp finehero.db "backup/finehero_$(date +%Y%m%d_%H%M%S).db"
fi

# Remove all data
rm -rf finehero.db
rm -rf vector_store/*
rm -rf knowledge_base/processed/*

# Reset to clean state
docker-compose up -d --build

# Recreate database
docker-compose exec api python backend/database_migrations.py

# Reinitialize knowledge base
docker-compose exec api python -c "from rag.ingest import ingest_documents_from_directory; ingest_documents_from_directory()"

echo "Emergency reset complete"
```

### Data Recovery Procedures
```bash
# Restore database from backup
gunzip -c /backups/finehero_20251111.sql.gz | docker-compose exec -T postgres psql -U finehero_user finehero_prod

# Restore vector store
tar -xzf /backups/vector_store_20251111.tar.gz

# Verify restoration
python -c "
from backend.database import SessionLocal
from backend.app.models import Fine

db = SessionLocal()
count = db.query(Fine).count()
print(f'Restored database contains {count} fine records')
db.close()
"
```

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Review Frequency:** Monthly  
**Owner:** DevOps Team