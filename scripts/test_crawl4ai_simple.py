#!/usr/bin/env python3
"""
Simple Crawl4AI Installation Test
=================================

Tests basic Crawl4AI functionality without unicode characters.
"""

import asyncio
import sys
import json
from datetime import datetime

# Test if Crawl4AI is available
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.content_filter_strategy import PruningContentFilter
    CRAWL4AI_AVAILABLE = True
    print("SUCCESS: Crawl4AI module imported successfully")
except ImportError as e:
    CRAWL4AI_AVAILABLE = False
    print(f"ERROR: Crawl4AI not available: {e}")

# Test basic browser functionality
async def test_browser_launch():
    """Test if browser can launch"""
    if not CRAWL4AI_AVAILABLE:
        return False
    
    try:
        # Simple browser config
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=False
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("SUCCESS: Browser launched successfully")
            return True
            
    except Exception as e:
        print(f"ERROR: Browser launch failed: {e}")
        return False

# Test basic web crawling
async def test_simple_crawl():
    """Test simple web crawling on a basic site"""
    if not CRAWL4AI_AVAILABLE:
        return False
    
    try:
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Test with a simple, reliable site
            result = await crawler.arun("https://httpbin.org/html")
            
            if result.success:
                content_length = len(result.markdown)
                print(f"SUCCESS: Crawled content successfully")
                print(f"Content length: {content_length} characters")
                return True
            else:
                print(f"WARNING: Crawl returned success=False")
                return False
                
    except Exception as e:
        print(f"ERROR: Simple crawl failed: {e}")
        return False

# Test Portuguese legal site access (DRE)
async def test_portuguese_legal_access():
    """Test access to Portuguese legal sites"""
    if not CRAWL4AI_AVAILABLE:
        return False
    
    try:
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Test DRE access
            result = await crawler.arun("https://dre.pt/", wait_for="networkidle")
            
            if result.success:
                content_length = len(result.markdown)
                print(f"SUCCESS: DRE access successful")
                print(f"DRE content length: {content_length} characters")
                return True
            else:
                print(f"WARNING: DRE crawl returned success=False")
                return False
                
    except Exception as e:
        print(f"ERROR: Portuguese legal site access failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=== FineHero Crawl4AI Installation Test ===")
    print(f"Test time: {datetime.now().isoformat()}")
    print()
    
    results = {}
    
    # Test 1: Module import
    print("Test 1: Crawl4AI Module Import")
    results['module_import'] = CRAWL4AI_AVAILABLE
    print(f"Result: {'PASS' if CRAWL4AI_AVAILABLE else 'FAIL'}")
    print()
    
    # Test 2: Browser launch
    print("Test 2: Browser Launch")
    if CRAWL4AI_AVAILABLE:
        results['browser_launch'] = await test_browser_launch()
        print(f"Result: {'PASS' if results['browser_launch'] else 'FAIL'}")
    else:
        results['browser_launch'] = False
        print("Result: SKIP (module not available)")
    print()
    
    # Test 3: Simple crawl
    print("Test 3: Simple Web Crawl")
    if CRAWL4AI_AVAILABLE and results.get('browser_launch'):
        results['simple_crawl'] = await test_simple_crawl()
        print(f"Result: {'PASS' if results['simple_crawl'] else 'FAIL'}")
    else:
        results['simple_crawl'] = False
        print("Result: SKIP (browser not available)")
    print()
    
    # Test 4: Portuguese legal access
    print("Test 4: Portuguese Legal Site Access")
    if CRAWL4AI_AVAILABLE and results.get('browser_launch'):
        results['portuguese_access'] = await test_portuguese_legal_access()
        print(f"Result: {'PASS' if results['portuguese_access'] else 'FAIL'}")
    else:
        results['portuguese_access'] = False
        print("Result: SKIP (browser not available)")
    print()
    
    # Summary
    print("=== Test Summary ===")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")
    
    if passed_tests >= 3:
        print("OVERALL: SUCCESS - Crawl4AI is working properly!")
        print("You can now run the full FineHero implementation")
    elif passed_tests >= 2:
        print("OVERALL: PARTIAL - Crawl4AI is partially working")
        print("Some tests failed but basic functionality is available")
    else:
        print("OVERALL: FAILURE - Crawl4AI installation needs attention")
        print("Please check the installation and dependencies")
    
    # Save test results
    test_results = {
        'test_time': datetime.now().isoformat(),
        'crawl4ai_available': CRAWL4AI_AVAILABLE,
        'test_results': results,
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests/total_tests*100 if total_tests > 0 else 0
        }
    }
    
    with open('crawl4ai_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nTest results saved to: crawl4ai_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())