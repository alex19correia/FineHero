from typing import List, Dict, Any
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....app import crud, schemas
from ....services.defense_generator import DefenseGenerator
from .fines import get_db # Reuse the get_db dependency

router = APIRouter()

@router.post("/fines/{fine_id}/defenses/", response_model=schemas.DefenseWithMetadata)
def create_defense_for_fine(
    fine_id: int, db: Session = Depends(get_db)
):
    """
    Create a defense for a specific fine using AI generation.
    """
    try:
        # Get the fine data
        fine = crud.get_fine(db, fine_id=fine_id)
        if not fine:
            raise HTTPException(status_code=404, detail="Fine not found")
        
        # Create Fine object for defense generator
        fine_data = schemas.Fine(
            id=fine.id,
            date=fine.date,
            location=fine.location,
            infraction_code=fine.infraction_code,
            fine_amount=fine.fine_amount,
            infractor=fine.infractor
        )
        
        # Generate defense using AI
        generator = DefenseGenerator(fine_data)
        
        # Measure generation time
        start_time = time.time()
        
        # Generate the defense
        defense_content = generator.generate()
        
        generation_time = time.time() - start_time
        
        # Create defense record
        defense_create = schemas.DefenseCreate(
            defense_text=defense_content,
            success_probability=0.75  # Default, could be enhanced with ML model
        )
        
        defense = crud.create_fine_defense(db=db, defense=defense_create, fine_id=fine_id)
        
        # Return enhanced response with metadata
        return {
            **defense.__dict__,
            "generation_time": round(generation_time, 2),
            "ai_used": generator.gemini_available,
            "template_fallback": not generator.gemini_available
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}") from e
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Service configuration error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Defense generation failed: {str(e)}") from e

@router.get("/defenses/{defense_id}")
def get_defense(defense_id: int, db: Session = Depends(get_db)):
    """
    Get a specific defense by ID.
    """
    defense = crud.get_defense(db, defense_id=defense_id)
    if not defense:
        raise HTTPException(status_code=404, detail="Defense not found")
    return defense

@router.get("/fines/{fine_id}/defenses")
def get_fine_defenses(fine_id: int, db: Session = Depends(get_db)):
    """
    Get all defenses for a specific fine.
    """
    defenses = crud.get_fine_defenses(db, fine_id=fine_id)
    return defenses
