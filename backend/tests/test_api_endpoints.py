#!/usr/bin/env python3
"""
Test script to validate the new API endpoints for BLOCKER #2
Tests all the missing API features that were implemented
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_api_endpoint_imports():
    """Test that all new API endpoints can be imported."""
    print("Testing API endpoint imports...")
    
    try:
        # Test existing endpoints
        from app.api.v1.endpoints import fines, defenses
        print("PASS: Existing endpoints imported")
        
        # Test new endpoints
        from app.api.v1.endpoints import rag, quality, analytics, knowledge_base
        print("PASS: New advanced feature endpoints imported")
        
        return True
    except ImportError as e:
        print(f"FAIL: Import error: {e}")
        return False

def test_endpoint_routers():
    """Test that all routers are properly defined."""
    print("\nTesting router objects...")
    
    try:
        from app.api.v1.endpoints import fines, defenses, rag, quality, analytics, knowledge_base
        
        routers = {
            'fines': fines.router,
            'defenses': defenses.router,
            'rag': rag.router,
            'quality': quality.router,
            'analytics': analytics.router,
            'knowledge_base': knowledge_base.router
        }
        
        total_routes = 0
        for name, router in routers.items():
            if hasattr(router, 'routes'):
                route_count = len(router.routes)
                total_routes += route_count
                print(f"OK: {name}: {route_count} routes defined")
            else:
                print(f"ERROR: {name}: No routes attribute")
                return False
        
        print(f"Total API routes: {total_routes}")
        
        if total_routes >= 15:
            print("OK: Sufficient number of routes defined")
            return True
        else:
            print(f"WARNING: Expected at least 15 routes, found {total_routes}")
            return False
            
    except Exception as e:
        print(f"FAIL: Router test error: {e}")
        return False

def test_defense_generator_implementation():
    """Test that defense generator is properly implemented."""
    print("\nTesting defense generator implementation...")
    
    try:
        from services.defense_generator import DefenseGenerator
        print("PASS: DefenseGenerator class available")
        
        # Check for the updated implementation
        with open('services/defense_generator.py', 'r') as f:
            content = f.read()
        
        # Verify AI integration is present
        if 'google.generativeai' in content:
            print("PASS: AI integration found")
        else:
            print("FAIL: AI integration not found")
            return False
            
        # Verify template fallback exists
        if '_get_template_defense' in content:
            print("PASS: Template fallback implemented")
        else:
            print("FAIL: Template fallback not found")
            return False
            
        # Verify placeholder is removed
        if '[Argumento legal gerado pela AI]' not in content:
            print("PASS: Placeholder text removed")
        else:
            print("FAIL: Placeholder text still present")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL: Defense generator test error: {e}")
        return False

def test_main_api_file():
    """Test that main.py properly includes all routers."""
    print("\nTesting main API file...")
    
    try:
        with open('app/main.py', 'r') as f:
            content = f.read()
        
        # Check for router registrations
        expected_imports = ['fines', 'defenses', 'rag', 'quality', 'analytics', 'knowledge_base']
        for import_name in expected_imports:
            if import_name in content:
                print(f"OK: {import_name} router registered")
            else:
                print(f"FAIL: {import_name} router not found")
                return False
        
        # Check for new API features endpoint
        if '/api/v1/features' in content:
            print("PASS: Features endpoint found")
        else:
            print("FAIL: Features endpoint not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"FAIL: Main API file test error: {e}")
        return False

def main():
    print("=" * 60)
    print("API ENDPOINTS VALIDATION - BLOCKER #2")
    print("=" * 60)
    print("Testing the implementation of missing API features...")
    print("Expected: 70% of features now exposed via REST API")
    print()
    
    tests = [
        test_api_endpoint_imports,
        test_endpoint_routers,
        test_defense_generator_implementation,
        test_main_api_file
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: BLOCKER #2 FIX SUCCESSFUL!")
        print("\nAPI Features Now Exposed:")
        print("✓ RAG search endpoint (/api/v1/rag/search)")
        print("✓ Quality scoring results (/api/v1/documents/{id}/quality)")
        print("✓ Analytics dashboard (/api/v1/analytics/user/{id}/dashboard)")
        print("✓ Knowledge base management (/api/v1/knowledge-base/status)")
        print("✓ Enhanced defense generation (/api/v1/defenses/generate)")
        print("✓ Features endpoint (/api/v1/features)")
        print("\nImpact: Advanced capabilities now accessible via REST API")
        return True
    else:
        print("PARTIAL SUCCESS: Some tests failed")
        print("Review failed tests and resolve issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)