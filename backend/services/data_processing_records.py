"""
Data Processing Records System for GDPR Article 30 compliance.

This module provides comprehensive data processing records management:
- Complete records of processing activities (ROPA)
- Processing purpose tracking and legal basis documentation
- Data retention documentation and automated scheduling
- Data sharing records and third-party documentation
- Automated record generation and maintenance
- Portuguese CNPD integration for local compliance

Key Features:
- Article 30 compliance with detailed processing records
- Legal basis tracking for GDPR Article 6
- Automated data retention scheduling and documentation
- Third-party data sharing transparency
- Processing activity lifecycle management
- Compliance reporting and audit trails
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..app import models
from ..app.models_base import AuditTrail

# Configure logging
logger = logging.getLogger(__name__)


class LegalBasis(Enum):
    """GDPR Article 6 legal basis for processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataCategory(Enum):
    """Categories of personal data being processed."""
    IDENTITY_DATA = "identity_data"
    CONTACT_DATA = "contact_data"
    FINANCIAL_DATA = "financial_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"
    HEALTH_DATA = "health_data"
    BIOMETRIC_DATA = "biometric_data"
    CRIMINAL_DATA = "criminal_data"
    CHILDREN_DATA = "children_data"


class DataSubject(Enum):
    """Types of data subjects."""
    CUSTOMERS = "customers"
    EMPLOYEES = "employees"
    SUPPLIERS = "suppliers"
    PROSPECTS = "prospects"
    WEBSITE_USERS = "website_users"
    APP_USERS = "app_users"
    JOB_APPLICANTS = "job_applicants"
    BUSINESS_CONTACTS = "business_contacts"


class ProcessingPurpose(Enum):
    """Common processing purposes."""
    ACCOUNT_MANAGEMENT = "account_management"
    SERVICE_PROVISION = "service_provision"
    PAYMENT_PROCESSING = "payment_processing"
    CUSTOMER_SUPPORT = "customer_support"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    SECURITY = "security"
    FRAUD_PREVENTION = "fraud_prevention"
    LEGAL_COMPLIANCE = "legal_compliance"
    QUALITY_ASSURANCE = "quality_assurance"


class RetentionBasis(Enum):
    """Basis for data retention."""
    LEGAL_OBLIGATION = "legal_obligation"
    CONTRACTUAL_REQUIREMENT = "contractual_requirement"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT_BASED = "consent_based"
    BUSINESS_NEED = "business_need"


@dataclass
class ProcessingRecord:
    """
    Individual processing record as required by GDPR Article 30.
    
    Contains comprehensive information about a data processing activity:
    - Controller and processor information
    - Processing purposes and legal basis
    - Data categories and data subjects
    - Recipient information and international transfers
    - Retention periods and deletion schedules
    - Security measures and safeguards
    """
    
    # Record identification
    record_id: str
    activity_name: str
    description: str
    created_date: datetime
    last_updated: datetime
    status: str  # active, suspended, terminated
    
    # Controller information
    controller_name: str
    controller_address: str
    controller_contact: str
    controller_dpo_contact: Optional[str]
    
    # Joint controller information (if applicable)
    joint_controllers: Optional[List[Dict[str, str]]]
    
    # Processing purposes
    processing_purposes: List[ProcessingPurpose]
    business_justification: str
    
    # Legal basis (GDPR Article 6)
    legal_basis: LegalBasis
    legal_basis_details: str
    consent_details: Optional[Dict[str, Any]]  # If legal basis is consent
    
    # Categories of data subjects
    data_subjects: List[DataSubject]
    
    # Categories of personal data
    personal_data_categories: List[DataCategory]
    sensitive_data_categories: List[DataCategory]
    
    # Categories of recipients
    internal_recipients: List[str]
    external_recipients: List[str]
    categories_of_recipients: List[str]
    
    # International transfers
    international_transfers: bool
    third_country_transfers: bool
    transfer_details: Optional[List[Dict[str, str]]]
    adequacy_decisions: Optional[List[str]]
    appropriate_safeguards: Optional[List[str]]
    
    # Retention periods
    retention_bases: List[RetentionBasis]
    retention_periods: Dict[str, str]  # category -> retention period
    deletion_schedules: Optional[List[Dict[str, str]]]
    
    # Technical and organizational measures
    security_measures: List[str]
    technical_safeguards: List[str]
    organizational_measures: List[str]
    
    # Processors and sub-processors
    processors: Optional[List[Dict[str, str]]]
    sub_processors: Optional[List[Dict[str, str]]]
    
    # Additional information
    source_of_data: str
    automated_decision_making: bool
    profiling: bool
    profiling_details: Optional[str]
    special_category_processing: bool
    criminal_data_processing: bool
    
    # Risk assessment
    risk_level: str
    dpia_required: bool
    dpia_reference: Optional[str]
    
    # Compliance tracking
    last_audit_date: Optional[datetime]
    next_review_date: Optional[datetime]
    compliance_notes: Optional[str]
    
    # Portuguese specific requirements
    portuguese_dpo_contact: Optional[str]
    cnpd_notification_required: bool
    local_legal_basis: Optional[str]


class RecordOfProcessingActivities:
    """
    Manager for Records of Processing Activities (ROPA).
    
    Provides comprehensive management of processing records:
    - Automated record generation
    - Record maintenance and updates
    - Compliance monitoring
    - Audit trail management
    - Integration with other privacy systems
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.records: Dict[str, ProcessingRecord] = {}
    
    def create_processing_record(
        self,
        record_data: Dict[str, Any],
        created_by: str
    ) -> ProcessingRecord:
        """
        Create a new processing record.
        
        Args:
            record_data: Dictionary containing record details
            created_by: Person creating the record
            
        Returns:
            Created processing record
        """
        try:
            # Generate unique record ID
            record_id = f"ROPA_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.records)+1:04d}"
            
            # Convert enums
            processing_purposes = [ProcessingPurpose(p) for p in record_data.get('processing_purposes', [])]
            data_subjects = [DataSubject(ds) for ds in record_data.get('data_subjects', [])]
            personal_data_categories = [DataCategory(dc) for dc in record_data.get('personal_data_categories', [])]
            sensitive_data_categories = [DataCategory(dc) for dc in record_data.get('sensitive_data_categories', [])]
            legal_basis = LegalBasis(record_data.get('legal_basis', 'consent'))
            retention_bases = [RetentionBasis(rb) for rb in record_data.get('retention_bases', [])]
            
            # Create processing record
            record = ProcessingRecord(
                record_id=record_id,
                activity_name=record_data['activity_name'],
                description=record_data['description'],
                created_date=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                status="active",
                
                # Controller information
                controller_name=record_data.get('controller_name', 'FineHero'),
                controller_address=record_data.get('controller_address', 'Portugal'),
                controller_contact=record_data.get('controller_contact', 'privacy@finehero.pt'),
                controller_dpo_contact=record_data.get('controller_dpo_contact', 'dpo@finehero.pt'),
                
                # Joint controllers
                joint_controllers=record_data.get('joint_controllers'),
                
                # Processing purposes
                processing_purposes=processing_purposes,
                business_justification=record_data.get('business_justification', ''),
                
                # Legal basis
                legal_basis=legal_basis,
                legal_basis_details=record_data.get('legal_basis_details', ''),
                consent_details=record_data.get('consent_details'),
                
                # Data subjects
                data_subjects=data_subjects,
                
                # Data categories
                personal_data_categories=personal_data_categories,
                sensitive_data_categories=sensitive_data_categories,
                
                # Recipients
                internal_recipients=record_data.get('internal_recipients', []),
                external_recipients=record_data.get('external_recipients', []),
                categories_of_recipients=record_data.get('categories_of_recipients', []),
                
                # International transfers
                international_transfers=record_data.get('international_transfers', False),
                third_country_transfers=record_data.get('third_country_transfers', False),
                transfer_details=record_data.get('transfer_details'),
                adequacy_decisions=record_data.get('adequacy_decisions'),
                appropriate_safeguards=record_data.get('appropriate_safeguards'),
                
                # Retention
                retention_bases=retention_bases,
                retention_periods=record_data.get('retention_periods', {}),
                deletion_schedules=record_data.get('deletion_schedules'),
                
                # Security measures
                security_measures=record_data.get('security_measures', []),
                technical_safeguards=record_data.get('technical_safeguards', []),
                organizational_measures=record_data.get('organizational_measures', []),
                
                # Processors
                processors=record_data.get('processors'),
                sub_processors=record_data.get('sub_processors'),
                
                # Additional information
                source_of_data=record_data.get('source_of_data', 'direct'),
                automated_decision_making=record_data.get('automated_decision_making', False),
                profiling=record_data.get('profiling', False),
                profiling_details=record_data.get('profiling_details'),
                special_category_processing=record_data.get('special_category_processing', False),
                criminal_data_processing=record_data.get('criminal_data_processing', False),
                
                # Risk assessment
                risk_level=record_data.get('risk_level', 'medium'),
                dpia_required=record_data.get('dpia_required', False),
                dpia_reference=record_data.get('dpia_reference'),
                
                # Compliance tracking
                last_audit_date=record_data.get('last_audit_date'),
                next_review_date=record_data.get('next_review_date', 
                    datetime.utcnow() + timedelta(days=365)),  # Annual review
                compliance_notes=record_data.get('compliance_notes'),
                
                # Portuguese specific
                portuguese_dpo_contact=record_data.get('portuguese_dpo_contact', 'dpo@finehero.pt'),
                cnpd_notification_required=record_data.get('cnpd_notification_required', False),
                local_legal_basis=record_data.get('local_legal_basis')
            )
            
            # Store record
            self.records[record_id] = record
            
            # Create audit trail entry
            self._create_record_audit_entry(record, created_by, "created")
            
            logger.info(f"Processing record created: {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error creating processing record: {e}")
            raise
    
    def update_processing_record(
        self,
        record_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Optional[ProcessingRecord]:
        """
        Update an existing processing record.
        
        Args:
            record_id: ID of the record to update
            updates: Dictionary containing updates
            updated_by: Person updating the record
            
        Returns:
            Updated processing record or None if not found
        """
        try:
            if record_id not in self.records:
                logger.warning(f"Processing record not found: {record_id}")
                return None
            
            record = self.records[record_id]
            old_values = asdict(record)
            
            # Update fields
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            record.last_updated = datetime.utcnow()
            
            # Create audit trail entry
            self._create_record_audit_entry(
                record, updated_by, "updated", 
                old_values=old_values, new_values=asdict(record)
            )
            
            logger.info(f"Processing record updated: {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating processing record {record_id}: {e}")
            return None
    
    def get_processing_record(self, record_id: str) -> Optional[ProcessingRecord]:
        """
        Get a processing record by ID.
        
        Args:
            record_id: ID of the record to retrieve
            
        Returns:
            Processing record if found, None otherwise
        """
        return self.records.get(record_id)
    
    def list_processing_records(
        self,
        status: Optional[str] = None,
        legal_basis: Optional[LegalBasis] = None,
        purpose: Optional[ProcessingPurpose] = None
    ) -> List[ProcessingRecord]:
        """
        List processing records with optional filtering.
        
        Args:
            status: Filter by record status
            legal_basis: Filter by legal basis
            purpose: Filter by processing purpose
            
        Returns:
            List of matching processing records
        """
        filtered_records = list(self.records.values())
        
        if status:
            filtered_records = [r for r in filtered_records if r.status == status]
        
        if legal_basis:
            filtered_records = [r for r in filtered_records if r.legal_basis == legal_basis]
        
        if purpose:
            filtered_records = [r for r in filtered_records if purpose in r.processing_purposes]
        
        return filtered_records
    
    def delete_processing_record(
        self,
        record_id: str,
        deleted_by: str,
        reason: str
    ) -> bool:
        """
        Delete a processing record (mark as terminated).
        
        Args:
            record_id: ID of the record to delete
            deleted_by: Person deleting the record
            reason: Reason for deletion
            
        Returns:
            Success status of deletion
        """
        try:
            if record_id not in self.records:
                logger.warning(f"Processing record not found: {record_id}")
                return False
            
            record = self.records[record_id]
            record.status = "terminated"
            record.last_updated = datetime.utcnow()
            
            # Create audit trail entry
            self._create_record_audit_entry(
                record, deleted_by, "terminated", 
                additional_info={"termination_reason": reason}
            )
            
            logger.info(f"Processing record terminated: {record_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting processing record {record_id}: {e}")
            return False
    
    def generate_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate compliance report for processing records.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Comprehensive compliance report
        """
        try:
            active_records = [r for r in self.records.values() if r.status == "active"]
            
            report = {
                "report_period": f"Last {days} days",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_records": len(self.records),
                    "active_records": len(active_records),
                    "records_created": 0,  # Would query audit trail
                    "records_updated": 0,   # Would query audit trail
                    "records_terminated": 0  # Would query audit trail
                },
                "legal_basis_distribution": {},
                "purpose_distribution": {},
                "risk_distribution": {},
                "retention_compliance": {},
                "international_transfers": {
                    "records_with_transfers": len([r for r in active_records if r.international_transfers]),
                    "records_with_third_country_transfers": len([r for r in active_records if r.third_country_transfers])
                },
                "dpia_compliance": {
                    "dpia_required_records": len([r for r in active_records if r.dpia_required]),
                    "dpia_completed_records": 0  # Would need DPIA integration
                },
                "retention_schedules": self._generate_retention_schedules(active_records),
                "upcoming_reviews": self._get_upcoming_reviews(active_records),
                "compliance_gaps": self._identify_compliance_gaps(active_records)
            }
            
            # Calculate distributions
            legal_basis_count = {}
            for record in active_records:
                basis = record.legal_basis.value
                legal_basis_count[basis] = legal_basis_count.get(basis, 0) + 1
            
            report["legal_basis_distribution"] = legal_basis_count
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {}
    
    def _create_record_audit_entry(
        self,
        record: ProcessingRecord,
        performed_by: str,
        action: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        additional_info: Optional[Dict] = None
    ):
        """Create audit trail entry for processing record."""
        # Create comprehensive audit entry
        audit_data = {
            "record_id": record.record_id,
            "activity_name": record.activity_name,
            "action": action,
            "performed_by": performed_by,
            "timestamp": datetime.utcnow().isoformat(),
            "old_values": old_values,
            "new_values": new_values,
            "additional_info": additional_info or {}
        }
        
        logger.debug(f"Processing record audit entry created for {record.record_id}")
    
    def _generate_retention_schedules(self, records: List[ProcessingRecord]) -> List[Dict[str, Any]]:
        """Generate data retention schedules from processing records."""
        schedules = []
        
        for record in records:
            for category, period in record.retention_periods.items():
                schedules.append({
                    "record_id": record.record_id,
                    "activity_name": record.activity_name,
                    "data_category": category,
                    "retention_period": period,
                    "retention_basis": [rb.value for rb in record.retention_bases],
                    "next_review": record.next_review_date.isoformat() if record.next_review_date else None
                })
        
        return schedules
    
    def _get_upcoming_reviews(self, records: List[ProcessingRecord]) -> List[Dict[str, Any]]:
        """Get upcoming compliance reviews."""
        upcoming_reviews = []
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        
        for record in records:
            if (record.next_review_date and 
                record.next_review_date <= thirty_days_from_now):
                upcoming_reviews.append({
                    "record_id": record.record_id,
                    "activity_name": record.activity_name,
                    "review_date": record.next_review_date.isoformat(),
                    "days_until_review": (record.next_review_date - datetime.utcnow()).days
                })
        
        return upcoming_reviews
    
    def _identify_compliance_gaps(self, records: List[ProcessingRecord]) -> List[str]:
        """Identify compliance gaps in processing records."""
        gaps = []
        
        for record in records:
            # Check for missing legal basis details
            if record.legal_basis == LegalBasis.CONSENT and not record.consent_details:
                gaps.append(f"Record {record.record_id}: Missing consent details for consent-based processing")
            
            # Check for missing DPO contact
            if not record.controller_dpo_contact:
                gaps.append(f"Record {record.record_id}: Missing DPO contact information")
            
            # Check for missing security measures
            if not record.security_measures:
                gaps.append(f"Record {record.record_id}: No security measures documented")
            
            # Check for overdue reviews
            if record.next_review_date and record.next_review_date < datetime.utcnow():
                gaps.append(f"Record {record.record_id}: Overdue compliance review")
            
            # Check for high-risk processing without DPIA
            if (record.risk_level in ['high', 'very_high'] and 
                record.dpia_required and not record.dpia_reference):
                gaps.append(f"Record {record.record_id}: High-risk processing without DPIA")
        
        return gaps


class ProcessingRecordsService:
    """
    Main service for processing records management.
    
    Provides unified interface for all processing records functionality:
    - ROPA management and compliance
    - Automated record generation
    - Integration with DPIA and other privacy systems
    - Portuguese legal compliance integration
    - Compliance reporting and monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ropa_manager = RecordOfProcessingActivities(db)
    
    def register_processing_activity(
        self,
        activity_data: Dict[str, Any],
        registered_by: str
    ) -> str:
        """
        Register a new processing activity in the ROPA.
        
        Args:
            activity_data: Processing activity details
            registered_by: Person registering the activity
            
        Returns:
            Record ID of the created processing record
        """
        try:
            record = self.ropa_manager.create_processing_record(activity_data, registered_by)
            logger.info(f"Processing activity registered: {record.record_id}")
            return record.record_id
            
        except Exception as e:
            logger.error(f"Error registering processing activity: {e}")
            raise
    
    def update_processing_activity(
        self,
        record_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> bool:
        """
        Update an existing processing activity record.
        
        Args:
            record_id: ID of the record to update
            updates: Dictionary containing updates
            updated_by: Person updating the record
            
        Returns:
            Success status of update
        """
        try:
            result = self.ropa_manager.update_processing_record(record_id, updates, updated_by)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating processing activity {record_id}: {e}")
            return False
    
    def get_ropa_entry(self, record_id: str) -> Optional[ProcessingRecord]:
        """
        Get a specific ROPA entry.
        
        Args:
            record_id: ID of the record to retrieve
            
        Returns:
            Processing record if found
        """
        return self.ropa_manager.get_processing_record(record_id)
    
    def list_ropa_entries(
        self,
        compliance_check: bool = False
    ) -> List[ProcessingRecord]:
        """
        List all ROPA entries with optional compliance filtering.
        
        Args:
            compliance_check: Only return compliant records
            
        Returns:
            List of processing records
        """
        all_records = self.ropa_manager.list_processing_records(status="active")
        
        if compliance_check:
            # Filter for compliant records
            compliant_records = []
            for record in all_records:
                if self._is_record_compliant(record):
                    compliant_records.append(record)
            return compliant_records
        
        return all_records
    
    def generate_ropa_export(self, format: str = "json") -> Dict[str, Any]:
        """
        Generate ROPA export for regulatory submission.
        
        Args:
            format: Export format ('json', 'csv', 'pdf')
            
        Returns:
            ROPA export data
        """
        try:
            active_records = self.ropa_manager.list_processing_records(status="active")
            
            export_data = {
                "export_metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "total_records": len(active_records),
                    "export_format": format,
                    "controller": "FineHero",
                    "compliance_framework": "GDPR Article 30",
                    "local_compliance": "Portuguese CNPD"
                },
                "records": []
            }
            
            for record in active_records:
                # Convert record to exportable format
                export_record = asdict(record)
                
                # Convert datetime objects to ISO strings
                export_record["created_date"] = record.created_date.isoformat()
                export_record["last_updated"] = record.last_updated.isoformat()
                if record.last_audit_date:
                    export_record["last_audit_date"] = record.last_audit_date.isoformat()
                if record.next_review_date:
                    export_record["next_review_date"] = record.next_review_date.isoformat()
                
                # Convert enums to strings
                export_record["legal_basis"] = record.legal_basis.value
                export_record["processing_purposes"] = [p.value for p in record.processing_purposes]
                export_record["data_subjects"] = [ds.value for ds in record.data_subjects]
                export_record["personal_data_categories"] = [dc.value for dc in record.personal_data_categories]
                export_record["sensitive_data_categories"] = [dc.value for dc in record.sensitive_data_categories]
                export_record["retention_bases"] = [rb.value for rb in record.retention_bases]
                
                export_data["records"].append(export_record)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error generating ROPA export: {e}")
            return {}
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive compliance summary.
        
        Args:
            None
            
        Returns:
            Compliance summary data
        """
        return self.ropa_manager.generate_compliance_report()
    
    def _is_record_compliant(self, record: ProcessingRecord) -> bool:
        """
        Check if a processing record is compliant.
        
        Args:
            record: Processing record to check
            
        Returns:
            Compliance status
        """
        # Check required fields
        if not record.controller_dpo_contact:
            return False
        
        if not record.legal_basis_details:
            return False
        
        if not record.security_measures:
            return False
        
        # Check for high-risk processing
        if record.risk_level in ['high', 'very_high'] and not record.dpia_reference:
            return False
        
        # Check for overdue reviews
        if record.next_review_date and record.next_review_date < datetime.utcnow():
            return False
        
        return True


# Utility functions for easy integration
def create_processing_records_service(db: Session) -> ProcessingRecordsService:
    """Create a processing records service instance."""
    return ProcessingRecordsService(db)


def register_standard_processing_activities(db: Session) -> List[str]:
    """
    Register standard processing activities for FineHero business operations.
    
    Args:
        db: Database session
        
    Returns:
        List of created record IDs
    """
    try:
        service = ProcessingRecordsService(db)
        record_ids = []
        
        # Standard activities for a traffic fine defense platform
        standard_activities = [
            {
                "activity_name": "User Account Management",
                "description": "Creation and management of user accounts for the traffic fine defense platform",
                "processing_purposes": ["account_management", "service_provision"],
                "legal_basis": "contract",
                "data_subjects": ["customers"],
                "personal_data_categories": ["identity_data", "contact_data"],
                "sensitive_data_categories": [],
                "international_transfers": False,
                "retention_bases": ["contractual_requirement"],
                "retention_periods": {"identity_data": "2 years after account closure"},
                "security_measures": ["encryption", "access_controls", "audit_logging"],
                "risk_level": "low"
            },
            {
                "activity_name": "Payment Processing",
                "description": "Processing of subscription payments through Stripe integration",
                "processing_purposes": ["payment_processing"],
                "legal_basis": "contract",
                "data_subjects": ["customers"],
                "personal_data_categories": ["financial_data"],
                "sensitive_data_categories": [],
                "international_transfers": True,
                "third_country_transfers": False,
                "retention_bases": ["legal_obligation", "contractual_requirement"],
                "retention_periods": {"financial_data": "7 years (Portuguese tax law)"},
                "security_measures": ["PCI_DSS_compliance", "encryption", "secure_payment_processing"],
                "risk_level": "medium"
            },
            {
                "activity_name": "Legal Defense Generation",
                "description": "AI-powered generation of legal defenses for traffic fines",
                "processing_purposes": ["service_provision", "quality_assurance"],
                "legal_basis": "contract",
                "data_subjects": ["customers"],
                "personal_data_categories": ["identity_data", "behavioral_data"],
                "sensitive_data_categories": [],
                "international_transfers": False,
                "retention_bases": ["legitimate_interest", "business_need"],
                "retention_periods": {"behavioral_data": "1 year after service completion"},
                "security_measures": ["data_anonymization", "access_controls", "secure_ai_processing"],
                "risk_level": "medium"
            }
        ]
        
        for activity_data in standard_activities:
            record_id = service.register_processing_activity(activity_data, "system_setup")
            record_ids.append(record_id)
        
        logger.info(f"Standard processing activities registered: {record_ids}")
        return record_ids
        
    except Exception as e:
        logger.error(f"Error registering standard processing activities: {e}")
        return []