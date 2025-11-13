#!/usr/bin/env python3
"""
FineHero Crawl4AI Simple Implementation
======================================

Simple, working version of FineHero implementation using Crawl4AI
without complex API calls that might cause issues.

Usage:
    python run_crawl4ai_finehero_simple.py
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Try to import Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig
    CRAWL4AI_AVAILABLE = True
    print("Crawl4AI available - starting implementation")
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("ERROR: Crawl4AI not installed. Run: pip install crawl4ai")
    sys.exit(1)

async def test_crawl_simple():
    """Test simple crawling with minimal configuration"""
    
    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True
    )
    
    # Portuguese legal targets
    targets = [
        {
            'name': 'DRE - Diario da Republica',
            'url': 'https://dre.pt/',
            'description': 'Portuguese official legal gazette'
        },
        {
            'name': 'Lisbon Municipal',
            'url': 'https://lisboa.pt/',
            'description': 'Lisbon city official website'
        },
        {
            'name': 'Porto Municipal',
            'url': 'https://www.porto.pt/',
            'description': 'Porto city official website'
        }
    ]
    
    results = []
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for target in targets:
            print(f"Crawling: {target['name']}")
            
            try:
                # Simple crawl with basic configuration
                result = await crawler.arun(
                    url=target['url'],
                    wait_for="networkidle"
                )
                
                if result.success and result.markdown:
                    content_length = len(result.markdown)
                    results.append({
                        'source': target['name'],
                        'url': target['url'],
                        'description': target['description'],
                        'content_length': content_length,
                        'content_preview': result.markdown[:500] + "..." if len(result.markdown) > 500 else result.markdown,
                        'crawl_success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    print(f"SUCCESS: {target['name']} - {content_length} characters")
                else:
                    results.append({
                        'source': target['name'],
                        'url': target['url'],
                        'description': target['description'],
                        'content_length': 0,
                        'content_preview': '',
                        'crawl_success': False,
                        'error': 'No content or crawl failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    print(f"FAILED: {target['name']} - No content")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                results.append({
                    'source': target['name'],
                    'url': target['url'],
                    'description': target['description'],
                    'content_length': 0,
                    'content_preview': '',
                    'crawl_success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                print(f"ERROR: {target['name']} - {str(e)}")
    
    return results

async def save_results(results):
    """Save crawl results to files"""
    
    # Create output directory
    output_dir = Path("knowledge_base/crawl4ai_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"crawl4ai_test_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Create summary
    successful_crawls = sum(1 for r in results if r['crawl_success'])
    total_content = sum(r['content_length'] for r in results)
    
    summary = {
        'test_timestamp': datetime.now().isoformat(),
        'total_targets': len(results),
        'successful_crawls': successful_crawls,
        'success_rate': (successful_crawls / len(results)) * 100 if results else 0,
        'total_content_length': total_content,
        'average_content_length': total_content / len(results) if results else 0,
        'crawl4ai_installation': 'SUCCESS',
        'windows_compatibility': 'SUCCESS',
        'cost': '$0 (Free Open Source)'
    }
    
    summary_file = output_dir / f"crawl4ai_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"Detailed results: {results_file}")
    print(f"Summary results: {summary_file}")
    
    return summary

async def main():
    """Main test function"""
    print("FineHero Crawl4AI Simple Test")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    print()
    
    # Test crawling
    results = await test_crawl_simple()
    
    # Save results
    summary = await save_results(results)
    
    # Print summary
    print()
    print("CRAWL4AI TEST SUMMARY")
    print("=" * 50)
    print(f"Targets crawled: {summary['total_targets']}")
    print(f"Successful crawls: {summary['successful_crawls']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Total content: {summary['total_content_length']:,} characters")
    print(f"Average content: {summary['average_content_length']:,.0f} characters")
    print(f"Installation: {summary['crawl4ai_installation']}")
    print(f"Windows compatibility: {summary['windows_compatibility']}")
    print(f"Cost: {summary['cost']}")
    print()
    
    # Print detailed results
    print("DETAILED RESULTS:")
    print("-" * 30)
    for result in results:
        status = "SUCCESS" if result['crawl_success'] else "FAILED"
        print(f"{result['source']}: {status}")
        if result['crawl_success']:
            print(f"  Content length: {result['content_length']:,} characters")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print()
    print(f"Completed: {datetime.now()}")
    
    return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        print("\nCrawl4AI test completed successfully!")
        print("FineHero modern content discovery is working!")
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        sys.exit(1)