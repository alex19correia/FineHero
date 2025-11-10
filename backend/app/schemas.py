from pydantic import BaseModel
from typing import Optional
from datetime import date

class FineBase(BaseModel):
    """
    Base schema for a traffic fine.
    """
    date: Optional[date] = None
    location: Optional[str] = None
    infractor: Optional[str] = None
    fine_amount: Optional[float] = None
    infraction_code: Optional[str] = None
    pdf_reference: Optional[str] = None

class FineCreate(FineBase):
    """
    Schema for creating a new fine.
    """
    pass

class Fine(FineBase):
    """
    Schema for a fine in the database.
    """
    id: int

    class Config:
        orm_mode = True

class DefenseBase(BaseModel):
    """
    Base schema for a defense.
    """
    fine_id: int
    content: str

class DefenseCreate(DefenseBase):
    """
    Schema for creating a new defense.
    """
    pass

class Defense(DefenseBase):
    """
    Schema for a defense in the database.
    """
    id: int

    class Config:
        orm_mode = True
