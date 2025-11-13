"""
Base mixins for soft delete and audit trail functionality.

This module provides base classes that implement soft delete capabilities
and audit trail logging for all database models.
"""
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
import json

Base = declarative_base()


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Provides soft delete capabilities by adding deleted_at and is_deleted fields.
    Records are never actually deleted from the database, only marked as deleted.
    """
    
    @declared_attr
    def deleted_at(cls):
        """Timestamp when the record was soft deleted (nullable)."""
        return Column(DateTime, nullable=True, index=True)
    
    @declared_attr 
    def is_deleted(cls):
        """Boolean flag indicating if the record has been soft deleted."""
        return Column(Boolean, default=False, index=True)
    
    def soft_delete(self, deleted_at: Optional[datetime] = None) -> None:
        """
        Soft delete this record.
        
        Args:
            deleted_at: Timestamp for deletion (defaults to current UTC time)
        """
        self.is_deleted = True
        self.deleted_at = deleted_at or datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restore a soft deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
    
    @classmethod
    def get_active_records_query(cls, db_session):
        """
        Get query for all non-deleted records.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Query filtered to exclude soft deleted records
        """
        return db_session.query(cls).filter(cls.is_deleted == False)
    
    @classmethod
    def get_deleted_records_query(cls, db_session):
        """
        Get query for all soft deleted records.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Query filtered to only include soft deleted records
        """
        return db_session.query(cls).filter(cls.is_deleted == True)


class AuditMixin:
    """
    Mixin for audit trail functionality.
    
    Provides comprehensive audit logging by tracking creation and modification
    timestamps along with user attribution for compliance and traceability.
    """
    
    @declared_attr
    def created_at(cls):
        """Timestamp when the record was created."""
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        """Timestamp when the record was last updated."""
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def created_by(cls):
        """User ID who created the record (nullable for system operations)."""
        return Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    @declared_attr
    def updated_by(cls):
        """User ID who last updated the record (nullable for system operations)."""
        return Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    @declared_attr
    def audit_metadata(cls):
        """JSON metadata for audit trail (version, changes, etc.)."""
        return Column(Text, nullable=True)
    
    # Relationships for audit trail
    creator = relationship("User", foreign_keys=[getattr(cls, 'created_by', None)], 
                          post_update=True)
    updater = relationship("User", foreign_keys=[getattr(cls, 'updated_by', None)],
                          post_update=True)
    
    def update_audit_info(self, user_id: Optional[int] = None, 
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update audit information for this record.
        
        Args:
            user_id: ID of user making the update
            metadata: Additional metadata to store in audit trail
        """
        self.updated_at = datetime.utcnow()
        if user_id:
            self.updated_by = user_id
        
        if metadata:
            current_metadata = self.audit_metadata
            if current_metadata:
                try:
                    existing_metadata = json.loads(current_metadata)
                    existing_metadata.update(metadata)
                except (json.JSONDecodeError, TypeError):
                    existing_metadata = metadata
            else:
                existing_metadata = metadata
            
            self.audit_metadata = json.dumps(existing_metadata, default=str)
    
    def create_with_audit(self, user_id: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize audit information for record creation.
        
        Args:
            user_id: ID of user creating the record
            metadata: Additional metadata for audit trail
        """
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.created_by = user_id
        self.updated_by = user_id
        
        if metadata:
            creation_metadata = {
                "created_by_user": user_id,
                "creation_timestamp": self.created_at.isoformat(),
                "additional_metadata": metadata
            }
            self.audit_metadata = json.dumps(creation_metadata, default=str)


class TimestampMixin:
    """
    Simple mixin for timestamp tracking (created_at, updated_at).
    """
    
    @declared_attr
    def created_at(cls):
        """Timestamp when the record was created."""
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        """Timestamp when the record was last updated."""
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditTrail(Base):
    """
    Dedicated audit trail table for comprehensive change tracking.
    
    Stores detailed audit information for compliance and debugging purposes.
    """
    __tablename__ = "audit_trails"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False, index=True)  # Name of the table
    record_id = Column(Integer, nullable=False, index=True)  # ID of the record
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE
    old_values = Column(Text, nullable=True)  # JSON of old values
    new_values = Column(Text, nullable=True)  # JSON of new values
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User performing action
    user_ip = Column(String, nullable=True)  # IP address of user
    user_agent = Column(Text, nullable=True)  # User agent string
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    correlation_id = Column(String, nullable=True)  # For request correlation
    additional_info = Column(Text, nullable=True)  # Additional context
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return (f"<AuditTrail(table='{self.table_name}', record_id={self.record_id}, "
                f"action='{self.action}', user_id={self.user_id}, "
                f"timestamp='{self.timestamp}')>")
    
    @classmethod
    def create_audit_entry(cls, table_name: str, record_id: int, action: str,
                          old_values: Optional[Dict] = None,
                          new_values: Optional[Dict] = None,
                          user_id: Optional[int] = None,
                          user_ip: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          correlation_id: Optional[str] = None,
                          additional_info: Optional[str] = None):
        """
        Create an audit trail entry.
        
        Args:
            table_name: Name of the database table
            record_id: ID of the affected record
            action: Type of action (CREATE, UPDATE, DELETE)
            old_values: Dictionary of old values (before change)
            new_values: Dictionary of new values (after change)
            user_id: ID of user performing the action
            user_ip: IP address of the user
            user_agent: User agent string
            correlation_id: Request correlation ID
            additional_info: Additional contextual information
        """
        return cls(
            table_name=table_name,
            record_id=record_id,
            action=action.upper(),
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent,
            correlation_id=correlation_id,
            additional_info=additional_info
        )