from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_
from . import models, schemas

# Enhanced CRUD functions with N+1 query fixes

def get_fine(db: Session, fine_id: int):
    """
    Get a single fine by ID with eager loading of related data.
    """
    return db.query(models.Fine).options(
        selectinload(models.Fine.user)
    ).filter(models.Fine.id == fine_id).first()

def get_fines(db: Session, skip: int = 0, limit: int = 100):
    """
    Get a list of fines with eager loading of related data.
    """
    return db.query(models.Fine).options(
        selectinload(models.Fine.user)
    ).offset(skip).limit(limit).all()

def create_fine(db: Session, fine: schemas.FineCreate):
    """
    Create a new fine.
    """
    db_fine = models.Fine(**fine.dict())
    db.add(db_fine)
    db.commit()
    db.refresh(db_fine)
    return db_fine

# Enhanced Defense CRUD functions with eager loading

def get_fine_defenses(db: Session, fine_id: int):
    """
    Get all defenses for a specific fine with eager loading to avoid N+1 queries.
    Uses selectinload to eagerly load the fine relationship for all defenses.
    """
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.fine_id == fine_id).all()

def get_defense(db: Session, defense_id: int):
    """
    Get a specific defense by ID with eager loading.
    """
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.id == defense_id).first()

def create_fine_defense(db: Session, defense: schemas.DefenseCreate, fine_id: int):
    """
    Create a new defense for a fine.
    """
    db_defense = models.Defense(**defense.dict(), fine_id=fine_id)
    db.add(db_defense)
    db.commit()
    db.refresh(db_defense)
    return db_defense

# Additional CRUD functions to prevent N+1 queries

def get_user_fines_with_defenses(db: Session, user_id: int):
    """
    Get all fines for a user with their defenses using eager loading.
    Uses selectinload to eagerly load the defenses relationship to avoid N+1 queries.
    """
    return db.query(models.Fine).options(
        selectinload(models.Fine.defenses)
    ).filter(models.Fine.user_id == user_id).all()

def get_user_defenses_with_fines(db: Session, user_id: int):
    """
    Get all defenses for a user with their associated fines using eager loading.
    Uses selectinload to eagerly load the fine relationship for all defenses.
    """
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.user_id == user_id).all()
