# FineHero Knowledge System - User Interaction Guide

## 🎯 What You Need to Interact With

### 1. **Main Setup Script** (One-time setup)
```bash
python finehero_knowledge_system_setup.py --full-setup
```
**What it does:**
- Scans Portuguese legal sources
- Downloads accessible documents  
- Sets up user contribution system
- Creates unified knowledge base
- Generates maintenance scripts

### 2. **Manual Downloads** (If sources are restricted)
If IMT/ANSR sites are blocked, you'll need to:
- Download documents manually using the guide: `01_Fontes_Oficiais/manual_downloads.md`
- Place files in specified directories
- Run: `python verify_manual_downloads.py`

### 3. **User Contribution Interface** (Ongoing)
To add real fine examples, use:
```python
from knowledge_base.user_contributions_collector import UserContributionsCollector

collector = UserContributionsCollector()

# Add a fine example
fine_data = {
    'fine_type': 'estacionamento',
    'location': 'Rua Augusta, Lisboa',
    'amount': 60.0,
    'authority': 'Câmara Municipal de Lisboa',
    'contest_outcome': 'successful',
    'defense_strategy': 'Ilegibilidade da sinalização'
}

fine_id = collector.submit_fine_example(fine_data)
```

### 4. **Daily Maintenance** (Automated)
The system creates scripts for ongoing maintenance:
- `python scripts/daily_update.py` - Updates knowledge base
- `python scripts/quality_check.py` - Validates quality

### 5. **Integration with Existing Code** (Required)
Update your defense generator to use the enhanced knowledge base:

```python
# In backend/services/defense_generator.py
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator

def generate_enhanced_defense(self, fine_data):
    # Get comprehensive context from unified knowledge base
    integrator = KnowledgeBaseIntegrator()
    context = integrator.get_defense_context(
        fine_data.infraction_code,
        fine_data.location, 
        fine_data.fine_amount
    )
    
    # Use context in defense generation
    enhanced_prompt = self.generate_prompt_with_context(context)
    return self.request_defense(enhanced_prompt)
```

## 🔧 Configuration Files You May Need to Edit

### 1. **VPN Configuration** (Optional - for restricted sites)
Create `scraper_config.json`:
```json
{
  "vpn_config": {
    "enabled": true,
    "proxy_url": "socks5://127.0.0.1:9050",
    "country_code": "PT"
  }
}
```

### 2. **Java Path** (If you install Java later)
```json
{
  "java_path": "/path/to/your/java/bin/java"
}
```

## 📋 Step-by-Step Interaction Checklist

### Phase 1: Initial Setup
- [ ] Run: `python finehero_knowledge_system_setup.py --full-setup`
- [ ] Check scan results in `01_Fontes_Oficiais/scan_report.json`
- [ ] If sources blocked, follow `01_Fontes_Oficiais/manual_downloads.md`
- [ ] Verify downloads: `python verify_manual_downloads.py`

### Phase 2: Integration
- [ ] Update `backend/services/defense_generator.py` to use enhanced context
- [ ] Test integration with sample fine data
- [ ] Verify RAG retriever works with unified knowledge base

### Phase 3: User Contributions (Ongoing)
- [ ] Set up user interface for fine example collection
- [ ] Implement community feedback system
- [ ] Regular quality checks: `python scripts/quality_check.py`

### Phase 4: Maintenance
- [ ] Schedule daily updates: `python scripts/daily_update.py`
- [ ] Monitor knowledge base quality metrics
- [ ] Add new legal sources as they become available

## 🚀 Quick Test Commands

### Test Java Detection
```bash
python finehero_knowledge_system_setup.py --java-check
```

### Test Knowledge Base
```bash
python knowledge_base/knowledge_base_integrator.py
```

### Test User Contributions
```bash
python knowledge_base/user_contributions_collector.py
```

### Test RAG Integration
```python
from rag.retriever import RAGRetriever
retriever = RAGRetriever()
docs = retriever.retrieve("estacionamento lisboa", k=3)
print(f"Found {len(docs)} relevant documents")
```

## 🎯 What Makes This System Work

1. **Handles Java Issues**: Automatic fallback to Python-only solutions
2. **Bypasses Site Restrictions**: VPN, proxy, manual download options
3. **Combines Sources**: Official legal + user examples + community wisdom
4. **Quality Control**: Automated scoring and validation
5. **Easy Maintenance**: Automated daily updates and quality checks

## 📞 If You Need Help

1. **Check logs**: `logs/finehero_setup_*.log`
2. **Run diagnostics**: `python finehero_knowledge_system_setup.py --scan-only`
3. **Review documentation**: `docs/knowledge_system/troubleshooting.md`
4. **Check system status**: `python scripts/quality_check.py`

The system is designed to work automatically once set up, requiring minimal ongoing interaction while continuously improving the knowledge base with user contributions and community feedback.