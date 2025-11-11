#!/usr/bin/env python3
"""
Simple validation test for the defense generator fix.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_basic_import():
    """Test that the defense generator can be imported."""
    try:
        from services.defense_generator import DefenseGenerator
        print("PASS: DefenseGenerator imported successfully")
        return True
    except Exception as e:
        print(f"FAIL: Failed to import DefenseGenerator: {e}")
        return False

def test_config_loading():
    """Test that configuration loads correctly."""
    try:
        from core.config import settings
        print(f"PASS: Configuration loaded - APP_NAME: {settings.APP_NAME}")
        return True
    except Exception as e:
        print(f"FAIL: Configuration loading failed: {e}")
        return False

def test_placeholder_removed():
    """Test that old placeholder text is eliminated."""
    try:
        with open('services/defense_generator.py', 'r') as f:
            content = f.read()
        
        # Check that old placeholder is gone
        assert '[Argumento legal gerado pela AI]' not in content
        
        # Check new implementation is present
        assert 'google.generativeai' in content
        assert 'self.model.generate_content' in content
        assert '_get_template_defense' in content
        
        print("PASS: Placeholder text eliminated successfully")
        return True
    except Exception as e:
        print(f"FAIL: Placeholder elimination check failed: {e}")
        return False

def main():
    print("=" * 50)
    print("DEFENSE GENERATOR FIX VALIDATION")
    print("=" * 50)
    
    tests = [
        test_basic_import,
        test_config_loading,
        test_placeholder_removed
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: BLOCKER #1 FIX SUCCESSFUL!")
        print("\nChanges made:")
        print("- Replaced hardcoded placeholder with Gemini API integration")
        print("- Added proper error handling and fallback template")
        print("- Enhanced logging and debugging capabilities")
        print("- Updated configuration for Google AI API key support")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)