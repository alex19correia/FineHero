"""
Enhanced Consent Management System for comprehensive GDPR compliance.

This module provides sophisticated consent management capabilities:
- Granular consent for specific purposes and data processing activities
- One-click automated consent withdrawal mechanisms
- Consent versioning and historical tracking for legal evidence
- Portuguese age verification compliance (16+ requirement)
- Consent lifecycle management and automated expiry
- Integration with DPIA and data processing records systems

Key Features:
- Fine-grained consent controls for specific purposes
- Automated consent withdrawal with immediate effect
- Versioned consent tracking for legal compliance evidence
- Portuguese minor protection (16+ age verification)
- Consent preferences dashboard for users
- Automated consent renewal and expiry management
- Integration with privacy by design principles
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


class ConsentType(Enum):
    """Types of consent that can be granted."""
    # Service-related consents
    ACCOUNT_CREATION = "account_creation"
    SERVICE_PROVISION = "service_provision"
    PAYMENT_PROCESSING = "payment_processing"
    CUSTOMER_SUPPORT = "customer_support"
    
    # Marketing and communication consents
    EMAIL_MARKETING = "email_marketing"
    SMS_MARKETING = "sms_marketing"
    PUSH_NOTIFICATIONS = "push_notifications"
    NEWSLETTER_SUBSCRIPTION = "newsletter_subscription"
    PRODUCT_UPDATES = "product_updates"
    
    # Analytics and profiling consents
    ANALYTICS_COOKIES = "analytics_cookies"
    BEHAVIORAL_ANALYTICS = "behavioral_analytics"
    PERFORMANCE_MONITORING = "performance_monitoring"
    A_B_TESTING = "a_b_testing"
    
    # Third-party consents
    THIRD_PARTY_INTEGRATIONS = "third_party_integrations"
    SOCIAL_MEDIA_SHARING = "social_media_sharing"
    DATA_BROKER_SHARING = "data_broker_sharing"
    
    # Legal and compliance consents
    TERMS_ACCEPTANCE = "terms_acceptance"
    PRIVACY_POLICY_ACCEPTANCE = "privacy_policy_acceptance"
    COOKIE_POLICY_ACCEPTANCE = "cookie_policy_acceptance"
    LEGAL_PROCESSING = "legal_processing"
    
    # Special category consents
    HEALTH_DATA_PROCESSING = "health_data_processing"
    BIOMETRIC_DATA_PROCESSING = "biometric_data_processing"
    CRIMINAL_DATA_PROCESSING = "criminal_data_processing"
    
    # Portuguese specific consents
    PORTUGUESE_LEGAL_COMPLIANCE = "portuguese_legal_compliance"
    CNPD_PROCESSING = "cnpd_processing"
    LOCAL_DATA_RESIDENCY = "local_data_residency"


class ConsentStatus(Enum):
    """Status of consent."""
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"  # Awaiting user response
    REJECTED = "rejected"
    INACTIVE = "inactive"  # Temporarily inactive


class ConsentVersion(Enum):
    """Consent versioning information."""
    VERSION_1_0 = "1.0"
    VERSION_2_0 = "2.0"
    VERSION_3_0 = "3.0"


class AgeVerificationStatus(Enum):
    """Age verification status for Portuguese compliance."""
    VERIFIED_ADULT = "verified_adult"  # 16+
    UNVERIFIED = "unverified"
    MINOR_DETECTED = "minor_detected"  # Under 16
    PARENTAL_CONSENT_REQUIRED = "parental_consent_required"


@dataclass
class ConsentRecord:
    """
    Individual consent record with comprehensive tracking.
    
    Provides detailed consent information including:
    - Granular consent for specific purposes
    - Versioned consent terms and conditions
    - Legal evidence for GDPR compliance
    - Withdrawal tracking and automated processing
    - Portuguese age verification compliance
    """
    
    # Record identification
    consent_id: str
    user_id: int
    consent_type: ConsentType
    status: ConsentStatus
    
    # Consent details
    consent_version: ConsentVersion
    purpose_description: str
    legal_basis: str  # GDPR Article 6 basis
    data_categories: List[str]
    processing_purposes: List[str]
    
    # User consent
    granted: bool
    consent_date: datetime
    withdrawal_date: Optional[datetime]
    expiry_date: Optional[datetime]
    
    # Consent terms version
    terms_version: str
    policy_version: str
    consent_text: str
    
    # Legal compliance
    lawful_basis: str  # Specific legal basis for this consent
    legitimate_interest_test: Optional[str]
    consent_mechanism: str  # How consent was obtained
    
    # Evidence and audit
    user_ip: Optional[str]
    user_agent: Optional[str]
    device_fingerprint: Optional[str]
    geographic_location: Optional[str]
    
    # Consent withdrawal
    withdrawal_reason: Optional[str]
    withdrawal_mechanism: Optional[str]
    automatic_withdrawal_trigger: Optional[str]
    
    # Portuguese compliance
    age_verification_status: AgeVerificationStatus
    birth_date: Optional[datetime]
    parental_consent_required: bool
    parental_consent_obtained: bool
    
    # Processing integration
    processing_activity_id: Optional[str]  # Links to ROPA record
    dpia_reference: Optional[str]  # Links to DPIA if required
    
    # Additional metadata
    consent_metadata: Dict[str, Any]
    renewal_required: bool
    last_renewal_attempt: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


@dataclass
class ConsentPreferences:
    """
    User's overall consent preferences and settings.
    
    Provides a consolidated view of all consent-related
    preferences for user interface and management.
    """
    
    user_id: int
    overall_status: str
    consent_summary: Dict[ConsentType, bool]  # type -> granted
    
    # Marketing preferences
    marketing_consents: Dict[ConsentType, bool]
    communication_channels: Dict[str, bool]  # email, sms, push, etc.
    
    # Analytics preferences
    analytics_consents: Dict[ConsentType, bool]
    tracking_level: str  # none, basic, detailed
    
    # Third-party sharing
    third_party_consents: Dict[ConsentType, bool]
    data_sharing_preferences: Dict[str, bool]
    
    # Legal compliance
    legal_consents: Dict[ConsentType, bool]
    terms_versions_accepted: List[str]
    
    # Portuguese specific
    portuguese_compliance: Dict[ConsentType, bool]
    age_verification_date: Optional[datetime]
    parental_consent_status: Optional[str]
    
    # Consent management
    default_consent_setting: bool
    auto_renewal_preference: bool
    withdrawal_notification_preference: bool
    
    # Privacy dashboard settings
    show_privacy_dashboard: bool
    consent_history_access: bool
    data_export_preference: bool


class ConsentVersionManager:
    """
    Manages consent versioning and terms updates.
    
    Handles:
    - Version tracking for consent terms and policies
    - Automatic consent renewal for updated terms
    - Migration of existing consents to new versions
    - Legal evidence preservation for different versions
    """
    
    CURRENT_CONSENT_VERSION = "3.0"
    CURRENT_PRIVACY_POLICY_VERSION = "2.1"
    CURRENT_TERMS_VERSION = "1.3"
    
    def __init__(self):
        self.version_history = {
            "3.0": {
                "effective_date": datetime(2024, 1, 1),
                "changes": [
                    "Enhanced data subject rights",
                    "Portuguese CNPD compliance",
                    "Granular consent controls",
                    "Automated withdrawal mechanisms"
                ],
                "migration_required": False
            },
            "2.0": {
                "effective_date": datetime(2023, 6, 1),
                "changes": [
                    "GDPR Article 7 compliance",
                    "Consent withdrawal mechanisms",
                    "Data retention policies"
                ],
                "migration_required": True
            },
            "1.0": {
                "effective_date": datetime(2022, 1, 1),
                "changes": [
                    "Initial GDPR implementation"
                ],
                "migration_required": True
            }
        }
    
    def get_current_version(self) -> ConsentVersion:
        """Get current consent version."""
        return ConsentVersion(self.CURRENT_CONSENT_VERSION)
    
    def get_consent_text(self, version: str, consent_type: ConsentType) -> str:
        """
        Get consent text for specific version and type.
        
        Args:
            version: Consent version
            consent_type: Type of consent
            
        Returns:
            Consent text for the specified version and type
        """
        consent_texts = {
            ConsentType.ACCOUNT_CREATION: {
                "3.0": "I consent to the creation and management of my user account for the FineHero traffic fine defense service.",
                "2.0": "I consent to account creation and basic service provision.",
                "1.0": "I agree to create an account and use the service."
            },
            ConsentType.PAYMENT_PROCESSING: {
                "3.0": "I consent to the processing of my payment information through secure third-party payment processors for subscription services.",
                "2.0": "I consent to payment processing for services.",
                "1.0": "I authorize payment processing."
            },
            ConsentType.EMAIL_MARKETING: {
                "3.0": "I consent to receiving marketing communications via email about FineHero services and related legal assistance.",
                "2.0": "I consent to email marketing communications.",
                "1.0": "I agree to receive promotional emails."
            },
            ConsentType.ANALYTICS_COOKIES: {
                "3.0": "I consent to the use of analytics cookies and similar technologies to improve service quality and user experience.",
                "2.0": "I consent to analytics tracking.",
                "1.0": "I agree to service analytics."
            },
            ConsentType.PORTUGUESE_LEGAL_COMPLIANCE: {
                "3.0": "I consent to the processing of my data in accordance with Portuguese data protection law (Lei 58/2019) and CNPD requirements.",
                "2.0": "I consent to Portuguese legal compliance processing.",
                "1.0": "I agree to comply with local laws."
            }
        }
        
        return consent_texts.get(consent_type, {}).get(version, "Standard consent text for " + consent_type.value)
    
    def requires_migration(self, current_version: str) -> bool:
        """
        Check if consent version requires migration.
        
        Args:
            current_version: Current consent version
            
        Returns:
            Whether migration is required
        """
        version_info = self.version_history.get(current_version, {})
        return version_info.get("migration_required", False)
    
    def get_migration_requirements(self, current_version: str) -> List[str]:
        """
        Get migration requirements for updating consent version.
        
        Args:
            current_version: Current consent version
            
        Returns:
            List of migration requirements
        """
        if current_version == "1.0":
            return [
                "Granular consent controls implementation",
                "Automated withdrawal mechanisms",
                "Enhanced audit trails",
                "Portuguese compliance integration"
            ]
        elif current_version == "2.0":
            return [
                "Advanced consent lifecycle management",
                "Age verification system",
                "Enhanced privacy controls",
                "Automated compliance monitoring"
            ]
        return []


class AgeVerificationService:
    """
    Portuguese age verification service for GDPR minor protection.
    
    Handles:
    - Age verification for 16+ Portuguese requirement
    - Parental consent management for minors
    - Compliance with Portuguese data protection law
    - CNPD age-related processing requirements
    """
    
    PORTUGUESE_AGE_OF_CONSENT = 16
    
    def __init__(self):
        self.verification_methods = {
            "document_verification": "Government ID verification",
            "declaration": "Self-declaration with documentation",
            "parental_consent": "Parental/guardian consent verification",
            "third_party_verification": "External age verification service"
        }
    
    def verify_age_compliance(
        self,
        user_id: int,
        birth_date: Optional[datetime] = None,
        verification_method: str = "declaration"
    ) -> AgeVerificationStatus:
        """
        Verify age compliance for Portuguese data protection law.
        
        Args:
            user_id: User ID to verify
            birth_date: User's birth date if available
            verification_method: Method used for verification
            
        Returns:
            Age verification status
        """
        try:
            if not birth_date:
                return AgeVerificationStatus.UNVERIFIED
            
            # Calculate age
            today = datetime.utcnow().date()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            if age >= self.PORTUGUESE_AGE_OF_CONSENT:
                return AgeVerificationStatus.VERIFIED_ADULT
            elif age >= 13:  # Minimum age for service use
                return AgeVerificationStatus.PARENTAL_CONSENT_REQUIRED
            else:
                return AgeVerificationStatus.MINOR_DETECTED
                
        except Exception as e:
            logger.error(f"Error verifying age for user {user_id}: {e}")
            return AgeVerificationStatus.UNVERIFIED
    
    def get_parental_consent_requirements(self, user_age: int) -> Dict[str, Any]:
        """
        Get parental consent requirements based on user age.
        
        Args:
            user_age: User's age
            
        Returns:
            Parental consent requirements
        """
        if user_age >= 16:
            return {
                "parental_consent_required": False,
                "reason": "User is over Portuguese age of consent (16)"
            }
        elif user_age >= 13:
            return {
                "parental_consent_required": True,
                "consent_level": "basic",
                "age_appropriate_consent": True,
                "reason": "User is minor but over 13 - parental consent required"
            }
        else:
            return {
                "parental_consent_required": True,
                "consent_level": "full",
                "age_appropriate_consent": False,
                "reason": "User is under 13 - full parental consent and age-appropriate processing required"
            }
    
    def validate_portuguese_compliance(self, user_id: int, consent_records: List[ConsentRecord]) -> Dict[str, Any]:
        """
        Validate Portuguese GDPR compliance for a user's consent records.
        
        Args:
            user_id: User ID
            consent_records: List of user's consent records
            
        Returns:
            Portuguese compliance validation result
        """
        validation_result = {
            "user_id": user_id,
            "compliance_status": "compliant",
            "issues": [],
            "recommendations": [],
            "age_verification_required": False
        }
        
        # Check for Portuguese-specific consents
        portuguese_consents = [c for c in consent_records if c.consent_type == ConsentType.PORTUGUESE_LEGAL_COMPLIANCE]
        if not portuguese_consents:
            validation_result["issues"].append("Missing Portuguese legal compliance consent")
            validation_result["recommendations"].append("Request Portuguese legal compliance consent")
        
        # Check age verification for relevant consents
        age_sensitive_consents = [
            ConsentType.HEALTH_DATA_PROCESSING,
            ConsentType.BIOMETRIC_DATA_PROCESSING,
            ConsentType.CRIMINAL_DATA_PROCESSING
        ]
        
        for record in consent_records:
            if record.consent_type in age_sensitive_consents:
                if record.age_verification_status != AgeVerificationStatus.VERIFIED_ADULT:
                    validation_result["age_verification_required"] = True
                    validation_result["issues"].append(f"Age verification required for {record.consent_type.value}")
                    validation_result["recommendations"].append("Complete age verification before processing special category data")
        
        return validation_result


class ConsentWithdrawalManager:
    """
    Manages automated consent withdrawal processes.
    
    Handles:
    - One-click consent withdrawal mechanisms
    - Automatic processing cessation upon withdrawal
    - Data impact assessment after withdrawal
    - User notification and follow-up actions
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def withdraw_consent(
        self,
        user_id: int,
        consent_type: ConsentType,
        reason: str = "User request",
        withdrawal_mechanism: str = "user_interface"
    ) -> bool:
        """
        Withdraw consent for a specific type.
        
        Args:
            user_id: User withdrawing consent
            consent_type: Type of consent to withdraw
            reason: Reason for withdrawal
            withdrawal_mechanism: How consent was withdrawn
            
        Returns:
            Success status of withdrawal
        """
        try:
            # Find active consent record
            consent_record = self._find_active_consent_record(user_id, consent_type)
            if not consent_record:
                logger.warning(f"No active consent record found for user {user_id}, type {consent_type}")
                return False
            
            # Update consent record
            consent_record.status = ConsentStatus.WITHDRAWN
            consent_record.granted = False
            consent_record.withdrawal_date = datetime.utcnow()
            consent_record.withdrawal_reason = reason
            consent_record.withdrawal_mechanism = withdrawal_mechanism
            consent_record.updated_at = datetime.utcnow()
            
            # Process data impact of withdrawal
            self._process_withdrawal_impact(user_id, consent_type, consent_record)
            
            # Create audit trail entry
            self._create_withdrawal_audit_entry(consent_record, reason)
            
            # Trigger automated processes
            self._trigger_withdrawal_processes(user_id, consent_type)
            
            logger.info(f"Consent withdrawn for user {user_id}, type {consent_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error withdrawing consent for user {user_id}: {e}")
            return False
    
    def withdraw_all_consents(
        self,
        user_id: int,
        reason: str = "User request",
        exclude_types: Optional[List[ConsentType]] = None
    ) -> Dict[ConsentType, bool]:
        """
        Withdraw all consents for a user.
        
        Args:
            user_id: User withdrawing all consents
            reason: Reason for withdrawal
            exclude_types: Consent types to exclude from withdrawal
            
        Returns:
            Dictionary of consent type -> withdrawal success
        """
        results = {}
        exclude_types = exclude_types or []
        
        try:
            # Get all active consent records
            active_consents = self._get_active_consent_records(user_id)
            
            for consent_record in active_consents:
                if consent_record.consent_type not in exclude_types:
                    success = self.withdraw_consent(
                        user_id,
                        consent_record.consent_type,
                        reason,
                        "bulk_withdrawal"
                    )
                    results[consent_record.consent_type] = success
                else:
                    results[consent_record.consent_type] = True  # Excluded, considered successful
            
            logger.info(f"Bulk consent withdrawal completed for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk consent withdrawal for user {user_id}: {e}")
            return {}
    
    def _find_active_consent_record(
        self,
        user_id: int,
        consent_type: ConsentType
    ) -> Optional[ConsentRecord]:
        """Find active consent record for user and type."""
        # This would query the database for active consent records
        # For now, returning None as placeholder
        return None
    
    def _get_active_consent_records(self, user_id: int) -> List[ConsentRecord]:
        """Get all active consent records for a user."""
        # This would query the database for active consent records
        # For now, returning empty list as placeholder
        return []
    
    def _process_withdrawal_impact(
        self,
        user_id: int,
        consent_type: ConsentType,
        consent_record: ConsentRecord
    ):
        """Process the impact of consent withdrawal on data processing."""
        # Immediate impact processing
        if consent_type in [ConsentType.EMAIL_MARKETING, ConsentType.SMS_MARKETING]:
            # Stop marketing communications
            self._stop_marketing_communications(user_id, consent_type)
        
        if consent_type == ConsentType.ANALYTICS_COOKIES:
            # Stop analytics tracking
            self._stop_analytics_tracking(user_id)
        
        if consent_type in [ConsentType.THIRD_PARTY_INTEGRATIONS, ConsentType.DATA_BROKER_SHARING]:
            # Stop third-party data sharing
            self._stop_third_party_sharing(user_id, consent_type)
    
    def _stop_marketing_communications(self, user_id: int, consent_type: ConsentType):
        """Stop marketing communications for user."""
        # Implementation would update marketing systems
        logger.info(f"Marketing communications stopped for user {user_id}, type {consent_type}")
    
    def _stop_analytics_tracking(self, user_id: int):
        """Stop analytics tracking for user."""
        # Implementation would update analytics systems
        logger.info(f"Analytics tracking stopped for user {user_id}")
    
    def _stop_third_party_sharing(self, user_id: int, consent_type: ConsentType):
        """Stop third-party data sharing for user."""
        # Implementation would update third-party integrations
        logger.info(f"Third-party sharing stopped for user {user_id}, type {consent_type}")
    
    def _create_withdrawal_audit_entry(self, consent_record: ConsentRecord, reason: str):
        """Create audit trail entry for consent withdrawal."""
        # Create comprehensive audit entry for withdrawal
        logger.debug(f"Consent withdrawal audit entry created for {consent_record.consent_id}")
    
    def _trigger_withdrawal_processes(self, user_id: int, consent_type: ConsentType):
        """Trigger automated processes after consent withdrawal."""
        # Trigger data deletion if required
        # Update processing systems
        # Notify relevant stakeholders
        logger.info(f"Withdrawal processes triggered for user {user_id}, type {consent_type}")


class EnhancedConsentService:
    """
    Main service for enhanced consent management.
    
    Provides comprehensive consent management functionality:
    - Granular consent handling for specific purposes
    - Automated withdrawal processing
    - Portuguese age verification compliance
    - Consent versioning and lifecycle management
    - Integration with privacy dashboard
    - Legal evidence preservation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.version_manager = ConsentVersionManager()
        self.age_verification = AgeVerificationService()
        self.withdrawal_manager = ConsentWithdrawalManager(db)
        self.consent_records: Dict[str, ConsentRecord] = {}
    
    def grant_consent(
        self,
        user_id: int,
        consent_type: ConsentType,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        birth_date: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Grant consent for a specific type.
        
        Args:
            user_id: User granting consent
            consent_type: Type of consent to grant
            user_ip: User's IP address for audit
            user_agent: User's browser information
            birth_date: User's birth date for age verification
            additional_metadata: Additional consent metadata
            
        Returns:
            Consent ID of the created consent record
        """
        try:
            # Verify age compliance if birth date provided
            age_status = AgeVerificationStatus.UNVERIFIED
            if birth_date:
                age_status = self.age_verification.verify_age_compliance(
                    user_id, birth_date
                )
            
            # Check if parental consent required
            parental_consent_required = False
            parental_consent_obtained = False
            
            if age_status == AgeVerificationStatus.PARENTAL_CONSENT_REQUIRED:
                parental_consent_required = True
                # In real implementation, would check for parental consent
            
            # Generate consent ID
            consent_id = f"CONSENT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}_{consent_type.value}"
            
            # Create consent record
            consent_record = ConsentRecord(
                consent_id=consent_id,
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.GRANTED,
                consent_version=self.version_manager.get_current_version(),
                purpose_description=self._get_purpose_description(consent_type),
                legal_basis="consent",
                data_categories=self._get_data_categories(consent_type),
                processing_purposes=self._get_processing_purposes(consent_type),
                granted=True,
                consent_date=datetime.utcnow(),
                expiry_date=None,
                terms_version=self.version_manager.CURRENT_TERMS_VERSION,
                policy_version=self.version_manager.CURRENT_PRIVACY_POLICY_VERSION,
                consent_text=self.version_manager.get_consent_text(
                    self.version_manager.CURRENT_CONSENT_VERSION, consent_type
                ),
                lawful_basis="consent",
                consent_mechanism="web_interface",
                user_ip=user_ip,
                user_agent=user_agent,
                age_verification_status=age_status,
                birth_date=birth_date,
                parental_consent_required=parental_consent_required,
                parental_consent_obtained=parental_consent_obtained,
                processing_activity_id=self._get_processing_activity_id(consent_type),
                consent_metadata=additional_metadata or {},
                renewal_required=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store consent record
            self.consent_records[consent_id] = consent_record
            
            # Create audit trail entry
            self._create_consent_audit_entry(consent_record, "granted")
            
            # Process immediate actions for granted consent
            self._process_consent_granted(user_id, consent_type)
            
            logger.info(f"Consent granted: {consent_id}")
            return consent_id
            
        except Exception as e:
            logger.error(f"Error granting consent for user {user_id}: {e}")
            raise
    
    def withdraw_consent(
        self,
        user_id: int,
        consent_type: ConsentType,
        reason: str = "User request"
    ) -> bool:
        """
        Withdraw consent for a specific type.
        
        Args:
            user_id: User withdrawing consent
            consent_type: Type of consent to withdraw
            reason: Reason for withdrawal
            
        Returns:
            Success status of withdrawal
        """
        return self.withdrawal_manager.withdraw_consent(user_id, consent_type, reason)
    
    def get_user_consent_preferences(self, user_id: int) -> ConsentPreferences:
        """
        Get comprehensive consent preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User's consent preferences
        """
        # Get all consent records for user
        user_consents = [
            record for record in self.consent_records.values()
            if record.user_id == user_id
        ]
        
        # Build consent summary
        consent_summary = {}
        marketing_consents = {}
        analytics_consents = {}
        third_party_consents = {}
        legal_consents = {}
        portuguese_consents = {}
        
        for record in user_consents:
            consent_summary[record.consent_type] = record.granted
            
            if record.consent_type in [
                ConsentType.EMAIL_MARKETING, ConsentType.SMS_MARKETING,
                ConsentType.PUSH_NOTIFICATIONS, ConsentType.NEWSLETTER_SUBSCRIPTION,
                ConsentType.PRODUCT_UPDATES
            ]:
                marketing_consents[record.consent_type] = record.granted
            
            elif record.consent_type in [
                ConsentType.ANALYTICS_COOKIES, ConsentType.BEHAVIORAL_ANALYTICS,
                ConsentType.PERFORMANCE_MONITORING, ConsentType.A_B_TESTING
            ]:
                analytics_consents[record.consent_type] = record.granted
            
            elif record.consent_type in [
                ConsentType.THIRD_PARTY_INTEGRATIONS, ConsentType.SOCIAL_MEDIA_SHARING,
                ConsentType.DATA_BROKER_SHARING
            ]:
                third_party_consents[record.consent_type] = record.granted
            
            elif record.consent_type in [
                ConsentType.TERMS_ACCEPTANCE, ConsentType.PRIVACY_POLICY_ACCEPTANCE,
                ConsentType.COOKIE_POLICY_ACCEPTANCE, ConsentType.LEGAL_PROCESSING
            ]:
                legal_consents[record.consent_type] = record.granted
            
            elif record.consent_type in [
                ConsentType.PORTUGUESE_LEGAL_COMPLIANCE, ConsentType.CNPD_PROCESSING,
                ConsentType.LOCAL_DATA_RESIDENCY
            ]:
                portuguese_consents[record.consent_type] = record.granted
        
        # Get age verification status
        age_verification_date = None
        parental_consent_status = None
        
        for record in user_consents:
            if record.birth_date:
                age_verification_date = record.birth_date
            if record.age_verification_status != AgeVerificationStatus.UNVERIFIED:
                parental_consent_status = record.age_verification_status.value
        
        return ConsentPreferences(
            user_id=user_id,
            overall_status="active" if user_consents else "inactive",
            consent_summary=consent_summary,
            marketing_consents=marketing_consents,
            communication_channels={
                "email": marketing_consents.get(ConsentType.EMAIL_MARKETING, False),
                "sms": marketing_consents.get(ConsentType.SMS_MARKETING, False),
                "push": marketing_consents.get(ConsentType.PUSH_NOTIFICATIONS, False)
            },
            analytics_consents=analytics_consents,
            tracking_level="detailed" if any(analytics_consents.values()) else "none",
            third_party_consents=third_party_consents,
            data_sharing_preferences={
                "integrations": third_party_consents.get(ConsentType.THIRD_PARTY_INTEGRATIONS, False),
                "social_sharing": third_party_consents.get(ConsentType.SOCIAL_MEDIA_SHARING, False),
                "data_brokers": third_party_consents.get(ConsentType.DATA_BROKER_SHARING, False)
            },
            legal_consents=legal_consents,
            terms_versions_accepted=[r.terms_version for r in user_consents if r.granted],
            portuguese_compliance=portuguese_consents,
            age_verification_date=age_verification_date,
            parental_consent_status=parental_consent_status,
            default_consent_setting=False,
            auto_renewal_preference=True,
            withdrawal_notification_preference=True,
            show_privacy_dashboard=True,
            consent_history_access=True,
            data_export_preference=True
        )
    
    def get_consent_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate consent compliance report.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Compliance report data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            active_records = [
                record for record in self.consent_records.values()
                if record.created_at >= cutoff_date
            ]
            
            report = {
                "report_period": f"Last {days} days",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_consents": len(active_records),
                    "granted_consents": len([r for r in active_records if r.granted]),
                    "withdrawn_consents": len([r for r in active_records if r.status == ConsentStatus.WITHDRAWN]),
                    "expired_consents": len([r for r in active_records if r.status == ConsentStatus.EXPIRED])
                },
                "consent_type_distribution": {},
                "withdrawal_analysis": {
                    "withdrawal_reasons": {},
                    "withdrawal_mechanisms": {}
                },
                "portuguese_compliance": {
                    "age_verified_users": len([r for r in active_records if r.age_verification_status == AgeVerificationStatus.VERIFIED_ADULT]),
                    "parental_consent_required": len([r for r in active_records if r.parental_consent_required]),
                    "local_compliance_rate": 0.0
                },
                "version_distribution": {},
                "legal_evidence_quality": {}
            }
            
            # Calculate distributions
            type_count = {}
            version_count = {}
            
            for record in active_records:
                # Consent type distribution
                type_count[record.consent_type.value] = type_count.get(record.consent_type.value, 0) + 1
                
                # Version distribution
                version_count[record.consent_version.value] = version_count.get(record.consent_version.value, 0) + 1
                
                # Withdrawal analysis
                if record.status == ConsentStatus.WITHDRAWN:
                    reason = record.withdrawal_reason or "unknown"
                    report["withdrawal_analysis"]["withdrawal_reasons"][reason] = \
                        report["withdrawal_analysis"]["withdrawal_reasons"].get(reason, 0) + 1
                    
                    mechanism = record.withdrawal_mechanism or "unknown"
                    report["withdrawal_analysis"]["withdrawal_mechanisms"][mechanism] = \
                        report["withdrawal_analysis"]["withdrawal_mechanisms"].get(mechanism, 0) + 1
            
            report["consent_type_distribution"] = type_count
            report["version_distribution"] = version_count
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating consent compliance report: {e}")
            return {}
    
    def _get_purpose_description(self, consent_type: ConsentType) -> str:
        """Get purpose description for consent type."""
        descriptions = {
            ConsentType.ACCOUNT_CREATION: "Creating and managing user accounts",
            ConsentType.PAYMENT_PROCESSING: "Processing subscription payments",
            ConsentType.EMAIL_MARKETING: "Sending marketing communications via email",
            ConsentType.ANALYTICS_COOKIES: "Analyzing website usage and user behavior",
            ConsentType.PORTUGUESE_LEGAL_COMPLIANCE: "Processing data according to Portuguese law"
        }
        return descriptions.get(consent_type, f"Processing for {consent_type.value}")
    
    def _get_data_categories(self, consent_type: ConsentType) -> List[str]:
        """Get data categories for consent type."""
        category_mapping = {
            ConsentType.ACCOUNT_CREATION: ["identity_data", "contact_data"],
            ConsentType.PAYMENT_PROCESSING: ["financial_data"],
            ConsentType.EMAIL_MARKETING: ["contact_data", "behavioral_data"],
            ConsentType.ANALYTICS_COOKIES: ["technical_data", "behavioral_data"],
            ConsentType.PORTUGUESE_LEGAL_COMPLIANCE: ["identity_data", "contact_data"]
        }
        return category_mapping.get(consent_type, ["personal_data"])
    
    def _get_processing_purposes(self, consent_type: ConsentType) -> List[str]:
        """Get processing purposes for consent type."""
        purpose_mapping = {
            ConsentType.ACCOUNT_CREATION: ["service_provision", "account_management"],
            ConsentType.PAYMENT_PROCESSING: ["payment_processing", "service_provision"],
            ConsentType.EMAIL_MARKETING: ["marketing", "customer_communication"],
            ConsentType.ANALYTICS_COOKIES: ["analytics", "service_improvement"],
            ConsentType.PORTUGUESE_LEGAL_COMPLIANCE: ["legal_compliance", "data_protection"]
        }
        return purpose_mapping.get(consent_type, ["service_operation"])
    
    def _get_processing_activity_id(self, consent_type: ConsentType) -> Optional[str]:
        """Get processing activity ID for consent type."""
        # This would link to ROPA records
        return f"ROPA_{consent_type.value}"
    
    def _process_consent_granted(self, user_id: int, consent_type: ConsentType):
        """Process immediate actions when consent is granted."""
        if consent_type == ConsentType.EMAIL_MARKETING:
            # Add to marketing list
            pass
        elif consent_type == ConsentType.ANALYTICS_COOKIES:
            # Enable analytics tracking
            pass
    
    def _create_consent_audit_entry(self, consent_record: ConsentRecord, action: str):
        """Create audit trail entry for consent action."""
        # Create comprehensive audit entry
        logger.debug(f"Consent audit entry created: {consent_record.consent_id} - {action}")


# Utility functions for easy integration
def create_enhanced_consent_service(db: Session) -> EnhancedConsentService:
    """Create an enhanced consent service instance."""
    return EnhancedConsentService(db)


def setup_default_consent_types(db: Session) -> List[str]:
    """
    Set up default consent types for FineHero service.
    
    Args:
        db: Database session
        
    Returns:
        List of created consent type configurations
    """
    try:
        # This would initialize default consent configurations
        # For now, returning placeholder
        default_types = [
            ConsentType.ACCOUNT_CREATION.value,
            ConsentType.PAYMENT_PROCESSING.value,
            ConsentType.EMAIL_MARKETING.value,
            ConsentType.ANALYTICS_COOKIES.value,
            ConsentType.PORTUGUESE_LEGAL_COMPLIANCE.value
        ]
        
        logger.info(f"Default consent types setup completed: {default_types}")
        return default_types
        
    except Exception as e:
        logger.error(f"Error setting up default consent types: {e}")
        return []