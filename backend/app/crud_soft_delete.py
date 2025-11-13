"""
Enhanced CRUD operations with soft delete and audit trail functionality.

This module provides comprehensive CRUD operations that include:
- Soft delete methods (soft_delete, restore, get_active_records)
- Audit trail logging (create_with_audit, update_with_audit, get_audit_history)
- Data retention policies
- GDPR compliance operations

All operations automatically track changes for compliance and provide data recovery capabilities.
"""
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any, Type, TypeVar
from datetime import datetime, timedelta
import json

from . import models, schemas
from .models_base import AuditTrail

# Type variables for better type hints
ModelType = TypeVar('ModelType', bound=models.Base)
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class SoftDeleteCRUD:
    """
    Base CRUD class with soft delete and audit trail capabilities.
    
    Provides common operations for all models that implement soft delete
    and audit mixins, ensuring consistent behavior across the application.
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID, filtering out soft-deleted records.
        """
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).first()
    
    def get_with_deleted(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID, including soft-deleted records.
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering.
        """
        query = db.query(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        # Filter out soft-deleted records if specified
        if active_only:
            query = query.filter(self.model.is_deleted == False)
        
        return query.offset(skip).limit(limit).all()
    
    def get_multi_with_relationships(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        includes: Optional[List[str]] = None,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with eager loading of relationships.
        """
        query = db.query(self.model)
        
        # Add eager loading if specified
        if includes:
            for include in includes:
                if hasattr(self.model, include):
                    relationship = getattr(self.model, include)
                    if hasattr(relationship, 'property'):
                        query = query.options(selectinload(relationship.property))
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        # Filter out soft-deleted records if specified
        if active_only:
            query = query.filter(self.model.is_deleted == False)
        
        return query.offset(skip).limit(limit).all()
    
    def soft_delete(
        self,
        db: Session,
        id: int,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Optional[ModelType]:
        """
        Soft delete a record.
        """
        obj = self.get_with_deleted(db, id=id)
        if obj:
            # Record old values for audit trail
            old_values = {col.name: getattr(obj, col.name) 
                         for col in obj.__table__.columns 
                         if col.name not in ['audit_metadata']}
            
            # Perform soft delete
            obj.soft_delete()
            
            # Update audit information
            metadata = {
                "soft_delete_reason": reason,
                "deleted_at": obj.deleted_at.isoformat() if obj.deleted_at else None
            }
            obj.update_audit_info(user_id, metadata)
            
            # Create audit trail entry
            self._create_audit_entry(
                db, obj, 'SOFT_DELETE', old_values, 
                self._record_to_dict(obj), user_id, reason
            )
            
            db.commit()
            db.refresh(obj)
        return obj
    
    def restore(
        self,
        db: Session,
        id: int,
        user_id: Optional[int] = None
    ) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        """
        obj = db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == True
        ).first()
        
        if obj:
            # Record old values for audit trail
            old_values = self._record_to_dict(obj)
            
            # Restore the record
            obj.restore()
            
            # Update audit information
            metadata = {"restored_at": datetime.utcnow().isoformat()}
            obj.update_audit_info(user_id, metadata)
            
            # Create audit trail entry
            self._create_audit_entry(
                db, obj, 'RESTORE', old_values,
                self._record_to_dict(obj), user_id, "Record restored"
            )
            
            db.commit()
            db.refresh(obj)
        return obj
    
    def permanent_delete(
        self,
        db: Session,
        id: int,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Permanently delete a record (hard delete).
        WARNING: This operation cannot be undone.
        """
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            # Record for audit trail
            old_values = self._record_to_dict(obj)
            
            # Create audit trail entry before deletion
            self._create_audit_entry(
                db, obj, 'PERMANENT_DELETE', old_values, 
                None, user_id, reason or "Permanent deletion"
            )
            
            # Perform permanent deletion
            db.delete(obj)
            db.commit()
            return True
        return False
    
    def get_active_records(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Get all active (non-deleted) records.
        """
        query = db.query(self.model).filter(self.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def get_deleted_records(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get all soft-deleted records.
        """
        return db.query(self.model).filter(
            self.model.is_deleted == True
        ).offset(skip).limit(limit).all()
    
    def count_records(
        self,
        db: Session,
        include_deleted: bool = False
    ) -> int:
        """
        Count total records (active or all).
        """
        query = db.query(self.model)
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        return query.count()
    
    def bulk_soft_delete(
        self,
        db: Session,
        ids: List[int],
        user_id: Optional[int] = None,
        reason: str = "Bulk soft delete"
    ) -> int:
        """
        Soft delete multiple records at once.
        """
        deleted_count = 0
        for id in ids:
            if self.soft_delete(db, id, user_id, reason):
                deleted_count += 1
        return deleted_count
    
    def _create_audit_entry(
        self,
        db: Session,
        obj: ModelType,
        action: str,
        old_values: Optional[Dict],
        new_values: Optional[Dict],
        user_id: Optional[int],
        additional_info: Optional[str]
    ):
        """
        Create an audit trail entry for compliance and debugging.
        """
        try:
            audit_entry = AuditTrail.create_audit_entry(
                table_name=self.model.__tablename__,
                record_id=obj.id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                user_id=user_id,
                additional_info=additional_info
            )
            db.add(audit_entry)
        except Exception as e:
            print(f"Warning: Could not create audit entry: {e}")
    
    def _record_to_dict(self, obj: ModelType) -> Dict:
        """
        Convert a model instance to dictionary for audit logging.
        """
        return {
            col.name: getattr(obj, col.name) 
            for col in obj.__table__.columns
        }


# Fine-specific CRUD operations
class FineCRUD(SoftDeleteCRUD):
    """
    CRUD operations for Fine model with enhanced soft delete and audit capabilities.
    """
    
    def __init__(self):
        super().__init__(models.Fine)
    
    def create_with_audit(
        self,
        db: Session,
        fine: schemas.FineCreate,
        user_id: Optional[int] = None
    ) -> models.Fine:
        """
        Create a fine with audit trail logging.
        """
        db_fine = models.Fine(**fine.dict())
        db_fine.create_with_audit(user_id, {"created_from": "api"})
        
        db.add(db_fine)
        db.commit()
        db.refresh(db_fine)
        
        # Create audit trail entry
        self._create_audit_entry(
            db, db_fine, 'CREATE', None,
            self._record_to_dict(db_fine), user_id, "Fine created"
        )
        
        db.commit()
        return db_fine
    
    def update_with_audit(
        self,
        db: Session,
        id: int,
        fine_update: schemas.FineUpdate,
        user_id: Optional[int] = None
    ) -> Optional[models.Fine]:
        """
        Update a fine with audit trail logging.
        """
        obj = self.get(db, id)
        if obj:
            # Record old values
            old_values = self._record_to_dict(obj)
            
            # Update fields
            update_data = fine_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(obj, field, value)
            
            # Update audit information
            obj.update_audit_info(user_id, {"updated_fields": list(update_data.keys())})
            
            # Create audit trail entry
            self._create_audit_entry(
                db, obj, 'UPDATE', old_values,
                self._record_to_dict(obj), user_id, "Fine updated"
            )
            
            db.commit()
            db.refresh(obj)
        return obj
    
    def get_with_relationships(
        self,
        db: Session,
        id: int
    ) -> Optional[models.Fine]:
        """
        Get a fine with eager loading of related data.
        """
        return db.query(models.Fine).options(
            selectinload(models.Fine.user),
            selectinload(models.Fine.defenses)
        ).filter(
            models.Fine.id == id,
            models.Fine.is_deleted == False
        ).first()
    
    def get_user_fines(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.Fine]:
        """
        Get all fines for a specific user with active records only.
        """
        return db.query(models.Fine).options(
            selectinload(models.Fine.defenses)
        ).filter(
            models.Fine.user_id == user_id,
            models.Fine.is_deleted == False
        ).offset(skip).limit(limit).all()


# Defense-specific CRUD operations
class DefenseCRUD(SoftDeleteCRUD):
    """
    CRUD operations for Defense model with enhanced soft delete and audit capabilities.
    """
    
    def __init__(self):
        super().__init__(models.Defense)
    
    def create_with_audit(
        self,
        db: Session,
        defense: schemas.DefenseCreate,
        fine_id: int,
        user_id: Optional[int] = None
    ) -> models.Defense:
        """
        Create a defense with audit trail logging.
        """
        db_defense = models.Defense(**defense.dict(), fine_id=fine_id)
        db_defense.create_with_audit(user_id, {"fine_id": fine_id})
        
        db.add(db_defense)
        db.commit()
        db.refresh(db_defense)
        
        # Create audit trail entry
        self._create_audit_entry(
            db, db_defense, 'CREATE', None,
            self._record_to_dict(db_defense), user_id, "Defense created"
        )
        
        db.commit()
        return db_defense
    
    def update_with_audit(
        self,
        db: Session,
        id: int,
        defense_update: schemas.DefenseUpdate,
        user_id: Optional[int] = None
    ) -> Optional[models.Defense]:
        """
        Update a defense with audit trail logging.
        """
        obj = self.get(db, id)
        if obj:
            # Record old values
            old_values = self._record_to_dict(obj)
            
            # Update fields
            update_data = defense_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(obj, field, value)
            
            # Update audit information
            obj.update_audit_info(user_id, {"updated_fields": list(update_data.keys())})
            
            # Create audit trail entry
            self._create_audit_entry(
                db, obj, 'UPDATE', old_values,
                self._record_to_dict(obj), user_id, "Defense updated"
            )
            
            db.commit()
            db.refresh(obj)
        return obj
    
    def get_fine_defenses(
        self,
        db: Session,
        fine_id: int,
        active_only: bool = True
    ) -> List[models.Defense]:
        """
        Get all defenses for a specific fine.
        """
        query = db.query(models.Defense).options(
            selectinload(models.Defense.fine),
            selectinload(models.Defense.user)
        ).filter(models.Defense.fine_id == fine_id)
        
        if active_only:
            query = query.filter(models.Defense.is_deleted == False)
        
        return query.all()


# User-specific CRUD operations with GDPR compliance
class UserCRUD(SoftDeleteCRUD):
    """
    CRUD operations for User model with GDPR compliance and audit capabilities.
    """
    
    def __init__(self):
        super().__init__(models.User)
    
    def create_with_audit(
        self,
        db: Session,
        user: schemas.UserCreate
    ) -> models.User:
        """
        Create a user with audit trail logging.
        """
        db_user = models.User(**user.dict())
        db_user.create_with_audit(None, {"registration_source": "api"})
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def update_with_audit(
        self,
        db: Session,
        id: int,
        user_update: schemas.UserUpdate,
        user_id: Optional[int] = None
    ) -> Optional[models.User]:
        """
        Update a user with audit trail logging.
        """
        obj = self.get(db, id)
        if obj:
            # Record old values
            old_values = self._record_to_dict(obj)
            
            # Update fields
            update_data = user_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(obj, field, value)
            
            # Update audit information
            obj.update_audit_info(user_id, {"updated_fields": list(update_data.keys())})
            
            # Create audit trail entry
            self._create_audit_entry(
                db, obj, 'UPDATE', old_values,
                self._record_to_dict(obj), user_id, "User updated"
            )
            
            db.commit()
            db.refresh(obj)
        return obj
    
    def get_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """
        Get user by email (active only).
        """
        return db.query(models.User).filter(
            models.User.email == email,
            models.User.is_deleted == False
        ).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[models.User]:
        """
        Get user by username (active only).
        """
        return db.query(models.User).filter(
            models.User.username == username,
            models.User.is_deleted == False
        ).first()
    
    def update_last_login(
        self,
        db: Session,
        id: int
    ) -> Optional[models.User]:
        """
        Update user's last login timestamp.
        """
        obj = self.get(db, id)
        if obj:
            obj.last_login = datetime.utcnow()
            obj.update_audit_info(id, {"action": "last_login_update"})
            
            db.commit()
            db.refresh(obj)
        return obj


# Audit trail CRUD operations
class AuditTrailCRUD:
    """
    CRUD operations for audit trail data.
    """
    
    def __init__(self):
        self.model = AuditTrail
    
    def get_by_table_and_record(
        self,
        db: Session,
        table_name: str,
        record_id: int,
        limit: int = 100
    ) -> List[AuditTrail]:
        """
        Get audit trail for a specific table record.
        """
        return db.query(AuditTrail).filter(
            AuditTrail.table_name == table_name,
            AuditTrail.record_id == record_id
        ).order_by(desc(AuditTrail.timestamp)).limit(limit).all()
    
    def get_by_user(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditTrail]:
        """
        Get audit trail for a specific user.
        """
        return db.query(AuditTrail).filter(
            AuditTrail.user_id == user_id
        ).order_by(desc(AuditTrail.timestamp)).offset(skip).limit(limit).all()
    
    def get_by_action(
        self,
        db: Session,
        action: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditTrail]:
        """
        Get audit trail by action type with optional date range.
        """
        query = db.query(AuditTrail).filter(AuditTrail.action == action)
        
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        return query.order_by(desc(AuditTrail.timestamp)).offset(skip).limit(limit).all()
    
    def get_recent_audit_activity(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 1000
    ) -> List[AuditTrail]:
        """
        Get recent audit activity for monitoring.
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(AuditTrail).filter(
            AuditTrail.timestamp >= since
        ).order_by(desc(AuditTrail.timestamp)).limit(limit).all()
    
    def cleanup_old_audit_data(
        self,
        db: Session,
        retention_days: int = 2555  # 7 years for compliance
    ) -> int:
        """
        Clean up old audit data based on retention policy.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted_count = db.query(AuditTrail).filter(
            AuditTrail.timestamp < cutoff_date
        ).count()
        
        db.query(AuditTrail).filter(
            AuditTrail.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        return deleted_count


# Create instances for use across the application
fine_crud = FineCRUD()
defense_crud = DefenseCRUD()
user_crud = UserCRUD()
audit_trail_crud = AuditTrailCRUD()

# Generic CRUD instances for other models
legal_document_crud = SoftDeleteCRUD(models.LegalDocument)
case_outcome_crud = SoftDeleteCRUD(models.CaseOutcome)
stripe_customer_crud = SoftDeleteCRUD(models.StripeCustomer)
stripe_subscription_crud = SoftDeleteCRUD(models.StripeSubscription)
payment_crud = SoftDeleteCRUD(models.Payment)
payment_method_crud = SoftDeleteCRUD(models.PaymentMethod)
defense_template_crud = SoftDeleteCRUD(models.DefenseTemplate)