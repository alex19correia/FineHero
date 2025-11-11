# FineHero Phase 3: Production Deployment Guide

## Overview

FineHero Phase 3 transforms the system from prototype to enterprise-grade production deployment. This guide covers the complete setup and deployment process for PostgreSQL database integration, Redis caching, performance monitoring, and production infrastructure.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Redis Configuration](#redis-configuration)
7. [Deployment Process](#deployment-process)
8. [Performance Monitoring](#performance-monitoring)
9. [Health Checks](#health-checks)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

FineHero Phase 3 implements a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Redis Cache   │    │ PostgreSQL DB   │
│   (Future)      │    │   Cluster       │    │   + PostGIS     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │ Performance     │    │   Monitoring    │
│   (Main API)    │    │   Monitor       │    │   & Alerts      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **Database**: PostgreSQL with PostGIS for spatial data
- **Caching**: Redis for high-performance data caching
- **Monitoring**: Built-in performance monitoring and health checks
- **Configuration**: Environment-based configuration management

## Prerequisites

### System Requirements

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- 2GB RAM minimum, 4GB+ recommended
- 10GB+ disk space

### Required Software

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib postgresql-13-postgis-3

# Install Redis
sudo apt-get install redis-server

# Install Python dependencies
pip install -r backend/requirements-production.txt
```

### External Services (Optional)

- Google AI API key for enhanced features
- Cloud Redis service (Redis Cloud, AWS ElastiCache)
- Cloud PostgreSQL (AWS RDS, Google Cloud SQL)

## Installation & Setup

### 1. Clone and Setup Project

```bash
git clone <repository-url>
cd multas-ai

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
cd backend
pip install -r requirements-production.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb finehero_prod

# Create user and set permissions
sudo -u postgres psql
```

```sql
CREATE USER finehero_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE finehero_prod TO finehero_user;
\q
```

## Configuration

### Database Configuration (.env)

```bash
# Database Settings
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finehero_prod
POSTGRES_USER=finehero_user
POSTGRES_PASSWORD=your-secure-password

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### Redis Configuration (.env)

```bash
# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Leave empty for local development
REDIS_DB=0

# Cache Settings
CACHE_DEFAULT_TTL=3600
DOCUMENT_CACHE_TTL=7200
FINES_CACHE_TTL=1800
```

### Performance Monitoring

```bash
# Monitoring Settings
MONITORING_ENABLED=true
SLOW_QUERY_THRESHOLD=2.0
HEALTH_CHECK_INTERVAL=30
```

## Database Setup

### 1. Initialize Database Schema

```bash
# Run database initialization
python -c "
from app.models import Base
from database_enhanced import engine
Base.metadata.create_all(bind=engine)
print('Database schema created successfully')
"
```

### 2. Enable PostGIS Extension (if needed)

```bash
# Connect to PostgreSQL and enable PostGIS
psql -U finehero_user -d finehero_prod -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 3. Test Database Connection

```bash
# Test database connectivity
python -c "
from database_enhanced import db_config
print('Database connection test:', db_config.test_connection())
print('Database info:', db_config.get_database_info())
"
```

## Redis Configuration

### 1. Start Redis Server

```bash
# Start Redis (Ubuntu/Debian)
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Check Redis status
redis-cli ping
# Should return: PONG
```

### 2. Test Redis Connection

```bash
# Test Redis connectivity
python -c "
from services.redis_cache import cache
print('Redis connection test:', cache.is_connected())
print('Redis stats:', cache.get_stats())
"
```

## Deployment Process

### 1. Automated Deployment

```bash
# Run complete deployment
python deploy.py

# Development deployment
python deploy.py --dev

# Skip specific steps
python deploy.py --skip-deps --skip-db
```

### 2. Manual Deployment Steps

```bash
# 1. Install dependencies
pip install -r requirements-production.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your values

# 3. Setup database
python -c "from app.models import Base; from database import engine; Base.metadata.create_all(bind=engine)"

# 4. Test connections
python -c "from database_enhanced import db_config; print('DB:', db_config.test_connection())"
python -c "from services.redis_cache import cache; print('Redis:', cache.is_connected())"

# 5. Run health check
python -c "from services.performance_monitoring import quick_health_check; print(quick_health_check())"
```

### 3. Start Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Performance Monitoring

### 1. Built-in Monitoring

The system includes comprehensive performance monitoring:

```python
# Check performance summary
from services.performance_monitoring import performance_monitor

summary = performance_monitor.get_performance_summary()
print(f"Average response time: {summary['response_time_stats']['avg']:.3f}s")
print(f"95th percentile: {summary['response_time_stats']['p95']:.3f}s")
```

### 2. Health Checks

```python
# Comprehensive health check
from services.performance_monitoring import health_checker

health = health_checker.check_all()
print(f"System status: {health.status}")
print(f"CPU: {health.cpu_percent}%")
print(f"Memory: {health.memory_percent}%")
```

### 3. API Endpoints for Monitoring

Add these endpoints to your FastAPI application:

```python
from fastapi import APIRouter
from services.performance_monitoring import quick_health_check, performance_monitor, health_checker

router = APIRouter()

@router.get("/health")
async def health_endpoint():
    """Quick health check endpoint."""
    return quick_health_check()

@router.get("/metrics")
async def metrics_endpoint():
    """Performance metrics endpoint."""
    return performance_monitor.get_performance_summary()

@router.get("/health/detailed")
async def detailed_health_endpoint():
    """Detailed health check endpoint."""
    return health_checker.check_all()
```

## Health Checks

### 1. Database Health Check

```python
from database_enhanced import health_check as db_health_check

health = db_health_check()
print(f"Database status: {health['status']}")
```

### 2. Cache Health Check

```python
from services.redis_cache import cache

if cache.is_connected():
    stats = cache.get_stats()
    print(f"Cache hit rate: {stats['hit_rate']}%")
else:
    print("Cache connection failed")
```

### 3. System Health Check

```bash
# Manual health check
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8000/health/detailed
```

## Performance Optimization

### 1. Database Optimization

The system automatically applies PostgreSQL optimizations:

- Connection pooling
- Query optimization settings
- Index suggestions
- Performance monitoring

### 2. Caching Strategy

Implemented caching levels:

- **Legal Documents**: 2-hour TTL
- **Fines Data**: 30-minute TTL
- **Search Results**: 1-hour TTL
- **API Responses**: Configurable TTL

### 3. Monitoring Thresholds

- Slow queries: > 2.0 seconds
- Memory usage: > 85%
- CPU usage: > 80%
- Disk usage: > 90%

## Scaling Configuration

### Horizontal Scaling

For high-traffic deployments:

```bash
# Multiple application instances
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8

# Load balancer configuration
# Configure nginx or cloud load balancer
```

### Database Scaling

```bash
# Read replicas
POSTGRES_REPLICA_HOSTS=replica1,replica2

# Connection pool tuning
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

### Redis Clustering

For high availability:

```bash
# Redis Cluster configuration
REDIS_URL=redis://user:pass@host1:6379,host2:6379/0
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection string
python -c "from database_enhanced import db_config; print(db_config.connection_string)"

# Test manual connection
psql -h localhost -U finehero_user -d finehero_prod
```

#### 2. Redis Connection Failed

```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis manually
redis-cli ping

# Check Redis logs
sudo journalctl -u redis-server
```

#### 3. Performance Issues

```bash
# Check system resources
top
htop
df -h

# Check application logs
tail -f app.log

# Monitor slow queries
python -c "from infrastructure.postgresql_replicas import query_optimizer; print(query_optimizer.analyze_slow_queries())"
```

### Log Analysis

```bash
# Application logs
tail -f logs/app.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

## Security Considerations

### 1. Environment Security

```bash
# Set proper file permissions
chmod 600 .env

# Use strong passwords
# Generate secure keys: openssl rand -hex 32
```

### 2. Database Security

```sql
-- Create dedicated database user
CREATE USER app_user WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE app_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

### 3. Network Security

```bash
# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
sudo ufw allow 8000/tcp  # Application
sudo ufw enable
```

## Monitoring & Alerting

### 1. Built-in Alerts

The system automatically alerts on:

- Database connection failures
- High resource usage (>80%)
- Slow query performance (>2s)
- Cache connection issues

### 2. External Monitoring

Integrate with monitoring services:

```python
# Prometheus metrics (if enabled)
from prometheus_client import Counter, Histogram, generate_latest

# Custom metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')
```

## Backup & Recovery

### 1. Database Backup

```bash
# Automated backup script
#!/bin/bash
pg_dump -h localhost -U finehero_user finehero_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -h localhost -U finehero_user finehero_prod < backup_file.sql
```

### 2. Configuration Backup

```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

## Production Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database created and accessible
- [ ] Redis server running
- [ ] Dependencies installed
- [ ] SSL certificates configured
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

### Post-Deployment

- [ ] Health checks passing
- [ ] Performance metrics within limits
- [ ] Database connections stable
- [ ] Caching working correctly
- [ ] Monitoring alerts configured
- [ ] Backup verification
- [ ] Load testing completed

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check performance metrics
2. **Monthly**: Review database optimization
3. **Quarterly**: Update dependencies
4. **Annually**: Security audit

### Performance Tuning

```bash
# Database optimization
python -c "from infrastructure.postgresql_replicas import query_optimizer; print(query_optimizer.get_comprehensive_optimization_report())"

# Cache analysis
python -c "from services.redis_cache import FineHeroCache; print(FineHeroCache.get_cache_status())"
```

## Conclusion

This deployment guide provides a complete production-ready setup for FineHero Phase 3. The system includes:

✅ **PostgreSQL Integration**: Enterprise-grade database with connection pooling
✅ **Redis Caching**: High-performance caching layer
✅ **Performance Monitoring**: Real-time metrics and alerting
✅ **Health Checks**: Comprehensive system health monitoring
✅ **Deployment Automation**: Simplified deployment process

The implementation successfully transforms FineHero from prototype to enterprise-grade deployment, supporting thousands of concurrent users and massive legal document processing as specified in the Phase 3 requirements.