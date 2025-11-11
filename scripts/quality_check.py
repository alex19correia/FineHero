#!/usr/bin/env python3
"""
FineHero Knowledge Base Quality Check
=====================================

Validates the quality of knowledge base content and provides comprehensive
quality metrics and recommendations for improvement.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
from knowledge_base.user_contributions_collector import UserContributionsCollector

def check_knowledge_base_quality() -> Dict:
    """Comprehensive quality check of the knowledge base"""
    print("🔍 FINEHERO KNOWLEDGE BASE QUALITY CHECK")
    print("=" * 60)
    
    quality_report = {
        'timestamp': datetime.now().isoformat(),
        'overall_score': 0.0,
        'checks': {},
        'recommendations': [],
        'metrics': {}
    }
    
    # Check 1: Knowledge Base Coverage
    print("\\n📚 1. KNOWLEDGE BASE COVERAGE CHECK")
    try:
        integrator = KnowledgeBaseIntegrator()
        kb_report = integrator.generate_knowledge_report()
        
        total_entries = kb_report.get('total_entries', 0)
        entry_types = kb_report.get('entry_types', {})
        
        quality_report['checks']['coverage'] = {
            'status': 'PASS' if total_entries >= 50 else 'NEEDS_IMPROVEMENT',
            'total_entries': total_entries,
            'entry_types': entry_types,
            'score': min(1.0, total_entries / 100)  # Score based on target of 100 entries
        }
        
        print(f"   Total entries: {total_entries}")
        print(f"   Entry types: {entry_types}")
        print(f"   Coverage score: {quality_report['checks']['coverage']['score']:.2f}")
        
        if total_entries < 50:
            quality_report['recommendations'].append(f"Add more content - currently only {total_entries} entries (target: 50+)")
        
    except Exception as e:
        print(f"   ❌ Coverage check failed: {e}")
        quality_report['checks']['coverage'] = {'status': 'FAILED', 'error': str(e)}
    
    # Check 2: User Contributions Quality
    print("\\n👥 2. USER CONTRIBUTIONS QUALITY CHECK")
    try:
        collector = UserContributionsCollector()
        stats = collector.get_community_statistics()
        
        fine_examples = stats.get('total_fine_examples', 0)
        contest_examples = stats.get('total_contest_examples', 0)
        success_rate = stats.get('contest_success_rate', 0)
        
        quality_report['checks']['user_contributions'] = {
            'status': 'PASS' if fine_examples >= 10 and contest_examples >= 5 else 'NEEDS_IMPROVEMENT',
            'fine_examples': fine_examples,
            'contest_examples': contest_examples,
            'success_rate': success_rate,
            'score': min(1.0, (fine_examples + contest_examples) / 50)  # Score based on 50 total examples
        }
        
        print(f"   Fine examples: {fine_examples}")
        print(f"   Contest examples: {contest_examples}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Contributions score: {quality_report['checks']['user_contributions']['score']:.2f}")
        
        if fine_examples < 10:
            quality_report['recommendations'].append(f"Add more fine examples - currently only {fine_examples} (target: 10+)")
        if contest_examples < 5:
            quality_report['recommendations'].append(f"Add more contest examples - currently only {contest_examples} (target: 5+)")
        
    except Exception as e:
        print(f"   ❌ User contributions check failed: {e}")
        quality_report['checks']['user_contributions'] = {'status': 'FAILED', 'error': str(e)}
    
    # Check 3: Legal Article Quality
    print("\\n⚖️  3. LEGAL ARTICLE QUALITY CHECK")
    legal_articles_dir = project_root / "knowledge_base" / "legal_articles"
    
    if legal_articles_dir.exists():
        article_files = list(legal_articles_dir.glob("*.txt"))
        total_articles = len(article_files)
        
        # Analyze article quality
        high_quality_articles = 0
        content_lengths = []
        
        for article_file in article_files:
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content_lengths.append(len(content))
                    
                    # Check if article has proper structure
                    if len(content) > 500 and 'artigo' in content.lower() or 'lei' in content.lower():
                        high_quality_articles += 1
                        
            except Exception as e:
                print(f"   ⚠️  Error reading article {article_file}: {e}")
        
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        quality_report['checks']['legal_articles'] = {
            'status': 'PASS' if high_quality_articles >= 10 else 'NEEDS_IMPROVEMENT',
            'total_articles': total_articles,
            'high_quality_articles': high_quality_articles,
            'avg_content_length': avg_content_length,
            'score': min(1.0, high_quality_articles / 20)  # Score based on 20 high-quality articles
        }
        
        print(f"   Total articles: {total_articles}")
        print(f"   High-quality articles: {high_quality_articles}")
        print(f"   Average content length: {avg_content_length:.0f} characters")
        print(f"   Legal articles score: {quality_report['checks']['legal_articles']['score']:.2f}")
        
        if high_quality_articles < 10:
            quality_report['recommendations'].append(f"Improve legal article quality - only {high_quality_articles} high-quality articles (target: 10+)")
        
    else:
        print("   ❌ Legal articles directory not found")
        quality_report['checks']['legal_articles'] = {'status': 'FAILED', 'error': 'Directory not found'}
    
    # Check 4: Unified Knowledge Base Integrity
    print("\\n🔗 4. UNIFIED KNOWLEDGE BASE INTEGRITY CHECK")
    unified_kb_path = project_root / "knowledge_base" / "unified_knowledge_base.json"
    
    if unified_kb_path.exists():
        try:
            with open(unified_kb_path, 'r', encoding='utf-8') as f:
                unified_kb = json.load(f)
            
            # Check structure
            required_fields = ['content', 'source_type', 'quality_score', 'tags']
            valid_entries = 0
            total_entries = len(unified_kb)
            
            for entry_id, entry in unified_kb.items():
                if all(field in entry for field in required_fields):
                    valid_entries += 1
            
            integrity_score = valid_entries / total_entries if total_entries > 0 else 0
            
            quality_report['checks']['unified_integrity'] = {
                'status': 'PASS' if integrity_score >= 0.8 else 'NEEDS_IMPROVEMENT',
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'integrity_score': integrity_score,
                'score': integrity_score
            }
            
            print(f"   Total entries: {total_entries}")
            print(f"   Valid entries: {valid_entries}")
            print(f"   Integrity score: {integrity_score:.2f}")
            print(f"   Unified KB score: {quality_report['checks']['unified_integrity']['score']:.2f}")
            
            if integrity_score < 0.8:
                quality_report['recommendations'].append(f"Fix unified knowledge base structure - only {integrity_score:.1%} entries are valid")
                
        except Exception as e:
            print(f"   ❌ Unified KB check failed: {e}")
            quality_report['checks']['unified_integrity'] = {'status': 'FAILED', 'error': str(e)}
    else:
        print("   ❌ Unified knowledge base file not found")
        quality_report['checks']['unified_integrity'] = {'status': 'FAILED', 'error': 'File not found'}
    
    # Calculate overall quality score
    check_scores = [check.get('score', 0) for check in quality_report['checks'].values() if isinstance(check.get('score'), (int, float))]
    overall_score = sum(check_scores) / len(check_scores) if check_scores else 0
    quality_report['overall_score'] = overall_score
    
    # Overall assessment
    print("\\n" + "=" * 60)
    print("📊 OVERALL QUALITY ASSESSMENT")
    print("=" * 60)
    print(f"Overall Quality Score: {overall_score:.2f} / 1.00")
    
    if overall_score >= 0.8:
        print("🟢 STATUS: EXCELLENT - Knowledge base is high quality")
        quality_report['overall_status'] = 'EXCELLENT'
    elif overall_score >= 0.6:
        print("🟡 STATUS: GOOD - Knowledge base has room for improvement")
        quality_report['overall_status'] = 'GOOD'
    elif overall_score >= 0.4:
        print("🟠 STATUS: NEEDS IMPROVEMENT - Significant issues identified")
        quality_report['overall_status'] = 'NEEDS_IMPROVEMENT'
    else:
        print("🔴 STATUS: POOR - Major issues require immediate attention")
        quality_report['overall_status'] = 'POOR'
    
    # Recommendations
    if quality_report['recommendations']:
        print("\\n💡 RECOMMENDATIONS FOR IMPROVEMENT")
        print("-" * 40)
        for i, rec in enumerate(quality_report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # Quality metrics summary
    quality_report['metrics'] = {
        'total_knowledge_entries': quality_report['checks'].get('coverage', {}).get('total_entries', 0),
        'user_contributions': quality_report['checks'].get('user_contributions', {}).get('fine_examples', 0) + quality_report['checks'].get('user_contributions', {}).get('contest_examples', 0),
        'legal_articles': quality_report['checks'].get('legal_articles', {}).get('total_articles', 0),
        'quality_improvement_needed': len(quality_report['recommendations'])
    }
    
    print(f"\\n📈 QUALITY METRICS SUMMARY")
    print("-" * 30)
    print(f"Knowledge entries: {quality_report['metrics']['total_knowledge_entries']}")
    print(f"User contributions: {quality_report['metrics']['user_contributions']}")
    print(f"Legal articles: {quality_report['metrics']['legal_articles']}")
    print(f"Improvements needed: {quality_report['metrics']['quality_improvement_needed']}")
    
    return quality_report

def save_quality_report(quality_report: Dict):
    """Save quality report to file"""
    reports_dir = project_root / "01_Fontes_Oficiais" / "Access_Logs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f"quality_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(quality_report, f, ensure_ascii=False, indent=2)
    
    print(f"\\n💾 Quality report saved to: {report_file}")

if __name__ == "__main__":
    print(f"Starting knowledge base quality check: {datetime.now()}")
    
    quality_report = check_knowledge_base_quality()
    save_quality_report(quality_report)
    
    print(f"\\n🏁 Quality check completed: {datetime.now()}")
    
    # Return exit code based on quality
    if quality_report['overall_score'] >= 0.6:
        exit(0)  # Success
    else:
        exit(1)  # Needs improvement
