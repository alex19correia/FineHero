from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ....app import crud, schemas
from .fines import get_db # Reuse the get_db dependency

router = APIRouter()

@router.post("/fines/{fine_id}/defenses/", response_model=schemas.Defense)
def create_defense_for_fine(
    fine_id: int, defense: schemas.DefenseCreate, db: Session = Depends(get_db)
):
    """
    Create a defense for a specific fine.
    """
    return crud.create_fine_defense(db=db, defense=defense, fine_id=fine_id)
