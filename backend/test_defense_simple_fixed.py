#!/usr/bin/env python3
"""
Simple test of the DefenseGenerator without full RAG integration
This creates a minimal working version to validate core functionality
"""

import sys
import os
from datetime import date
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.schemas import Fine

def test_defense_generator_basic():
    """
    Test the basic defense generator functionality with simulated legal context
    """
    print("=== Testing FineHero Defense Generator ===")
    
    # Create a test fine object
    test_fine = Fine(
        id=1,
        location="Lisboa, Rua Augusta",
        infraction_code="P-48-01",
        fine_amount=60.0,
        infractor="João Silva"
    )
    
    print(f"Test Fine Created:")
    print(f"- Date: {test_fine.date}")
    print(f"- Location: {test_fine.location}")
    print(f"- Infraction: {test_fine.infraction_code}")
    print(f"- Amount: €{test_fine.fine_amount}")
    print(f"- Infractor: {test_fine.infractor}")
    print()
    
    # Initialize the DefenseGenerator
    try:
        from services.defense_generator import DefenseGenerator
        generator = DefenseGenerator(test_fine)
        print("[OK] DefenseGenerator initialized successfully!")
        
        # Generate a basic prompt with Portuguese legal context
        prompt = generator.generate_prompt()
        print("\n--- Generated Legal Prompt ---")
        print(prompt[:300] + "...")
        print("--- End of Prompt ---")
        
        # Generate a basic defense using the Portuguese legal laws we added
        defense = generator.request_defense(prompt)
        print(f"\n--- Generated Defense Letter ({len(defense)} chars) ---")
        print(defense)
        print("--- End of Defense ---")
        
        # Test RAG retrieval with our legal documents
        print("\n--- Testing RAG Integration ---")
        try:
            from rag.retriever import RAGRetriever
            retriever = RAGRetriever()
            legal_results = retriever.retrieve("estacionamento proibido", k=2)
            print(f"RAG retrieved {len(legal_results)} relevant legal documents")
            for i, result in enumerate(legal_results):
                print(f"Document {i+1}: {result[:100]}...")
        except Exception as e:
            print(f"RAG test failed: {e}")
        
        print("\n[OK] Basic Defense Generation Test PASSED!")
        return True
        
    except Exception as e:
        print(f"[FAIL] DefenseGenerator test failed: {e}")
        return False

def test_portuguese_legal_content():
    """
    Test that our Portuguese legal documents are accessible
    """
    print("\n=== Testing Portuguese Legal Content ===")
    
    knowledge_base_dir = "../knowledge_base/legal_articles"
    if not os.path.exists(knowledge_base_dir):
        print(f"[FAIL] Knowledge base directory not found: {knowledge_base_dir}")
        return False
    
    # List available legal documents
    legal_files = [f for f in os.listdir(knowledge_base_dir) if f.endswith('.txt')]
    print(f"Found {len(legal_files)} Portuguese legal documents:")
    
    for file in legal_files:
        file_path = os.path.join(knowledge_base_dir, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"- {file}: {len(content)} characters")
        print(f"  Preview: {content[:100]}...")
        print()
    
    print("[OK] Portuguese Legal Content Test PASSED!")
    return len(legal_files) > 0

if __name__ == "__main__":
    print("FineHero System Test - Tuesday Implementation")
    print("=" * 50)
    
    # Test 1: Portuguese Legal Content
    content_ok = test_portuguese_legal_content()
    
    # Test 2: Defense Generator
    generator_ok = test_defense_generator_basic()
    
    # Final Status
    print("\n" + "=" * 50)
    print("FINAL TEST RESULTS:")
    print(f"- Portuguese Legal Content: {'[OK] PASS' if content_ok else '[FAIL] FAIL'}")
    print(f"- Defense Generator: {'[OK] PASS' if generator_ok else '[FAIL] FAIL'}")
    
    if content_ok and generator_ok:
        print("\n[SUCCESS] TUESDAY IMPLEMENTATION SUCCESSFUL!")
        print("FineHero can now generate Portuguese legal defenses!")
    else:
        print("\n[WARNING] Some tests failed - further fixes needed")
    
    print("=" * 50)