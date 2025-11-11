#!/usr/bin/env python3
"""
FineHero Knowledge System Setup
===============================

Master script to set up the complete FineHero knowledge base system:
1. Diagnoses and fixes Java execution issues
2. Scrapes accessible legal sources with fallback mechanisms  
3. Integrates official documents with user-contributed content
4. Creates unified knowledge base for defense generation
5. Provides ongoing maintenance tools

Usage:
    python finehero_knowledge_system_setup.py [--scan-only] [--build-only] [--full-setup]
"""

import sys
import os
import json
import argparse
from pathlib import Path
import subprocess
import logging
from typing import Dict
from datetime import datetime

# Add project paths
sys.path.append('backend')
sys.path.append('knowledge_base')

from backend.services.enhanced_portuguese_scraper import EnhancedPortugueseScraper
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
from knowledge_base.user_contributions_collector import UserContributionsCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FineHeroKnowledgeSetup:
    """Complete setup system for FineHero knowledge base"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging file
        log_file = self.logs_dir / f"finehero_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def diagnose_java_issues(self) -> Dict:
        """Diagnose and fix Java execution issues"""
        logger.info("=== DIAGNOSING JAVA EXECUTION ISSUES ===")
        
        diagnosis = {
            'java_available': False,
            'java_version': None,
            'java_path': None,
            'issues_found': [],
            'solutions_applied': [],
            'recommendations': []
        }
        
        # Check Java availability
        java_commands = ['java', 'java.exe', '/usr/bin/java', '/usr/lib/jvm/java/bin/java']
        
        for java_cmd in java_commands:
            try:
                result = subprocess.run([java_cmd, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    diagnosis['java_available'] = True
                    diagnosis['java_version'] = result.stderr.strip()
                    diagnosis['java_path'] = java_cmd
                    logger.info(f"Java found: {java_cmd} - {result.stderr.strip()}")
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        if not diagnosis['java_available']:
            diagnosis['issues_found'].append("Java not found in PATH")
            diagnosis['recommendations'].append("Install Java Runtime Environment (JRE) or Java Development Kit (JDK)")
            diagnosis['recommendations'].append("Add Java to system PATH environment variable")
            diagnosis['recommendations'].append("Alternative: Use Python-only scraping solutions")
            
            # Try to provide alternative solutions
            logger.warning("Java not available - will use Python-only alternatives")
        
        # Check environment variables
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            logger.info(f"JAVA_HOME set to: {java_home}")
        else:
            diagnosis['issues_found'].append("JAVA_HOME environment variable not set")
            diagnosis['recommendations'].append("Set JAVA_HOME to Java installation directory")
        
        # Check PATH
        path_env = os.environ.get('PATH', '')
        java_in_path = any('java' in part.lower() for part in path_env.split(os.pathsep))
        if not java_in_path:
            diagnosis['issues_found'].append("Java not in system PATH")
            diagnosis['recommendations'].append("Add Java bin directory to PATH")
        
        return diagnosis

    def run_legal_source_scan(self) -> Dict:
        """Run comprehensive legal source scanning with fallback mechanisms"""
        logger.info("=== RUNNING LEGAL SOURCE SCAN ===")
        
        # Initialize enhanced scraper
        scraper = EnhancedPortugueseScraper()
        
        # Run comprehensive scan
        scan_results = scraper.run_comprehensive_scan()
        
        logger.info("Legal source scan completed")
        return scan_results

    def build_integrated_knowledge_base(self) -> Dict:
        """Build complete integrated knowledge base"""
        logger.info("=== BUILDING INTEGRATED KNOWLEDGE BASE ===")
        
        # Initialize integrator
        integrator = KnowledgeBaseIntegrator()
        
        # Build complete knowledge base
        kb_results = integrator.build_complete_knowledge_base()
        
        logger.info("Integrated knowledge base completed")
        return kb_results

    def setup_user_contributions_system(self) -> Dict:
        """Setup user contributions collection system"""
        logger.info("=== SETTING UP USER CONTRIBUTIONS SYSTEM ===")
        
        # Initialize user contributions collector
        collector = UserContributionsCollector()
        
        # Create sample data if none exists
        sample_submission = {
            'fine_type': 'estacionamento',
            'location': 'Praça do Comércio, Lisboa',
            'amount': 45.0,
            'date_issued': '2024-01-15',
            'authority': 'Câmara Municipal de Lisboa',
            'infraction_code': '48.1.a',
            'description': 'Estacionamento em zona de duração limitada sem ticket',
            'user_city': 'Lisboa',
            'contest_outcome': 'successful',
            'user_notes': 'Ticket expirado por apenas 5 minutos'
        }
        
        # Add sample data
        fine_id = collector.submit_fine_example(sample_submission)
        
        # Create sample contest case
        if fine_id:
            sample_contest = {
                'fine_reference': fine_id,
                'contest_type': 'administrative',
                'outcome': 'approved',
                'defense_strategy': 'Excesso mínimo de tempo - tolerância razoável',
                'outcome_factors': ['Tempo excessivo mínimo', 'Boa-fé do condutor'],
                'supporting_law': 'Artigo 48º do Código da Estrada',
                'user_feedback_score': 4.8
            }
            
            contest_id = collector.submit_contest_example(sample_contest)
        
        # Generate statistics
        stats = collector.get_community_statistics()
        
        logger.info("User contributions system setup completed")
        return {
            'fine_examples_count': len(collector.fine_examples),
            'contest_examples_count': len(collector.contest_examples),
            'statistics': stats
        }

    def create_maintenance_scripts(self):
        """Create maintenance and automation scripts"""
        logger.info("=== CREATING MAINTENANCE SCRIPTS ===")
        
        # 1. Daily update script
        daily_update_script = """#!/usr/bin/env python3
\"\"\"
FineHero Daily Knowledge Update
===============================

Updates knowledge base with fresh data and processes new user contributions.
Run this daily to keep the knowledge base current.
\"\"\"

import sys
import os
from datetime import datetime

# Add paths
sys.path.append('backend')
sys.path.append('knowledge_base')

from backend.services.enhanced_portuguese_scraper import EnhancedPortugueseScraper
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
from knowledge_base.user_contributions_collector import UserContributionsCollector

def daily_update():
    \"\"\"Run daily knowledge base update\"\"\"
    print(f"Starting daily update: {datetime.now()}")
    
    # 1. Update legal sources (if accessible)
    try:
        scraper = EnhancedPortugueseScraper()
        scan_results = scraper.run_comprehensive_scan()
        print(f"Legal sources scan: {len([r for r in scan_results['source_results'].values() if r['status'] == 'accessible'])} accessible")
    except Exception as e:
        print(f"Legal sources update failed: {e}")
    
    # 2. Process new user contributions
    try:
        collector = UserContributionsCollector()
        stats = collector.get_community_statistics()
        print(f"User contributions: {stats['total_fine_examples']} fine examples, {stats['total_contest_examples']} contest examples")
    except Exception as e:
        print(f"User contributions update failed: {e}")
    
    # 3. Rebuild knowledge base
    try:
        integrator = KnowledgeBaseIntegrator()
        result = integrator.build_complete_knowledge_base()
        print(f"Knowledge base updated: {result['report']['total_entries']} total entries")
    except Exception as e:
        print(f"Knowledge base rebuild failed: {e}")
    
    print(f"Daily update completed: {datetime.now()}")

if __name__ == "__main__":
    daily_update()
"""
        
        # 2. Knowledge base quality check script
        quality_check_script = """#!/usr/bin/env python3
\"\"\"
FineHero Knowledge Base Quality Check
=====================================

Validates the quality and completeness of the knowledge base.
\"\"\"

import sys
import json
from pathlib import Path
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator

def quality_check():
    \"\"\"Perform quality check on knowledge base\"\"\"
    print("=== KNOWLEDGE BASE QUALITY CHECK ===")
    
    integrator = KnowledgeBaseIntegrator()
    report = integrator.generate_knowledge_report()
    
    print(f"Total entries: {report['total_entries']}")
    print(f"Average quality: {report['quality_metrics']['average_quality_score']:.2f}")
    print(f"Average confidence: {report['quality_metrics']['average_confidence_level']:.2f}")
    
    print("\\nEntry distribution:")
    for entry_type, count in report['entry_types'].items():
        print(f"  {entry_type}: {count}")
    
    print("\\nSource distribution:")
    for source_type, count in report['source_types'].items():
        print(f"  {source_type}: {count}")
    
    print("\\nFine type distribution:")
    for fine_type, count in report['fine_type_distribution'].items():
        print(f"  {fine_type}: {count}")
    
    # Check for low-quality entries
    low_quality = [entry for entry in integrator.unified_entries.values() 
                   if entry.quality_score < 0.5]
    
    if low_quality:
        print(f"\\n⚠️  {len(low_quality)} entries with low quality score (<0.5)")
    else:
        print("\\n✅ All entries have acceptable quality scores")
    
    return report

if __name__ == "__main__":
    quality_check()
"""
        
        # Save scripts
        scripts_dir = self.base_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        with open(scripts_dir / "daily_update.py", 'w', encoding='utf-8') as f:
            f.write(daily_update_script)
        
        with open(scripts_dir / "quality_check.py", 'w', encoding='utf-8') as f:
            f.write(quality_check_script)
        
        # Make scripts executable (Unix-like systems)
        try:
            os.chmod(scripts_dir / "daily_update.py", 0o755)
            os.chmod(scripts_dir / "quality_check.py", 0o755)
        except:
            pass  # Windows doesn't support chmod
        
        logger.info(f"Maintenance scripts created in {scripts_dir}")
        return str(scripts_dir)

    def create_user_documentation(self):
        """Create comprehensive user documentation"""
        logger.info("=== CREATING USER DOCUMENTATION ===")
        
        docs_dir = self.base_dir / "docs" / "knowledge_system"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Main README
        readme_content = """# FineHero Knowledge System

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
"""
        
        with open(docs_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Troubleshooting guide
        troubleshooting_content = """# FineHero Knowledge System - Troubleshooting

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
"""
        
        with open(docs_dir / "troubleshooting.md", 'w', encoding='utf-8') as f:
            f.write(troubleshooting_content)
        
        logger.info(f"User documentation created in {docs_dir}")
        return str(docs_dir)

    def run_full_setup(self) -> Dict:
        """Run complete knowledge system setup"""
        logger.info("🚀 STARTING FINEHERO KNOWLEDGE SYSTEM SETUP")
        
        setup_results = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'issues_found': [],
            'recommendations': [],
            'generated_files': []
        }
        
        try:
            # Step 1: Diagnose Java issues
            java_diagnosis = self.diagnose_java_issues()
            setup_results['java_diagnosis'] = java_diagnosis
            setup_results['steps_completed'].append('java_diagnosis')
            
            if java_diagnosis['issues_found']:
                setup_results['issues_found'].extend(java_diagnosis['issues_found'])
                setup_results['recommendations'].extend(java_diagnosis['recommendations'])
            
            # Step 2: Run legal source scan
            scan_results = self.run_legal_source_scan()
            setup_results['scan_results'] = scan_results
            setup_results['steps_completed'].append('legal_source_scan')
            
            # Step 3: Setup user contributions
            contributions_setup = self.setup_user_contributions_system()
            setup_results['contributions_setup'] = contributions_setup
            setup_results['steps_completed'].append('user_contributions_setup')
            
            # Step 4: Build integrated knowledge base
            kb_results = self.build_integrated_knowledge_base()
            setup_results['kb_results'] = kb_results
            setup_results['steps_completed'].append('knowledge_base_build')
            
            # Step 5: Create maintenance scripts
            scripts_dir = self.create_maintenance_scripts()
            setup_results['generated_files'].append(f"maintenance_scripts:{scripts_dir}")
            setup_results['steps_completed'].append('maintenance_scripts')
            
            # Step 6: Create user documentation
            docs_dir = self.create_user_documentation()
            setup_results['generated_files'].append(f"documentation:{docs_dir}")
            setup_results['steps_completed'].append('user_documentation')
            
            setup_results['status'] = 'completed'
            setup_results['end_time'] = datetime.now().isoformat()
            
        except Exception as e:
            setup_results['status'] = 'failed'
            setup_results['error'] = str(e)
            setup_results['end_time'] = datetime.now().isoformat()
            logger.error(f"Setup failed: {e}")
        
        # Save setup report
        report_path = self.base_dir / "knowledge_system_setup_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(setup_results, f, ensure_ascii=False, indent=2, default=str)
        
        return setup_results

    def print_setup_summary(self, results: Dict):
        """Print setup results summary"""
        print("\\n" + "="*60)
        print("🏁 FINEHERO KNOWLEDGE SYSTEM SETUP COMPLETE")
        print("="*60)
        
        print(f"\\n📊 SETUP STATUS: {results['status'].upper()}")
        print(f"⏰ Duration: {results.get('end_time', '')}")
        
        print(f"\\n✅ COMPLETED STEPS:")
        for step in results['steps_completed']:
            print(f"  • {step.replace('_', ' ').title()}")
        
        if results.get('issues_found'):
            print(f"\\n⚠️  ISSUES FOUND:")
            for issue in results['issues_found']:
                print(f"  • {issue}")
        
        if results.get('recommendations'):
            print(f"\\n💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        # Knowledge base statistics
        if 'kb_results' in results:
            kb_stats = results['kb_results']['report']
            print(f"\\n📚 KNOWLEDGE BASE STATISTICS:")
            print(f"  • Total entries: {kb_stats['total_entries']}")
            print(f"  • Average quality: {kb_stats['quality_metrics']['average_quality_score']:.2f}")
            print(f"  • Legal articles: {kb_stats['entry_types'].get('legal_article', 0)}")
            print(f"  • User examples: {kb_stats['entry_types'].get('fine_example', 0)}")
            print(f"  • Community tips: {kb_stats['entry_types'].get('community_tip', 0)}")
        
        # Generated files
        if results.get('generated_files'):
            print(f"\\n📁 GENERATED FILES:")
            for file_info in results['generated_files']:
                file_type, path = file_info.split(':', 1)
                print(f"  • {file_type}: {path}")
        
        print(f"\\n🔧 NEXT STEPS:")
        print(f"  1. Review documentation: docs/knowledge_system/README.md")
        print(f"  2. Run daily updates: python scripts/daily_update.py")
        print(f"  3. Check quality: python scripts/quality_check.py")
        print(f"  4. Test defense generation with integrated knowledge base")
        
        if results['status'] == 'failed':
            print(f"\\n❌ Setup failed - check logs/ directory for details")
        else:
            print(f"\\n🎉 Setup completed successfully!")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='FineHero Knowledge System Setup')
    parser.add_argument('--scan-only', action='store_true', 
                       help='Only run legal source scanning')
    parser.add_argument('--build-only', action='store_true',
                       help='Only build knowledge base (skip scanning)')
    parser.add_argument('--full-setup', action='store_true',
                       help='Run complete setup (default)')
    parser.add_argument('--java-check', action='store_true',
                       help='Only check Java availability')
    
    args = parser.parse_args()
    
    setup = FineHeroKnowledgeSetup()
    
    if args.java_check:
        diagnosis = setup.diagnose_java_issues()
        print(json.dumps(diagnosis, indent=2))
        return
    
    if args.scan_only:
        results = setup.run_legal_source_scan()
        print(json.dumps(results, indent=2))
        return
    
    if args.build_only:
        results = setup.build_integrated_knowledge_base()
        print(json.dumps(results, indent=2))
        return
    
    # Full setup (default)
    results = setup.run_full_setup()
    setup.print_setup_summary(results)

if __name__ == "__main__":
    main()