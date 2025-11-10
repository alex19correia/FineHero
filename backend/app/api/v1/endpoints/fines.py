from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....app import crud, models, schemas
from .... import database

models.Base.metadata.create_all(bind=database.engine)

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/fines/", response_model=schemas.Fine)
def create_fine(fine: schemas.FineCreate, db: Session = Depends(get_db)):
    """
    Create a new fine.
    """
    return crud.create_fine(db=db, fine=fine)

@router.get("/fines/", response_model=List[schemas.Fine])
def read_fines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve multiple fines.
    """
    fines = crud.get_fines(db, skip=skip, limit=limit)
    return fines

@router.get("/fines/{fine_id}", response_model=schemas.Fine)
def read_fine(fine_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single fine by ID.
    """
    db_fine = crud.get_fine(db, fine_id=fine_id)
    if db_fine is None:
        raise HTTPException(status_code=404, detail="Fine not found")
    return db_fine
