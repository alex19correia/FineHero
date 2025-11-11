"""
CRUD operations for user management.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional, List
from app.models import User
from app.schemas_auth import UserCreate, UserUpdate
from app.auth import get_password_hash, verify_password
from datetime import datetime

def create_user(db: Session, user: UserCreate) -> Optional[User]:
    """Create a new user."""
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name,
            subscription_tier=user.subscription_tier
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"User with this email or username already exists: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user information."""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        # Handle Pydantic v1/v2 compatibility
        try:
            # Try Pydantic v2 first
            update_data = user_update.model_dump(exclude_unset=True)
        except AttributeError:
            # Fall back to Pydantic v1
            update_data = user_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Update failed - user may already exist with provided email/username: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

def update_last_login(db: Session, user_id: int) -> Optional[User]:
    """Update user's last login timestamp."""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")

def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """Change user's password."""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        if not verify_password(current_password, db_user.hashed_password):
            return False
        
        db_user.hashed_password = get_password_hash(new_password)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")

def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Deactivate a user account."""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        db_user.is_active = False
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user account."""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error occurred: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error: {str(e)}")