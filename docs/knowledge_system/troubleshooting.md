# FineHero Knowledge System - Troubleshooting

## Common Issues and Solutions

### 1. Java Execution Errors

**Problem**: "java is not recognized as an internal or external command"

**Solutions**:
1. Install Java Runtime Environment (JRE)
2. Add Java to system PATH
3. Use Python-only scraping (automatic fallback)

**Configuration**:
```json
{
  "java_path": "/path/to/java/bin/java"
}
```

### 2. Legal Source Access Errors

**Problem**: "403 Forbidden" or "Connection failed"

**Solutions**:
1. Use VPN with Portuguese IP
2. Download manually using guide
3. Use alternative sources

**Status Check**:
```bash
python -c "from backend.services.enhanced_portuguese_scraper import EnhancedPortugueseScraper; scraper = EnhancedPortugueseScraper(); print(scraper.run_comprehensive_scan())"
```

### 3. Knowledge Base Quality Issues

**Problem**: Low-quality or inconsistent entries

**Solutions**:
1. Run quality check: `python scripts/quality_check.py`
2. Remove low-scoring entries manually
3. Add more high-quality sources

**Manual Quality Check**:
```python
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
integrator = KnowledgeBaseIntegrator()
report = integrator.generate_knowledge_report()
print(f"Average quality: {report['quality_metrics']['average_quality_score']}")
```

### 4. RAG Integration Issues

**Problem**: Defense generator not using knowledge base

**Solutions**:
1. Rebuild knowledge base: `python scripts/daily_update.py`
2. Check vector store exists: `ls vector_store/`
3. Verify RAG retriever configuration

**Test RAG**:
```python
from rag.retriever import RAGRetriever
retriever = RAGRetriever()
docs = retriever.retrieve("estacionamento lisboa", k=3)
print(f"Retrieved {len(docs)} documents")
```

### 5. User Contributions Not Appearing

**Problem**: Submitted fine examples not in knowledge base

**Solutions**:
1. Check UserContributionsCollector logs
2. Verify submission validation passed
3. Rebuild integrated knowledge base

**Debug User Contributions**:
```python
from knowledge_base.user_contributions_collector import UserContributionsCollector
collector = UserContributionsCollector()
stats = collector.get_community_statistics()
print(f"Total contributions: {stats}")
```

## Advanced Troubleshooting

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Requirements
```bash
python -c "import sys; print('Python version:', sys.version); import requests; print('Requests available'); from selenium import webdriver; print('Selenium available')"
```

### Manual Knowledge Base Rebuild
```python
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
integrator = KnowledgeBaseIntegrator()
result = integrator.build_complete_knowledge_base()
print(f"Rebuilt with {result['report']['total_entries']} entries")
```

## Getting Help

1. Check logs in `logs/` directory
2. Run diagnostic script: `python finehero_knowledge_system_setup.py --scan-only`
3. Review system status: `python scripts/quality_check.py`
