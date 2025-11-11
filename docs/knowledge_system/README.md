# FineHero Knowledge System

The FineHero Knowledge System combines official Portuguese legal documents with user-contributed fine examples and contest strategies to provide comprehensive defense support.

## System Components

### 1. Legal Sources Scanner
- **Purpose**: Automatically download Portuguese legal documents
- **Sources**: DRE (Diário da República), IMT, ANSR, Municipal sources
- **Features**: Fallback mechanisms, VPN support, manual download guides
- **Location**: `backend/services/enhanced_portuguese_scraper.py`

### 2. User Contributions Collector
- **Purpose**: Collect and validate user-submitted fine examples
- **Features**: Privacy protection, validation, community feedback
- **Location**: `knowledge_base/user_contributions_collector.py`

### 3. Knowledge Base Integrator
- **Purpose**: Combine all sources into unified knowledge base
- **Features**: Quality scoring, search, defense context generation
- **Location**: `knowledge_base/knowledge_base_integrator.py`

### 4. RAG Integration
- **Purpose**: Vector-based retrieval for AI defense generation
- **Location**: `rag/retriever.py`

## Quick Start

### 1. Initial Setup
```bash
python finehero_knowledge_system_setup.py --full-setup
```

### 2. Daily Maintenance
```bash
python scripts/daily_update.py
```

### 3. Quality Check
```bash
python scripts/quality_check.py
```

## Manual Document Download

Some legal sources require manual download due to access restrictions. See:
- `01_Fontes_Oficiais/manual_downloads.md`
- `verify_manual_downloads.py`

## Knowledge Base Structure

### Official Sources (High Authority)
- Código da Estrada articles
- Decreto-Lei regulations
- Municipal parking rules

### User Contributions (Medium Authority)  
- Real fine examples
- Contest case studies
- Community tips and strategies

### Community Verified (High Utility)
- Success-tested strategies
- Common defense arguments
- Procedural guidance

## Integration with Defense Generator

The knowledge base integrates with `backend/services/defense_generator.py`:

```python
# Get defense context
context = integrator.get_defense_context(
    fine_type="estacionamento",
    location="Lisboa",
    amount=60.0
)

# Use in defense generation
defense = DefenseGenerator(fine_data).generate_with_context(context)
```

## Contributing

### Adding User Contributions
Use the UserContributionsCollector to submit fine examples:

```python
from knowledge_base.user_contributions_collector import UserContributionsCollector

collector = UserContributionsCollector()
fine_id = collector.submit_fine_example({
    'fine_type': 'estacionamento',
    'location': 'Rua Augusta, Lisboa',
    'amount': 60.0,
    # ... other fields
})
```

### Adding Legal Sources
Modify the EnhancedPortugueseScraper configuration to add new sources.

## Troubleshooting

### Java Issues
If Java-based scraping fails, the system automatically falls back to Python-only solutions.

### Access Restrictions  
For blocked sources (IMT, ANSR), use the manual download guide or configure VPN access.

### Quality Issues
Run quality_check.py to identify and fix low-quality entries.

## File Structure
```
knowledge_base/
├── legal_articles/           # Official legal articles
├── user_contributions/       # User-submitted content
├── unified_knowledge_base.json  # Combined database
└── scraped/                  # Downloaded documents

scripts/
├── daily_update.py          # Daily maintenance
└── quality_check.py         # Quality validation

01_Fontes_Oficiais/
├── manual_downloads.md      # Manual download guide
├── Access_Logs/             # Download logs
└── scan_report.json         # Latest scan results
```
