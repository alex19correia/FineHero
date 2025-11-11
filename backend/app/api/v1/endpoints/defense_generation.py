from typing import Dict, Any, Optional
from datetime import datetime
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.services.defense_generator import DefenseGenerator
from backend.app.schemas import Fine, Defense, DefenseCreate
from backend.app import crud
from ..fines import get_db

router = APIRouter()

@router.post("/defenses/generate")
def generate_defense(
    fine_data: Fine,
    include_context: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered defense for a traffic fine.
    
    This endpoint:
    1. Uses RAG to retrieve relevant legal context
    2. Generates prompt for Gemini AI
    3. Returns AI-generated defense or template fallback
    4. Tracks generation metrics
    
    Args:
        fine_data: Fine object with infraction details
        include_context: Whether to include legal context in response
        
    Returns:
        Defense object with generated content and metadata
    """
    try:
        # Generate defense using DefenseGenerator
        generator = DefenseGenerator(fine_data)
        
        # Measure generation time
        start_time = time.time()
        
        # Generate the defense
        defense_content = generator.generate()
        
        generation_time = time.time() - start_time
        
        # Create defense in database
        defense_create = DefenseCreate(
            fine_id=fine_data.id if hasattr(fine_data, 'id') and fine_data.id else 0,  # Will be updated after creation
            defense_text=defense_content,
            success_probability=0.75  # Default, could be enhanced with ML model
        )
        
        # Save defense to database if fine exists
        if hasattr(fine_data, 'id') and fine_data.id:
            # Try to get the fine first
            db_fine = crud.get_fine(db, fine_id=fine_data.id)
            if db_fine:
                defense = crud.create_fine_defense(db=db, defense=defense_create, fine_id=fine_data.id)
            else:
                defense = None
        else:
            defense = None
        
        # Return comprehensive response
        response = {
            "defense_text": defense_content,
            "generation_time": round(generation_time, 2),
            "success": True,
            "ai_used": generator.gemini_available,
            "template_fallback": not generator.gemini_available,
            "context_included": include_context,
            "quality_score": 0.75,  # Default quality score
            "recommendations": [
                "Review generated defense for accuracy",
                "Customize with specific case details",
                "Consider seeking legal advice for complex cases"
            ],
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        }
        
        # Add database defense info if available
        if defense:
            response["defense_id"] = defense.id
            response["fine_id"] = defense.fine_id
        
        return response
        
    except Exception as e:
        # Return template defense on error
        generator = DefenseGenerator(fine_data)
        fallback_defense = generator._get_template_defense()
        
        return {
            "defense_text": fallback_defense,
            "generation_time": 0.5,
            "success": False,
            "error": str(e),
            "ai_used": False,
            "template_fallback": True,
            "context_included": include_context,
            "quality_score": 0.3,  # Lower quality for fallback
            "recommendations": [
                "AI generation failed - please retry",
                "Use template defense as starting point",
                "Contact support if issue persists"
            ],
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        }

@router.get("/defenses/templates")
def get_defense_templates():
    """
    Get available defense templates for different infraction types.
    
    Returns a list of template categories and their descriptions.
    """
    templates = {
        "parking_violations": {
            "description": "Templates for parking-related violations",
            "infraction_codes": ["ART-048", "ART-049"],
            "common_arguments": [
                "Improper signage",
                "Technical violation",
                "Circumstantial factors"
            ]
        },
        "speed_violations": {
            "description": "Templates for speeding violations",
            "infraction_codes": ["ART-085", "ART-105"],
            "common_arguments": [
                "Speed measurement accuracy",
                "Weather conditions",
                "Traffic circumstances"
            ]
        },
        "document_violations": {
            "description": "Templates for missing/expired documents",
            "infraction_codes": ["ART-121"],
            "common_arguments": [
                "Document validity",
                "Administrative error",
                "Compliance efforts"
            ]
        },
        "general_procedural": {
            "description": "General procedural defense templates",
            "infraction_codes": ["ART-135", "ART-137"],
            "common_arguments": [
                "Procedure compliance",
                "Notification validity",
                "Legal representation rights"
            ]
        }
    }
    
    return {
        "templates": templates,
        "total_categories": len(templates),
        "last_updated": "2025-11-11T22:16:00Z"
    }

@router.post("/defenses/validate")
def validate_defense(
    defense_text: str
):
    """
    Validate generated defense quality and completeness.
    
    Provides feedback on defense strength and suggestions for improvement.
    """
    validation_criteria = {
        "structure": {
            "description": "Proper legal document structure",
            "required_elements": ["introduction", "facts", "arguments", "conclusion"]
        },
        "legal_references": {
            "description": "Appropriate legal citations and references",
            "weight": 0.3
        },
        "specificity": {
            "description": "Case-specific details and customization",
            "weight": 0.25
        },
        "formality": {
            "description": "Appropriate formal legal language",
            "weight": 0.25
        },
        "completeness": {
            "description": "Comprehensive argument coverage",
            "weight": 0.2
        }
    }
    
    # Simple validation heuristics
    validation_results = {
        "structure_score": 0.0,
        "legal_references_score": 0.0,
        "specificity_score": 0.0,
        "formality_score": 0.0,
        "completeness_score": 0.0,
        "overall_quality": 0.0,
        "issues": [],
        "suggestions": []
    }
    
    # Check structure
    structure_keywords = ["Exmo.", "Venho por este meio", "Factos:", "Argumentos:", "Cumprimentos"]
    structure_score = sum(1 for keyword in structure_keywords if keyword in defense_text)
    validation_results["structure_score"] = min(1.0, structure_score / len(structure_keywords))
    
    # Check legal references
    legal_keywords = ["código da estrada", "lei", "decreto", "portaria", "artigo"]
    legal_score = sum(1 for keyword in legal_keywords if keyword.lower() in defense_text.lower())
    validation_results["legal_references_score"] = min(1.0, legal_score / len(legal_keywords))
    
    # Check specificity (presence of specific details)
    specificity_score = 0.5  # Base score
    if len(defense_text) > 500:  # Reasonable length
        specificity_score += 0.2
    if defense_text.count(".") > 3:  # Multiple sentences
        specificity_score += 0.3
    
    validation_results["specificity_score"] = min(1.0, specificity_score)
    
    # Calculate overall quality
    weights = [0.2, 0.3, 0.25, 0.25]  # Structure, legal refs, specificity, formality
    scores = [validation_results["structure_score"], validation_results["legal_references_score"], 
              validation_results["specificity_score"], 0.7]  # Default formality score
    validation_results["overall_quality"] = sum(w * s for w, s in zip(weights, scores))
    
    # Generate issues and suggestions
    if validation_results["structure_score"] < 0.5:
        validation_results["issues"].append("Defense structure may be incomplete")
        validation_results["suggestions"].append("Include proper legal document format with introduction, facts, arguments, and conclusion")
    
    if validation_results["legal_references_score"] < 0.3:
        validation_results["issues"].append("Limited legal references found")
        validation_results["suggestions"].append("Add specific legal citations and references to relevant articles")
    
    if validation_results["specificity_score"] < 0.6:
        validation_results["issues"].append("Defense may lack sufficient case-specific details")
        validation_results["suggestions"].append("Customize the defense with specific details about your case")
    
    if validation_results["overall_quality"] < 0.6:
        validation_results["issues"].append("Overall defense quality could be improved")
        validation_results["suggestions"].append("Consider revising the defense or seeking legal assistance")
    
    validation_results["quality_grade"] = (
        "A" if validation_results["overall_quality"] >= 0.8 else
        "B" if validation_results["overall_quality"] >= 0.7 else
        "C" if validation_results["overall_quality"] >= 0.6 else
        "D"
    )
    
    return {
        "validation_results": validation_results,
        "recommendation": "Use as-is" if validation_results["overall_quality"] >= 0.7 else "Revise recommended",
        "validated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    }