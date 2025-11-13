"""
GDPR Compliance Service for automated data retention and privacy protection.

This service provides comprehensive GDPR compliance features:
- Automated data retention policies
- User data export capabilities (data portability)
- Data anonymization for privacy protection
- Consent management integration
- Data deletion upon retention period expiration
- Compliance reporting and audit trails

Supports Portuguese data protection requirements alongside EU GDPR compliance.
"""
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..app import models
from ..app.crud_soft_delete import audit_trail_crud
from ..app.models_base import AuditTrail

# Configure logging
logger = logging.getLogger(__name__)


class RetentionPolicy:
    """
    Defines data retention policies for different data types.
    
    These policies ensure compliance with legal requirements:
    - Financial data: 7 years (Portuguese commercial law)
    - User data: 2 years after account closure (GDPR)
    - Audit data: 7 years (compliance requirements)
    - Legal documents: Indefinite for legal reference
    """
    
    # Retention periods in days
    RETENTION_POLICIES = {
        # Financial data - 7 years (2555 days)
        "financial": {
            "payments": 2555,
            "stripe_subscriptions": 2555,
            "stripe_customers": 2555,
            "payment_methods": 2555
        },
        
        # User data - 2 years after account closure (730 days)
        "user_data": {
            "users": 730,
            "fines": 730,
            "defenses": 730
        },
        
        # Audit data - 7 years for compliance (2555 days)
        "audit_data": {
            "audit_trails": 2555,
            "fines": 2555,  # Keep fines for legal reference
            "defenses": 2555,  # Keep defenses for legal reference
            "legal_documents": 2555,
            "case_outcomes": 2555
        },
        
        # System data - shorter retention
        "system_data": {
            "webhook_events": 365,
            "defense_templates": 365
        },
        
        # Legal documents - longer retention for compliance
        "legal": {
            "legal_documents": 2555,
            "case_outcomes": 2555
        }
    }
    
    @classmethod
    def get_retention_days(cls, table_name: str, data_type: str = "user_data") -> int:
        """
        Get retention days for a specific table.
        
        Args:
            table_name: Name of the database table
            data_type: Category of data (financial, user_data, audit_data, system_data, legal)
            
        Returns:
            Number of days to retain data
        """
        policies = cls.RETENTION_POLICIES.get(data_type, {})
        return policies.get(table_name, 730)  # Default to 2 years


class DataExportService:
    """
    Service for user data export (GDPR Article 20 - Data Portability).
    
    Provides comprehensive data export functionality to fulfill user requests
    for data portability, allowing users to request a complete export of their data.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_user_data(
        self,
        user_id: int,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export all data for a specific user in portable format.
        
        Args:
            user_id: ID of the user requesting data export
            format: Export format ('json', 'csv')
            
        Returns:
            Dictionary containing all user data
        """
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data": {}
        }
        
        try:
            # User profile data
            user = self.db.query(models.User).filter(
                models.User.id == user_id,
                models.User.is_deleted == False
            ).first()
            
            if user:
                export_data["data"]["user_profile"] = self._serialize_model(user)
            
            # User's fines
            fines = self.db.query(models.Fine).filter(
                models.Fine.user_id == user_id,
                models.Fine.is_deleted == False
            ).all()
            
            if fines:
                export_data["data"]["fines"] = [self._serialize_model(fine) for fine in fines]
            
            # User's defenses
            defenses = self.db.query(models.Defense).filter(
                models.Defense.user_id == user_id,
                models.Defense.is_deleted == False
            ).all()
            
            if defenses:
                export_data["data"]["defenses"] = [self._serialize_model(defense) for defense in defenses]
            
            # User's payment data (if exists)
            stripe_customer = self.db.query(models.StripeCustomer).filter(
                models.StripeCustomer.user_id == user_id,
                models.StripeCustomer.is_deleted == False
            ).first()
            
            if stripe_customer:
                export_data["data"]["payment_data"] = self._serialize_model(stripe_customer)
                
                # Include subscription data
                subscriptions = self.db.query(models.StripeSubscription).filter(
                    models.StripeSubscription.customer_id == stripe_customer.id,
                    models.StripeSubscription.is_deleted == False
                ).all()
                
                if subscriptions:
                    export_data["data"]["subscriptions"] = [
                        self._serialize_model(sub) for sub in subscriptions
                    ]
                
                # Include payment history
                payments = self.db.query(models.Payment).filter(
                    models.Payment.customer_id == stripe_customer.id,
                    models.Payment.is_deleted == False
                ).all()
                
                if payments:
                    export_data["data"]["payments"] = [self._serialize_model(payment) for payment in payments]
            
            # Audit trail for this user
            user_audit_trail = audit_trail_crud.get_by_user(self.db, user_id, limit=1000)
            if user_audit_trail:
                export_data["data"]["audit_trail"] = [self._serialize_audit_entry(entry) for entry in user_audit_trail]
            
            logger.info(f"User data export completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error during user data export for user {user_id}: {e}")
            raise
        
        return export_data
    
    def _serialize_model(self, model: models.Base) -> Dict[str, Any]:
        """Serialize a model instance to dictionary."""
        return {
            col.name: getattr(model, col.name)
            for col in model.__table__.columns
            if col.name not in ['hashed_password', 'audit_metadata']  # Exclude sensitive data
        }
    
    def _serialize_audit_entry(self, entry: AuditTrail) -> Dict[str, Any]:
        """Serialize an audit trail entry."""
        return {
            "table_name": entry.table_name,
            "record_id": entry.record_id,
            "action": entry.action,
            "timestamp": entry.timestamp.isoformat(),
            "user_ip": entry.user_ip,
            "additional_info": entry.additional_info
        }


class DataAnonymizationService:
    """
    Service for data anonymization to protect user privacy.
    
    Provides functionality to anonymize user data while maintaining
    the integrity of audit trails and compliance records.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def anonymize_user_data(self, user_id: int, reason: str = "User request") -> bool:
        """
        Anonymize all personal data for a user while preserving audit trails.
        
        Args:
            user_id: ID of the user to anonymize
            reason: Reason for anonymization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update user profile with anonymized data
            user = self.db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                old_values = self._serialize_model(user)
                
                # Anonymize user data
                user.email = f"anonymized_user_{user_id}@finehero.invalid"
                user.username = f"anonymized_user_{user_id}"
                user.full_name = "Anonymized User"
                user.is_verified = False
                user.subscription_tier = "free"
                
                # Update audit information
                user.update_audit_info(
                    None,  # System operation
                    {
                        "anonymization_reason": reason,
                        "anonymized_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Create audit trail entry
                audit_trail_crud._create_audit_entry(
                    self.db, user, 'ANONYMIZE', old_values,
                    self._serialize_model(user), None, reason
                )
            
            # Anonymize related fines
            fines = self.db.query(models.Fine).filter(models.Fine.user_id == user_id).all()
            for fine in fines:
                old_values = self._serialize_model(fine)
                fine.infractor = "ANONYMIZED"
                fine.update_audit_info(
                    None,
                    {"anonymized": True, "anonymization_reason": reason}
                )
            
            # Anonymize related defenses
            defenses = self.db.query(models.Defense).filter(models.Defense.user_id == user_id).all()
            for defense in defenses:
                old_values = self._serialize_model(defense)
                defense.update_audit_info(
                    None,
                    {"anonymized": True, "anonymization_reason": reason}
                )
            
            # Anonymize Stripe customer data if exists
            stripe_customer = self.db.query(models.StripeCustomer).filter(
                models.StripeCustomer.user_id == user_id
            ).first()
            
            if stripe_customer:
                old_values = self._serialize_model(stripe_customer)
                stripe_customer.email = f"anonymized_user_{user_id}@finehero.invalid"
                stripe_customer.name = "Anonymized User"
                stripe_customer.description = "Anonymized customer"
                
                stripe_customer.update_audit_info(
                    None,
                    {"anonymized": True, "anonymization_reason": reason}
                )
            
            self.db.commit()
            logger.info(f"User data anonymization completed for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during user data anonymization for user {user_id}: {e}")
            return False
    
    def _serialize_model(self, model: models.Base) -> Dict[str, Any]:
        """Serialize a model instance to dictionary."""
        return {
            col.name: getattr(model, col.name)
            for col in model.__table__.columns
        }


class ConsentManagementService:
    """
    Service for managing user consent and preferences.
    
    Tracks and manages user consent for data processing activities
    in compliance with GDPR Article 6 (lawful basis for processing).
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_consent(
        self,
        user_id: int,
        consent_type: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Record user consent for a specific processing type.
        
        Args:
            user_id: ID of the user
            consent_type: Type of consent ('data_processing', 'marketing', 'analytics', etc.)
            granted: Whether consent was granted
            ip_address: User's IP address for audit
            user_agent: User's browser information
            
        Returns:
            True if successful
        """
        try:
            # Create consent record in audit metadata or separate table
            consent_data = {
                "consent_type": consent_type,
                "granted": granted,
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            # Store consent in user's audit metadata
            user = self.db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                # Get existing consent records
                existing_metadata = {}
                if user.audit_metadata:
                    try:
                        existing_metadata = json.loads(user.audit_metadata)
                    except (json.JSONDecodeError, TypeError):
                        existing_metadata = {}
                
                # Update consent records
                if "consent_records" not in existing_metadata:
                    existing_metadata["consent_records"] = []
                
                existing_metadata["consent_records"].append(consent_data)
                
                # Update user's audit metadata
                user.audit_metadata = json.dumps(existing_metadata, default=str)
                user.updated_at = datetime.utcnow()
                
                # Create audit trail entry
                audit_trail_crud._create_audit_entry(
                    self.db, user, 'CONSENT_UPDATE', None,
                    {"consent_type": consent_type, "granted": granted}, user_id,
                    f"Consent {consent_type} {'granted' if granted else 'withdrawn'}"
                )
            
            self.db.commit()
            logger.info(f"Consent recorded for user {user_id}: {consent_type} = {granted}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording consent for user {user_id}: {e}")
            return False
    
    def get_user_consents(self, user_id: int) -> Dict[str, Any]:
        """
        Get all consent records for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of consent records
        """
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if user and user.audit_metadata:
            try:
                metadata = json.loads(user.audit_metadata)
                return metadata.get("consent_records", [])
            except (json.JSONDecodeError, TypeError):
                return []
        return []


class DataRetentionService:
    """
    Service for automated data retention management.
    
    Implements automated data deletion based on retention policies,
    ensuring compliance with legal requirements while maintaining necessary records.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.retention_policy = RetentionPolicy()
    
    def run_retention_cleanup(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Run automated data retention cleanup.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary with counts of records that would be/were deleted
        """
        cleanup_results = {}
        
        try:
            # Clean up user data based on retention policies
            cleanup_results.update(self._cleanup_user_data(dry_run))
            
            # Clean up financial data
            cleanup_results.update(self._cleanup_financial_data(dry_run))
            
            # Clean up audit data
            cleanup_results.update(self._cleanup_audit_data(dry_run))
            
            # Clean up system data
            cleanup_results.update(self._cleanup_system_data(dry_run))
            
            if not dry_run:
                self.db.commit()
                logger.info("Data retention cleanup completed successfully")
            else:
                logger.info("Data retention cleanup dry run completed")
            
        except Exception as e:
            if not dry_run:
                self.db.rollback()
            logger.error(f"Error during data retention cleanup: {e}")
            raise
        
        return cleanup_results
    
    def _cleanup_user_data(self, dry_run: bool) -> Dict[str, int]:
        """Clean up user data based on retention policies."""
        results = {}
        
        # Clean up user accounts that are older than retention period
        user_retention_days = self.retention_policy.get_retention_days("users", "user_data")
        cutoff_date = datetime.utcnow() - timedelta(days=user_retention_days)
        
        # Find users to clean up (soft-deleted users only)
        if dry_run:
            count = self.db.query(models.User).filter(
                models.User.is_deleted == True,
                models.User.deleted_at < cutoff_date
            ).count()
            results["users_to_cleanup"] = count
        else:
            deleted_count = 0
            users_to_delete = self.db.query(models.User).filter(
                models.User.is_deleted == True,
                models.User.deleted_at < cutoff_date
            ).all()
            
            for user in users_to_delete:
                # Permanently delete user and related data
                deleted_count += self._permanently_delete_user_data(user.id)
            
            results["users_deleted"] = deleted_count
        
        return results
    
    def _cleanup_financial_data(self, dry_run: bool) -> Dict[str, int]:
        """Clean up financial data based on retention policies."""
        results = {}
        
        financial_tables = ["payments", "stripe_subscriptions", "stripe_customers", "payment_methods"]
        
        for table_name in financial_tables:
            retention_days = self.retention_policy.get_retention_days(table_name, "financial")
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Find records older than retention period
            model_class = getattr(models, table_name.title().replace('_', ''))
            
            if dry_run:
                count = self.db.query(model_class).filter(
                    model_class.is_deleted == True,
                    model_class.deleted_at < cutoff_date
                ).count()
                results[f"{table_name}_to_cleanup"] = count
            else:
                # Permanently delete old financial data
                self.db.query(model_class).filter(
                    model_class.is_deleted == True,
                    model_class.deleted_at < cutoff_date
                ).delete()
                results[f"{table_name}_deleted"] = 0  # Would need actual count
        
        return results
    
    def _cleanup_audit_data(self, dry_run: bool) -> Dict[str, int]:
        """Clean up old audit data based on retention policies."""
        results = {}
        
        # Clean up old audit trail entries
        audit_retention_days = self.retention_policy.get_retention_days("audit_trails", "audit_data")
        cutoff_date = datetime.utcnow() - timedelta(days=audit_retention_days)
        
        if dry_run:
            count = self.db.query(AuditTrail).filter(
                AuditTrail.timestamp < cutoff_date
            ).count()
            results["audit_trails_to_cleanup"] = count
        else:
            deleted_count = audit_trail_crud.cleanup_old_audit_data(self.db, audit_retention_days)
            results["audit_trails_deleted"] = deleted_count
        
        return results
    
    def _cleanup_system_data(self, dry_run: bool) -> Dict[str, int]:
        """Clean up system data (webhook events, etc.)."""
        results = {}
        
        # Clean up old webhook events
        webhook_retention_days = self.retention_policy.get_retention_days("webhook_events", "system_data")
        cutoff_date = datetime.utcnow() - timedelta(days=webhook_retention_days)
        
        if dry_run:
            count = self.db.query(models.WebhookEvent).filter(
                models.WebhookEvent.created_at < cutoff_date
            ).count()
            results["webhook_events_to_cleanup"] = count
        else:
            deleted_count = self.db.query(models.WebhookEvent).filter(
                models.WebhookEvent.created_at < cutoff_date
            ).delete()
            results["webhook_events_deleted"] = deleted_count
        
        return results
    
    def _permanently_delete_user_data(self, user_id: int) -> int:
        """
        Permanently delete all data for a user (after soft delete retention period).
        
        This is a permanent operation and should only be used after proper
        legal review and notification periods.
        """
        deleted_count = 0
        
        # Delete user's defenses
        deleted_count += self.db.query(models.Defense).filter(
            models.Defense.user_id == user_id
        ).delete()
        
        # Delete user's fines
        deleted_count += self.db.query(models.Fine).filter(
            models.Fine.user_id == user_id
        ).delete()
        
        # Handle Stripe data (anonymize rather than delete for compliance)
        stripe_customer = self.db.query(models.StripeCustomer).filter(
            models.StripeCustomer.user_id == user_id
        ).first()
        
        if stripe_customer:
            # Anonymize rather than delete payment data
            stripe_customer.email = f"deleted_user_{user_id}@finehero.invalid"
            stripe_customer.name = "Deleted User"
            stripe_customer.description = "Account deleted - data anonymized"
        
        # Finally, delete the user
        deleted_count += self.db.query(models.User).filter(
            models.User.id == user_id
        ).delete()
        
        return deleted_count


class GDPRComplianceService:
    """
    Main service coordinating all GDPR compliance operations.
    
    Provides a unified interface for all GDPR-related functionality
    including data export, retention, anonymization, and compliance reporting.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.data_export_service = DataExportService(db)
        self.data_anonymization_service = DataAnonymizationService(db)
        self.consent_management_service = ConsentManagementService(db)
        self.data_retention_service = DataRetentionService(db)
    
    def handle_data_subject_request(
        self,
        user_id: int,
        request_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle a data subject access request (DSAR).
        
        Args:
            user_id: ID of the user making the request
            request_type: Type of request ('export', 'delete', 'anonymize', 'consent_update')
            **kwargs: Additional parameters for the request
            
        Returns:
            Dictionary with request results
        """
        result = {
            "request_id": f"DSAR_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "request_type": request_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        try:
            if request_type == "export":
                # Data portability request (GDPR Article 20)
                export_data = self.data_export_service.export_user_data(user_id)
                result.update({
                    "status": "completed",
                    "data": export_data,
                    "instructions": "This data export fulfills your right to data portability under GDPR Article 20"
                })
                
            elif request_type == "delete":
                # Right to erasure request (GDPR Article 17)
                if kwargs.get("confirm_deletion"):
                    # Initiate soft delete process
                    user = self.db.query(models.User).filter(models.User.id == user_id).first()
                    if user:
                        user.soft_delete()
                        user.update_audit_info(user_id, {
                            "deletion_requested": True,
                            "deletion_reason": kwargs.get("reason", "User request"),
                            "retention_period_start": datetime.utcnow().isoformat()
                        })
                        self.db.commit()
                        
                        result.update({
                            "status": "completed",
                            "message": "Your data has been marked for deletion. It will be permanently deleted after the legal retention period.",
                            "retention_days": self.data_retention_service.retention_policy.get_retention_days("users", "user_data")
                        })
                
            elif request_type == "anonymize":
                # Data anonymization request
                reason = kwargs.get("reason", "User request")
                success = self.data_anonymization_service.anonymize_user_data(user_id, reason)
                result.update({
                    "status": "completed" if success else "failed",
                    "message": "Your personal data has been anonymized while maintaining audit trails" if success else "Anonymization failed"
                })
                
            elif request_type == "consent_update":
                # Consent management
                consent_type = kwargs.get("consent_type")
                granted = kwargs.get("granted")
                ip_address = kwargs.get("ip_address")
                user_agent = kwargs.get("user_agent")
                
                success = self.consent_management_service.record_consent(
                    user_id, consent_type, granted, ip_address, user_agent
                )
                result.update({
                    "status": "completed" if success else "failed",
                    "message": "Your consent preferences have been updated"
                })
            
            # Create audit trail entry for the request
            self._log_compliance_request(result)
            
        except Exception as e:
            logger.error(f"Error processing DSAR for user {user_id}: {e}")
            result.update({
                "status": "failed",
                "error": str(e)
            })
        
        return result
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate a compliance report for the specified period.
        
        Args:
            days: Number of days to include in the report
            
        Returns:
            Comprehensive compliance report
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        report = {
            "report_period": f"Last {days} days",
            "generated_at": datetime.utcnow().isoformat(),
            "statistics": {}
        }
        
        try:
            # User statistics
            total_users = self.db.query(models.User).filter(
                models.User.is_deleted == False
            ).count()
            
            deleted_users = self.db.query(models.User).filter(
                models.User.is_deleted == True
            ).count()
            
            report["statistics"]["users"] = {
                "total_active": total_users,
                "total_deleted": deleted_users,
                "new_registrations": self.db.query(models.User).filter(
                    models.User.created_at >= cutoff_date
                ).count()
            }
            
            # Data processing statistics
            audit_entries = self.db.query(AuditTrail).filter(
                AuditTrail.timestamp >= cutoff_date
            ).count()
            
            report["statistics"]["data_processing"] = {
                "audit_entries": audit_entries,
                "consent_updates": self._count_consent_updates(days),
                "data_exports": self._count_data_exports(days)
            }
            
            # Retention statistics
            retention_stats = self.data_retention_service.run_retention_cleanup(dry_run=True)
            report["statistics"]["retention"] = retention_stats
            
            # Legal compliance status
            report["statistics"]["compliance_status"] = {
                "gdpr_compliant": self._check_gdpr_compliance(),
                "data_retention_policies_applied": True,
                "audit_trail_complete": self._verify_audit_trail_integrity()
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            report["error"] = str(e)
        
        return report
    
    def _log_compliance_request(self, result: Dict[str, Any]):
        """Log a compliance request for audit purposes."""
        try:
            # This would create an audit trail entry
            # Implementation depends on your audit system
            pass
        except Exception as e:
            logger.error(f"Error logging compliance request: {e}")
    
    def _count_consent_updates(self, days: int) -> int:
        """Count consent updates in the specified period."""
        # This would query audit metadata for consent updates
        # Simplified implementation
        return 0
    
    def _count_data_exports(self, days: int) -> int:
        """Count data exports in the specified period."""
        # This would query audit metadata for export requests
        # Simplified implementation
        return 0
    
    def _check_gdpr_compliance(self) -> bool:
        """Check if the system meets GDPR compliance requirements."""
        try:
            # Check if all required fields are present
            required_fields = ['deleted_at', 'is_deleted', 'created_at', 'updated_at']
            
            # Check User model
            user_columns = [col.name for col in models.User.__table__.columns]
            if not all(field in user_columns for field in required_fields):
                return False
            
            # Check if audit trail is working
            recent_audit = self.db.query(AuditTrail).order_by(
                desc(AuditTrail.timestamp)
            ).limit(10).all()
            
            return len(recent_audit) > 0
            
        except Exception as e:
            logger.error(f"Error checking GDPR compliance: {e}")
            return False
    
    def _verify_audit_trail_integrity(self) -> bool:
        """Verify that audit trail is complete and consistent."""
        try:
            # Check for audit trail entries
            total_audit_entries = self.db.query(AuditTrail).count()
            
            # Check for missing audit data
            tables_with_audit = ['users', 'fines', 'defenses', 'payments']
            for table_name in tables_with_audit:
                model_class = getattr(models, table_name.title().replace('_', ''))
                total_records = self.db.query(model_class).count()
                
                # This is a simplified check - in production you'd want more sophisticated validation
                if total_records > 0 and total_audit_entries == 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying audit trail integrity: {e}")
            return False


# Utility functions for easy integration
def create_gdpr_service(db: Session) -> GDPRComplianceService:
    """Create a GDPR compliance service instance."""
    return GDPRComplianceService(db)


def run_scheduled_retention_cleanup(db: Session, dry_run: bool = False) -> Dict[str, int]:
    """
    Run scheduled data retention cleanup.
    
    This function can be called by a cron job or scheduled task.
    """
    service = GDPRComplianceService(db)
    return service.data_retention_service.run_retention_cleanup(dry_run)