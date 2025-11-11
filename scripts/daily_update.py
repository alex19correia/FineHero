#!/usr/bin/env python3
"""
FineHero Daily Knowledge Update
===============================

Updates knowledge base with fresh data and processes new user contributions.
Run this daily to keep the knowledge base current.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.services.enhanced_portuguese_scraper import EnhancedPortugueseScraper
from knowledge_base.knowledge_base_integrator import KnowledgeBaseIntegrator
from knowledge_base.user_contributions_collector import UserContributionsCollector

def daily_update():
    """Run daily knowledge base update"""
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
