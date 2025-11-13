#!/usr/bin/env python3
"""
Verify Manual Downloads Script
==============================

Checks if all required legal documents have been successfully downloaded
and validates their file integrity.
"""

import os
from pathlib import Path
from datetime import datetime

def verify_downloads():
    """Verify all required downloads are present and valid"""
    
    required_files = {
        "01_Fontes_Oficiais/Diario_da_Republica/codigo_da_estrada_consolidado.pdf": {
            "name": "Código da Estrada (Consolidated)",
            "min_size": 1024 * 1024,  # 1MB
            "description": "Complete Portuguese Traffic Code"
        },
        "01_Fontes_Oficiais/Diario_da_Republica/decreto_lei_81_2006.pdf": {
            "name": "Decreto-Lei 81/2006", 
            "min_size": 100 * 1024,  # 100KB
            "description": "Parking Regulations"
        },
        "01_Fontes_Oficiais/Lisboa_Municipal/lisboa_regulamento_estacionamento.pdf": {
            "name": "Lisbon Parking Regulations",
            "min_size": 200 * 1024,  # 200KB
            "description": "Lisbon municipal parking rules"
        },
        "01_Fontes_Oficiais/Porto_Municipal/porto_regulamento_estacionamento.pdf": {
            "name": "Porto Parking Regulations", 
            "min_size": 200 * 1024,  # 200KB
            "description": "Porto municipal parking rules"
        }
    }
    
    print("=== Portuguese Legal Documents Verification ===")
    print(f"Verification date: {datetime.now().isoformat()}\n")
    
    missing_files = []
    incomplete_files = []
    
    for file_path, info in required_files.items():
        path = Path(file_path)
        print(f"Checking: {info['name']}")
        print(f"  Path: {file_path}")
        
        if not path.exists():
            print(f"  ❌ MISSING")
            missing_files.append(file_path)
        elif not path.is_file():
            print(f"  ❌ NOT A FILE")
            missing_files.append(file_path)
        else:
            file_size = path.stat().st_size
            print(f"  Size: {file_size / 1024 / 1024:.1f} MB")
            
            if file_size >= info['min_size']:
                print(f"  ✅ COMPLETE")
            else:
                print(f"  ⚠️  INCOMPLETE (expected > {info['min_size']/1024/1024:.1f} MB)")
                incomplete_files.append(file_path)
        
        print()
    
    # Summary
    print("=== VERIFICATION SUMMARY ===")
    print(f"Total files checked: {len(required_files)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Incomplete files: {len(incomplete_files)}")
    print(f"Successful downloads: {len(required_files) - len(missing_files) - len(incomplete_files)}")
    
    if missing_files:
        print("\n❌ MISSING FILES:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    if incomplete_files:
        print("\n⚠️  INCOMPLETE FILES:")
        for file_path in incomplete_files:
            print(f"  - {file_path}")
    
    success = len(missing_files) == 0 and len(incomplete_files) == 0
    
    if success:
        print("\n🎉 ALL FILES SUCCESSFULLY DOWNLOADED!")
        print("You can now run the knowledge base generation script.")
    else:
        print("\n📋 ACTION REQUIRED:")
        print("Please download the missing/incomplete files before proceeding.")
    
    return success

if __name__ == "__main__":
    verify_downloads()
