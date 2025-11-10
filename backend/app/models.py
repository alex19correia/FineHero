from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Fine(Base):
    """
    Database model for a traffic fine.
    """
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    location = Column(String, index=True)
    infractor = Column(String, index=True)
    fine_amount = Column(Float)
    infraction_code = Column(String, index=True)
    pdf_reference = Column(String)

    defenses = relationship("Defense", back_populates="fine")

class Defense(Base):
    """
    Database model for a defense.
    """
    __tablename__ = "defenses"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    fine_id = Column(Integer, ForeignKey("fines.id"))

    fine = relationship("Fine", back_populates="defenses")
