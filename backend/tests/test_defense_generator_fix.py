#!/usr/bin/env python3
"""
Test script to validate that the defense generator fix works correctly.
This tests the BLOCKER #1 fix: Defense Generator Broken
"""

import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_defense_generator_import():
    """Test that the defense generator can be imported successfully."""
    try:
        from services.defense_generator import DefenseGenerator
        print("OK: DefenseGenerator imported successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import DefenseGenerator: {e}")
        return False

def test_defense_generator_initialization():
    """Test that DefenseGenerator initializes correctly."""
    try:
        from services.defense_generator import DefenseGenerator
        from app.schemas import Fine
        
        # Create a mock fine data
        fine_data = Fine(
            date=datetime(2025, 11, 11),
            location="Lisboa",
            infraction_code="ART-135-1-A",
            fine_amount=120.0,
            infractor="João Silva"
        )
        
        # Initialize defense generator
        generator = DefenseGenerator(fine_data)
        
        print("✅ DefenseGenerator initialized successfully")
        print(f"   - Fine data: {fine_data.location}, {fine_data.infraction_code}")
        print(f"   - Gemini available: {getattr(generator, 'gemini_available', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize DefenseGenerator: {e}")
        return False

def test_defense_generation_no_ai():
    """Test defense generation without AI (fallback to template)."""
    try:
        from services.defense_generator import DefenseGenerator
        from app.schemas import Fine
        
        # Create a mock fine data
        fine_data = Fine(
            date=datetime(2025, 11, 11),
            location="Lisboa",
            infraction_code="ART-135-1-A",
            fine_amount=120.0,
            infractor="João Silva"
        )
        
        # Initialize defense generator (will use template since no API key)
        generator = DefenseGenerator(fine_data)
        
        # Generate a defense
        defense = generator.generate()
        
        # Verify the defense is not a placeholder
        assert defense is not None, "Defense should not be None"
        assert len(defense) > 100, "Defense should be substantial"
        assert "João Silva" in defense, "Defense should contain infractor name"
        assert "Lisboa" in defense, "Defense should contain location"
        assert "ART-135-1-A" in defense, "Defense should contain infraction code"
        assert "[Argumento legal gerado pela AI]" not in defense, "Should not contain placeholder text"
        
        print("✅ Defense generation works (template fallback)")
        print(f"   - Defense length: {len(defense)} characters")
        print(f"   - Contains real data: ✅")
        print(f"   - No placeholder text: ✅")
        return True
    except Exception as e:
        print(f"❌ Defense generation failed: {e}")
        return False

def test_configuration():
    """Test that configuration is loaded correctly."""
    try:
        from core.config import settings
        
        print("✅ Configuration loaded successfully")
        print(f"   - APP_NAME: {settings.APP_NAME}")
        print(f"   - GOOGLE_AI_API_KEY set: {'Yes' if settings.GOOGLE_AI_API_KEY else 'No (expected for testing)'}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_placeholder_eliminated():
    """Test that the old placeholder text is eliminated."""
    try:
        with open('services/defense_generator.py', 'r') as f:
            content = f.read()
        
        # Check that old placeholder text is gone
        assert '[Argumento legal gerado pela AI]' not in content, "Old placeholder should be removed"
        
        # Check that new implementation is present
        assert 'google.generativeai' in content, "Gemini API import should be present"
        assert 'self.model.generate_content' in content, "Gemini API call should be present"
        assert '_get_template_defense' in content, "Template fallback should be present"
        
        print("✅ Placeholder text eliminated successfully")
        print("   - Old placeholder removed: ✅")
        print("   - Gemini API integration added: ✅")
        print("   - Template fallback present: ✅")
        return True
    except Exception as e:
        print(f"❌ Placeholder elimination check failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("DEFENSE GENERATOR FIX VALIDATION")
    print("Testing BLOCKER #1: Defense Generator Broken")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration),
        ("Import Test", test_defense_generator_import),
        ("Initialization Test", test_defense_generator_initialization),
        ("Placeholder Elimination", test_placeholder_eliminated),
        ("Defense Generation", test_defense_generation_no_ai),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   Test failed")
        except Exception as e:
            print(f"   Test error: {e}")
    
    print("\n" + "=" * 60)
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - BLOCKER #1 FIX SUCCESSFUL!")
        print("\nSummary of changes:")
        print("✅ Replaced hardcoded placeholder with Gemini API integration")
        print("✅ Added proper error handling and fallback to template")
        print("✅ Enhanced logging and debugging capabilities")
        print("✅ Configuration updated to support Google AI API key")
        print("✅ Template defense now uses actual fine data")
        return True
    else:
        print("❌ SOME TESTS FAILED - Please review the implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)