"""
FineHero Knowledge System - Complete Solution
=============================================

This document addresses the issues with GEMINI CLI's inability to access Portuguese
legal sources and provides a comprehensive solution for building a robust knowledge base
that combines official legal documents with user-contributed content.

## Problems Addressed

### 1. Java Execution Issues
**Problem**: GEMINI CLI couldn't execute Java for complex web scraping tasks

**Solution**: Created multi-layered fallback system in `enhanced_portuguese_scraper.py`:
- Python-only scraping alternatives
- Automatic Java detection and configuration
- VPN/Proxy support for restricted sites
- Manual download workflows for blocked sources

### 2. Incomplete Knowledge Base
**Problem**: Need official legal documents + user-contributed fine examples + contest strategies

**Solution**: Built integrated system:
- `user_contributions_collector.py` - Collects real fine examples from users
- `knowledge_base_integrator.py` - Combines official + user sources
- `finehero_knowledge_system_setup.py` - Master setup and maintenance

## System Architecture

### Official Legal Sources (High Authority)
```
01_Fontes_Oficiais/
├── Diario_da_Republica/     # Código da Estrada, Decreto-Lei 81/2006
├── Lisboa_Municipal/        # Lisbon parking regulations  
├── Porto_Municipal/         # Porto parking regulations
└── Access_Logs/             # Download tracking
```

### User Contributions System (Medium Authority)
```
knowledge_base/
├── user_contributions_collector.py    # Collect user fine examples
├── legal_articles/                    # Official legal articles
├── unified_knowledge_base.json        # Combined database
└── scraped/                          # Downloaded documents
```

### Community-Verified Content (High Utility)
- Successful contest strategies
- Defense examples and templates
- Procedural guidance
- Quality-validated user contributions

## How Java Issues Are Resolved

### 1. Automatic Java Detection
The system automatically detects Java availability and configures alternatives:

```python
def check_java_availability(self) -> bool:
    # Try multiple Java commands
    for java_cmd in ['java', 'java.exe', '/usr/bin/java']:
        try:
            result = subprocess.run([java_cmd, '-version'], ...)
            if result.returncode == 0:
                return True  # Java found and working
        except:
            continue
    return False  # No Java found - use Python alternatives
```

### 2. Fallback Mechanisms
When Java is unavailable, the system uses:
- **Python-only web scraping** with requests/BeautifulSoup
- **Selenium webdriver** (if available) 
- **Direct HTTP requests** for simple pages
- **Manual download workflows** for restricted sites

### 3. VPN/Proxy Support
For sites requiring Portuguese IP (IMT, ANSR):

```python
def enable_vpn_access(self, vpn_service: str) -> bool:
    # Configure VPN for Portuguese IP access
    vpn_configs = {
        'nordvpn': {'proxy_url': 'socks5://127.0.0.1:1080'},
        'expressvpn': {'proxy_url': 'http://127.0.0.1:1080'}
    }
    # Enable VPN and test access
```

## Knowledge Base Integration Strategy

### 1. Official Legal Sources
- **High Authority** (Quality Score: 0.9-1.0)
- Código da Estrada articles
- Federal and municipal regulations
- Court decisions and legal precedents

### 2. User-Contributed Examples
- **Medium Authority** (Quality Score: 0.6-0.8)  
- Real fine examples with location, amount, outcome
- Contest strategies that worked
- Community feedback and validation

### 3. Community-Verified Content
- **High Utility** (Quality Score: 0.7-0.9)
- Success-tested defense strategies
- Procedural guidance
- Quality-validated user contributions

## Complete Setup Process

### Step 1: Initial Setup
```bash
python finehero_knowledge_system_setup.py --full-setup
```

This command:
1. Diagnoses Java issues and provides solutions
2. Scans Portuguese legal sources with fallback mechanisms
3. Downloads accessible documents automatically
4. Creates manual download guides for restricted sources
5. Sets up user contributions collection
6. Integrates all sources into unified knowledge base
7. Creates maintenance scripts and documentation

### Step 2: Daily Maintenance
```bash
python scripts/daily_update.py
```

Updates:
- Fresh legal document downloads
- New user contributions
- Knowledge base quality metrics
- Community feedback processing

### Step 3: Quality Monitoring
```bash
python scripts/quality_check.py
```

Validates:
- Entry quality scores
- Source authority levels  
- Knowledge base completeness
- Search effectiveness

## User Contributions Collection

### Real Fine Examples
The system collects authentic fine data from users:

```python
sample_fine = {
    'fine_type': 'estacionamento',
    'location': 'Rua Augusta, Lisboa',
    'amount': 60.0,
    'authority': 'Câmara Municipal de Lisboa',
    'contest_outcome': 'successful',
    'defense_strategy': 'Ilegibilidade da sinalização'
}
```

### Contest Case Studies
Documents successful contest strategies:

```python
contest_case = {
    'fine_reference': 'fine_001',
    'outcome': 'approved', 
    'defense_strategy': 'Sinalização confusa',
    'supporting_law': 'Artigo 48º do Código da Estrada',
    'success_factors': ['Visibilidade reduzida', 'Sinalização inadequada']
}
```

### Community Validation
User-contributed content is validated through:
- **Automated quality scoring** based on completeness and accuracy
- **Community feedback** and rating system
- **Expert review** for high-value contributions
- **Outcome tracking** to measure success rates

## Integration with Defense Generator

### Enhanced Context Generation
The knowledge base integrates with the existing defense system:

```python
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator

# Get comprehensive defense context
integrator = KnowledgeBaseIntegrator()
context = integrator.get_defense_context(
    fine_type="estacionamento",
    location="Lisboa", 
    amount=60.0
)

# Context includes:
# - Relevant legal articles
# - Similar fine examples
# - Successful contest strategies
# - Legal references
# - Community tips
```

### RAG Integration
The unified knowledge base feeds into the existing RAG system:

```python
# Existing RAG retriever now has access to:
# - Official legal sources
# - User-contributed examples  
# - Community-verified strategies
# - Real case studies with outcomes

retriever = RAGRetriever()
docs = retriever.retrieve("estacionamento lisboa contestação")
# Returns: Legal articles + Real examples + Success strategies
```

## What Makes This Better Than Before

### 1. Handles Access Restrictions
- **Before**: Failed completely on IMT/ANSR sites
- **Now**: Multiple fallback methods, VPN support, manual workflows

### 2. Java Independence  
- **Before**: Required Java for complex scraping
- **Now**: Automatic Java detection, Python alternatives, graceful degradation

### 3. Rich Knowledge Base
- **Before**: Only official legal text
- **Now**: Official + User examples + Community strategies + Real outcomes

### 4. Quality Assurance
- **Before**: No quality control on scraped content
- **Now**: Automated quality scoring, community validation, expert review

### 5. Continuous Learning
- **Before**: Static knowledge base
- **Now**: Dynamic updates, user feedback integration, success tracking

## File Structure Overview

```
project_root/
├── finehero_knowledge_system_setup.py     # Master setup script
├── knowledge_base/
│   ├── user_contributions_collector.py    # User data collection
│   ├── knowledge_base_integrator.py       # Source integration
│   ├── legal_articles/                    # Official legal docs
│   └── unified_knowledge_base.json        # Combined database
├── backend/services/
│   ├── enhanced_portuguese_scraper.py     # Advanced scraping
│   └── defense_generator.py               # Enhanced with context
├── scripts/
│   ├── daily_update.py                    # Maintenance automation
│   └── quality_check.py                   # Quality monitoring
├── 01_Fontes_Oficiais/                    # Downloaded legal sources
│   ├── manual_downloads.md               # Guide for restricted sites
│   └── scan_report.json                  # Latest accessibility report
└── docs/knowledge_system/                 # Complete documentation
    ├── README.md                         # User guide
    └── troubleshooting.md                # Problem resolution
```

## Running the Complete Solution

### Option 1: Full Setup (Recommended)
```bash
python finehero_knowledge_system_setup.py --full-setup
```

### Option 2: Component-by-Component
```bash
# 1. Check Java and accessibility
python finehero_knowledge_system_setup.py --java-check

# 2. Scan legal sources  
python finehero_knowledge_system_setup.py --scan-only

# 3. Build knowledge base only
python finehero_knowledge_system_setup.py --build-only
```

### Option 3: Manual Verification
```bash
# Verify downloads
python verify_manual_downloads.py

# Test knowledge integration
python knowledge_base/knowledge_base_integrator.py

# Check user contributions
python knowledge_base/user_contributions_collector.py
```

## Success Metrics

After running the setup, you should see:
- **Legal sources accessible**: 4-6 out of 6 Portuguese sources
- **Knowledge base entries**: 100+ combined entries
- **Quality scores**: Average >0.7 for all entry types
- **User examples**: Real fine cases with contest outcomes
- **Success strategies**: Proven defense approaches
- **Maintenance ready**: Daily update and quality check scripts

## Troubleshooting Common Issues

### Java Still Not Working
```bash
# System will automatically use Python alternatives
# Check fallback mechanism status
python finehero_knowledge_system_setup.py --java-check
```

### Sources Still Blocked
```bash
# Generate manual download guide
python backend/services/enhanced_portuguese_scraper.py
# Check 01_Fontes_Oficiais/manual_downloads.md for manual steps
```

### Low Quality Scores
```bash
# Run quality check and cleanup
python scripts/quality_check.py
python scripts/daily_update.py  # Rebuild with better sources
```

## Integration with Existing Code

The new system integrates seamlessly with existing components:

### Defense Generator Enhancement
```python
# OLD: Basic defense generation
defense = DefenseGenerator(fine_data).generate()

# NEW: Context-enhanced defense generation  
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
integrator = KnowledgeBaseIntegrator()
context = integrator.get_defense_context(
    fine_data.infraction_code, 
    fine_data.location, 
    fine_data.fine_amount
)
defense = DefenseGenerator(fine_data).generate_with_context(context)
```

### RAG System Enhancement  
```python
# OLD: Basic legal document retrieval
docs = retriever.retrieve("estacionamento lisboa")

# NEW: Unified knowledge base retrieval
docs = retriever.retrieve("estacionamento lisboa contestação")
# Returns: Legal articles + Real examples + Success strategies
```

This comprehensive solution addresses both the technical execution issues and the knowledge base completeness requirements, creating a robust system for Portuguese traffic fine defense generation that combines official legal authority with real-world user experience and community wisdom.