# Deployment Guide Template

## Overview

This guide provides step-by-step instructions for deploying the FineHero application to various environments.

## Deployment Architecture

### System Overview
```mermaid
graph TB
    subgraph "External"
        U[Users]
        L[Load Balancer]
    end
    
    subgraph "Application Tier"
        API1[API Server 1]
        API2[API Server 2]
        CLI[CLI Interface]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL)]
        VS[(Vector Store)]
        KB[Knowledge Base]
    end
    
    subgraph "External Services"
        OCR[OCR Services]
        AI[AI/ML Services]
    end
    
    U --> L
    L --> API1
    L --> API2
    API1 --> DB
    API2 --> DB
    API1 --> VS
    API2 --> VS
    API1 --> KB
    API2 --> KB
    API1 --> OCR
    API2 --> OCR
    API1 --> AI
    API2 --> AI
```

## Prerequisites

### Required Software
- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Git**: Version 2.30+
- **Python**: Version 3.8+ (for local development)

### System Requirements
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 20GB free space
- **Network**: Internet connection for external services

### External Dependencies
- **Google AI API Key**: Required for AI functionality
- **Domain Name**: For production deployment
- **SSL Certificate**: For HTTPS in production

## Environment Setup

### Development Environment

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/finehero-ai.git
cd finehero-ai
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
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

# AI Services
GOOGLE_API_KEY=your_google_api_key_here

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract

# RAG Configuration
VECTOR_STORE_DIR=vector_store
KNOWLEDGE_BASE_DIR=knowledge_base
```

#### 3. Install Dependencies
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Install Tesseract OCR (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por

# Install Tesseract OCR (macOS)
brew install tesseract

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### 4. Database Setup
```bash
# Run database migrations
python backend/database_migrations.py

# Initialize the database
python -c "from backend.app.models import Base; Base.metadata.create_all(bind=database.engine)"
```

#### 5. Start Development Server
```bash
# Start FastAPI server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start CLI interface
python cli/main.py --help
```

### Production Environment

#### 1. Server Setup
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.0.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Application Deployment
```bash
# Clone repository
git clone https://github.com/your-org/finehero-ai.git
cd finehero-ai

# Create production environment file
cp .env.example .env.production
nano .env.production
```

**Production Environment Variables:**
```bash
# Application
APP_NAME=FineHero AI
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/finehero_prod

# AI Services
GOOGLE_API_KEY=your_production_google_api_key

# Security
SECRET_KEY=your_production_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# SSL
SSL_CERT_PATH=/path/to/certificate.pem
SSL_KEY_PATH=/path/to/private.key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/finehero/app.log
```

#### 3. Database Setup (Production)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE finehero_prod;
CREATE USER finehero_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE finehero_prod TO finehero_user;
\q
```

#### 4. Build and Deploy
```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend python backend/database_migrations.py

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Deployment

#### 1. Development Docker Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./knowledge_base:/app/knowledge_base
      - ./vector_store:/app/vector_store
    environment:
      - DATABASE_URL=sqlite:///./finehero.db
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ENVIRONMENT=development
    depends_on:
      - tesseract

  tesseract:
    image: tesseract/tesseract:latest
    volumes:
      - ./tessdata:/usr/share/tesseract-ocr/5/tessdata

  cli:
    build: ./cli
    volumes:
      - ./backend:/app/backend
      - ./knowledge_base:/app/knowledge_base
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

#### 2. Production Docker Setup
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./knowledge_base:/app/knowledge_base
      - ./vector_store:/app/vector_store
      - ./logs:/var/log/finehero
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: finehero_prod
      POSTGRES_USER: finehero_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## Configuration Management

### Application Configuration
```python
# backend/core/config.py
class Settings(BaseSettings):
    APP_NAME: str = "FineHero AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./finehero.db"
    
    # API Security
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # External Services
    GOOGLE_API_KEY: str
    
    # OCR Configuration
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    
    # RAG Configuration
    VECTOR_STORE_DIR: str = "vector_store"
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"
    
    class Config:
        env_file = ".env"
```

### Nginx Configuration
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/certificate.pem;
        ssl_certificate_key /etc/nginx/ssl/private.key;

        # API proxy
        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }
}
```

## Monitoring and Logging

### Application Logs
```bash
# View application logs
docker-compose logs -f api

# View specific service logs
docker-compose logs -f postgres

# Export logs
docker-compose logs api > application.log
```

### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check database connectivity
docker-compose exec api python -c "from backend.database import engine; print('Database OK')"

# Check vector store
docker-compose exec api python -c "import faiss; print('FAISS OK')"
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Check disk usage
df -h

# Monitor database connections
docker-compose exec postgres psql -U finehero_user -d finehero_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

## Backup and Recovery

### Database Backup
```bash
# Automated daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup
docker-compose exec postgres pg_dump -U finehero_user finehero_prod > "$BACKUP_DIR/finehero_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/finehero_$DATE.sql"

# Remove backups older than 30 days
find $BACKUP_DIR -name "finehero_*.sql.gz" -mtime +30 -delete
```

### Vector Store Backup
```bash
# Backup vector store
tar -czf vector_store_backup_$(date +%Y%m%d).tar.gz vector_store/

# Restore vector store
tar -xzf vector_store_backup_20251111.tar.gz
```

### Knowledge Base Backup
```bash
# Backup knowledge base
rsync -avz knowledge_base/ /backups/knowledge_base_$(date +%Y%m%d)/
```

## Security Considerations

### SSL/TLS Configuration
- Use strong SSL certificates (Let's Encrypt recommended)
- Configure HTTPS redirects
- Enable HSTS headers
- Use modern cipher suites

### Access Control
```nginx
# Restrict access to admin endpoints
location /admin {
    allow 192.168.1.0/24;
    deny all;
}
```

### Environment Variables Security
- Use strong, unique secrets for production
- Store secrets in secure secret management systems
- Rotate API keys and passwords regularly
- Use environment-specific configurations

### Network Security
```bash
# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## Troubleshooting

### Common Issues

#### 1. OCR Service Not Working
**Symptoms:** PDF processing fails with OCR errors  
**Solution:**
```bash
# Check Tesseract installation
docker-compose exec api tesseract --version

# Install missing language models
docker-compose exec api tesseract --list-langs

# Reinstall Tesseract
docker-compose build --no-cache
```

#### 2. Database Connection Issues
**Symptoms:** API returns 500 errors, database connection refused  
**Solution:**
```bash
# Check database status
docker-compose exec postgres pg_isready

# Check logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Vector Store Issues
**Symptoms:** RAG queries return no results  
**Solution:**
```bash
# Check vector store files
ls -la vector_store/

# Rebuild vector store
python rag/ingest.py

# Check permissions
chmod -R 755 vector_store/
```

### Performance Issues
- Monitor resource usage with `docker stats`
- Check slow query logs in PostgreSQL
- Optimize database queries
- Scale horizontally if needed

### Backup Recovery
```bash
# Restore database
gunzip -c /backups/finehero_20251111.sql.gz | docker-compose exec -T postgres psql -U finehero_user finehero_prod

# Restore vector store
tar -xzf vector_store_backup_20251111.tar.gz --strip-components=1
```

## Rollback Procedures

### Application Rollback
```bash
# Rollback to previous version
git checkout <previous-commit-tag>
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Rollback database
docker-compose exec postgres psql -U finehero_user finehero_prod < /backups/pre_migration_backup.sql
```

### Database Rollback
```sql
-- Rollback migration
DROP TABLE IF EXISTS new_table;
```

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Review Frequency:** Quarterly  
**Owner:** DevOps Team