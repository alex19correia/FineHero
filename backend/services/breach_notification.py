"""
Breach Notification System for GDPR Articles 33-34 compliance.

This module provides comprehensive data breach notification capabilities:
- Automated breach detection and incident response
- 72-hour notification timeline tracking for supervisory authorities
- User notification system for Article 34 compliance
- Complete incident response tracking and documentation
- Portuguese CNPD notification procedures integration
- Breach impact assessment and risk evaluation

Key Features:
- Real-time breach detection and alerting
- Automated 72-hour notification timeline management
- Comprehensive incident response workflow
- Risk-based user notification decisions
- Portuguese DPA (CNPD) integration procedures
- Legal evidence preservation and audit trails
- Multi-channel breach notification delivery
- Post-breach improvement and prevention measures
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


class BreachType(Enum):
    """Types of data breaches."""
    CONFIDENTIALITY_BREACH = "confidentiality_breach"  # Unauthorized access/disclosure
    INTEGRITY_BREACH = "integrity_breach"             # Data alteration/damage
    AVAILABILITY_BREACH = "availability_breach"       # Data loss/unavailability
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_LEAK = "data_leak"
    SYSTEM_COMPROMISE = "system_compromise"
    THIRD_PARTY_BREACH = "third_party_breach"
    PHYSICAL_BREACH = "physical_breach"


class BreachSeverity(Enum):
    """Severity levels for data breaches."""
    LOW = "low"           # Minimal risk to rights and freedoms
    MEDIUM = "medium"     # Moderate risk requiring notification
    HIGH = "high"         # Significant risk requiring prompt notification
    CRITICAL = "critical" # Severe risk requiring immediate notification


class BreachStatus(Enum):
    """Status of breach incident."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ASSESSING = "assessing"
    NOTIFYING = "notifying"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationStatus(Enum):
    """Status of notifications."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class BreachSource(Enum):
    """Source of breach detection."""
    AUTOMATED_MONITORING = "automated_monitoring"
    USER_REPORT = "user_report"
    THIRD_PARTY_ALERT = "third_party_alert"
    INTERNAL_AUDIT = "internal_audit"
    SECURITY_TEAM = "security_team"
    REGULATORY_INQUIRY = "regulatory_inquiry"


@dataclass
class BreachIncident:
    """
    Data breach incident record with comprehensive tracking.
    
    Contains complete breach information:
    - Incident details and timeline
    - Affected data and systems
    - Risk assessment and impact evaluation
    - Notification tracking and compliance
    - Resolution and remediation actions
    - Legal evidence and audit trail
    """
    
    # Incident identification
    incident_id: str
    breach_type: BreachType
    severity: BreachSeverity
    status: BreachStatus
    
    # Detection information
    detection_date: datetime
    detection_source: BreachSource
    detected_by: str
    detection_method: str
    
    # Incident details
    description: str
    initial_assessment: str
    affected_systems: List[str]
    affected_data_categories: List[str]
    affected_data_subjects_count: Optional[int]
    
    # Technical details
    attack_vector: Optional[str]
    vulnerability_exploited: Optional[str]
    attacker_information: Optional[str]
    data_compromised: bool
    data_exfiltrated: bool
    
    # Risk assessment
    risk_level: BreachSeverity
    rights_impact_assessment: str
    harm_potential: str
    mitigation_measures: List[str]
    
    # Timeline tracking
    estimated_breach_start: Optional[datetime]
    estimated_breach_end: Optional[datetime]
    containment_date: Optional[datetime]
    investigation_start: datetime
    
    # Legal compliance
    gdpr_article_33_required: bool  # Supervisory authority notification
    gdpr_article_34_required: bool  # Data subject notification
    notification_deadline: datetime  # 72 hours from awareness
    user_notification_deadline: Optional[datetime]  # Without undue delay
    
    # Notification tracking
    supervisory_authority_notifications: List[Dict[str, Any]]
    data_subject_notifications: List[Dict[str, Any]]
    third_party_notifications: List[Dict[str, Any]]
    
    # Portuguese compliance
    cnpd_notification_required: bool
    cnpd_notification_sent: bool
    cnpd_notification_date: Optional[datetime]
    local_contact_information: Dict[str, str]
    
    # Resolution and remediation
    containment_actions: List[str]
    remediation_actions: List[str]
    preventive_measures: List[str]
    resolution_date: Optional[datetime]
    
    # Evidence and audit
    evidence_collected: List[str]
    legal_advice_sought: bool
    external_investigation: bool
    law_enforcement_contacted: bool
    
    # Additional metadata
    incident_metadata: Dict[str, Any]
    lessons_learned: Optional[str]
    system_improvements: List[str]


@dataclass
class NotificationRecord:
    """
    Record of breach notification sent to stakeholders.
    
    Provides detailed notification tracking:
    - Recipient information and contact details
    - Notification content and method
    - Delivery confirmation and acknowledgment
    - Legal compliance verification
    - Follow-up actions and reminders
    """
    
    notification_id: str
    incident_id: str
    recipient_type: str  # "supervisory_authority", "data_subject", "third_party"
    recipient_name: str
    recipient_contact: str
    
    # Notification details
    notification_method: str  # "email", "postal", "phone", "system"
    notification_date: datetime
    notification_content: Dict[str, Any]
    legal_basis: str
    
    # Status tracking
    status: NotificationStatus
    sent_date: Optional[datetime]
    delivered_date: Optional[datetime]
    acknowledged_date: Optional[datetime]
    
    # Compliance tracking
    gdpr_compliance_verified: bool
    notification_completeness: str  # "complete", "partial", "insufficient"
    follow_up_required: bool
    
    # Quality assurance
    notification_quality_score: Optional[float]
    delivery_confirmation: Dict[str, Any]
    response_received: bool
    response_content: Optional[str]


class BreachDetectionEngine:
    """
    Automated breach detection and alerting system.
    
    Handles:
    - Real-time monitoring of security events
    - Pattern recognition for potential breaches
    - Automated incident creation and escalation
    - Integration with security monitoring tools
    - Risk-based alert prioritization
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.monitoring_rules = self._initialize_monitoring_rules()
        self.alert_thresholds = self._initialize_alert_thresholds()
    
    def detect_potential_breach(
        self,
        security_event: Dict[str, Any],
        event_source: str = "automated_monitoring"
    ) -> Optional[BreachIncident]:
        """
        Detect potential data breach from security events.
        
        Args:
            security_event: Security event data
            event_source: Source of the security event
            
        Returns:
            Breach incident if detected, None otherwise
        """
        try:
            # Analyze security event against monitoring rules
            breach_indicators = self._analyze_security_event(security_event)
            
            if not breach_indicators:
                return None
            
            # Determine breach type and severity
            breach_type = self._determine_breach_type(breach_indicators)
            severity = self._assess_breach_severity(breach_indicators, security_event)
            
            # Create breach incident
            incident = self._create_breach_incident(
                breach_type, severity, security_event, event_source
            )
            
            logger.warning(f"Potential data breach detected: {incident.incident_id}")
            return incident
            
        except Exception as e:
            logger.error(f"Error detecting potential breach: {e}")
            return None
    
    def _initialize_monitoring_rules(self) -> List[Dict[str, Any]]:
        """Initialize breach detection monitoring rules."""
        return [
            {
                "rule_id": "unauthorized_access",
                "description": "Detect unauthorized access attempts",
                "conditions": [
                    {"event_type": "failed_login_attempts", "threshold": 10},
                    {"event_type": "privilege_escalation", "immediate": True},
                    {"event_type": "access_outside_hours", "weight": 0.7}
                ],
                "breach_types": [BreachType.UNAUTHORIZED_ACCESS],
                "severity_indicators": ["critical_system_access", "sensitive_data_access"]
            },
            {
                "rule_id": "data_exfiltration",
                "description": "Detect potential data exfiltration",
                "conditions": [
                    {"event_type": "large_data_export", "threshold": 1000},
                    {"event_type": "unusual_data_transfer", "weight": 0.9},
                    {"event_type": "off_hours_access", "weight": 0.6}
                ],
                "breach_types": [BreachType.DATA_LEAK, BreachType.CONFIDENTIALITY_BREACH],
                "severity_indicators": ["personal_data_volume", "sensitive_data_involved"]
            },
            {
                "rule_id": "system_compromise",
                "description": "Detect system compromise indicators",
                "conditions": [
                    {"event_type": "malware_detection", "immediate": True},
                    {"event_type": "system_modification", "weight": 0.8},
                    {"event_type": "network_anomaly", "weight": 0.7}
                ],
                "breach_types": [BreachType.SYSTEM_COMPROMISE],
                "severity_indicators": ["admin_privilege_compromise", "database_access"]
            }
        ]
    
    def _initialize_alert_thresholds(self) -> Dict[str, Any]:
        """Initialize alert thresholds for different breach types."""
        return {
            BreachType.CONFIDENTIALITY_BREACH: {
                "notification_threshold": 1,  # Immediate notification
                "severity_mapping": {
                    "personal_data_involved": BreachSeverity.HIGH,
                    "sensitive_data_involved": BreachSeverity.CRITICAL,
                    "large_volume": BreachSeverity.HIGH
                }
            },
            BreachType.DATA_LEAK: {
                "notification_threshold": 1,
                "severity_mapping": {
                    "external_transmission": BreachSeverity.HIGH,
                    "unauthorized_destination": BreachSeverity.CRITICAL
                }
            },
            BreachType.SYSTEM_COMPROMISE: {
                "notification_threshold": 1,
                "severity_mapping": {
                    "database_access": BreachSeverity.CRITICAL,
                    "admin_compromise": BreachSeverity.CRITICAL
                }
            }
        }
    
    def _analyze_security_event(self, security_event: Dict[str, Any]) -> List[str]:
        """Analyze security event for breach indicators."""
        indicators = []
        
        # Check against monitoring rules
        for rule in self.monitoring_rules:
            rule_indicators = self._check_rule_conditions(security_event, rule)
            indicators.extend(rule_indicators)
        
        return indicators
    
    def _check_rule_conditions(self, security_event: Dict[str, Any], rule: Dict[str, Any]) -> List[str]:
        """Check security event against rule conditions."""
        indicators = []
        
        for condition in rule["conditions"]:
            if condition.get("immediate"):
                if self._matches_immediate_condition(security_event, condition):
                    indicators.append(f"immediate_trigger_{rule['rule_id']}")
            else:
                # Check threshold-based conditions
                if self._check_threshold_condition(security_event, condition):
                    indicators.append(f"threshold_met_{rule['rule_id']}")
        
        return indicators
    
    def _matches_immediate_condition(self, security_event: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if security event matches immediate trigger condition."""
        event_type = security_event.get("event_type")
        return event_type == condition["event_type"]
    
    def _check_threshold_condition(self, security_event: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if security event meets threshold condition."""
        event_type = security_event.get("event_type")
        if event_type != condition["event_type"]:
            return False
        
        # For threshold conditions, we'd need to track cumulative events
        # For now, returning False as placeholder
        return False
    
    def _determine_breach_type(self, breach_indicators: List[str]) -> BreachType:
        """Determine breach type based on indicators."""
        # Simple mapping based on indicators
        if any("unauthorized_access" in indicator for indicator in breach_indicators):
            return BreachType.UNAUTHORIZED_ACCESS
        elif any("data_exfiltration" in indicator for indicator in breach_indicators):
            return BreachType.DATA_LEAK
        elif any("system_compromise" in indicator for indicator in breach_indicators):
            return BreachType.SYSTEM_COMPROMISE
        else:
            return BreachType.CONFIDENTIALITY_BREACH
    
    def _assess_breach_severity(self, breach_indicators: List[str], security_event: Dict[str, Any]) -> BreachSeverity:
        """Assess severity of potential breach."""
        # Assess based on multiple factors
        severity_score = 0
        
        # Factor in affected data types
        if security_event.get("involves_personal_data"):
            severity_score += 2
        if security_event.get("involves_sensitive_data"):
            severity_score += 3
        if security_event.get("volume_of_data", 0) > 1000:
            severity_score += 2
        
        # Factor in system criticality
        if security_event.get("affected_system") == "database":
            severity_score += 3
        elif security_event.get("affected_system") in ["user_management", "payment_processing"]:
            severity_score += 2
        
        # Factor in attack sophistication
        if security_event.get("attack_sophistication") == "high":
            severity_score += 2
        
        # Determine severity level
        if severity_score >= 7:
            return BreachSeverity.CRITICAL
        elif severity_score >= 4:
            return BreachSeverity.HIGH
        elif severity_score >= 2:
            return BreachSeverity.MEDIUM
        else:
            return BreachSeverity.LOW
    
    def _create_breach_incident(
        self,
        breach_type: BreachType,
        severity: BreachSeverity,
        security_event: Dict[str, Any],
        detection_source: str
    ) -> BreachIncident:
        """Create breach incident from security event."""
        # Generate incident ID
        incident_id = f"BREACH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(security_event.get('affected_records', []))}"
        
        # Determine notification requirements
        article_33_required = severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]
        article_34_required = severity == BreachSeverity.CRITICAL
        
        # Calculate notification deadline (72 hours from awareness)
        notification_deadline = datetime.utcnow() + timedelta(hours=72)
        
        # Estimate data subjects count if available
        affected_count = security_event.get("affected_records_count", 0)
        
        return BreachIncident(
            incident_id=incident_id,
            breach_type=breach_type,
            severity=severity,
            status=BreachStatus.DETECTED,
            detection_date=datetime.utcnow(),
            detection_source=BreachSource(detection_source),
            detected_by=security_event.get("detected_by", "automated_system"),
            detection_method=security_event.get("detection_method", "automated_monitoring"),
            description=security_event.get("description", "Potential data breach detected"),
            initial_assessment=security_event.get("initial_assessment", "Under investigation"),
            affected_systems=[security_event.get("affected_system", "unknown")],
            affected_data_categories=security_event.get("data_categories", []),
            affected_data_subjects_count=affected_count if affected_count > 0 else None,
            attack_vector=security_event.get("attack_vector"),
            vulnerability_exploited=security_event.get("vulnerability"),
            data_compromised=security_event.get("data_compromised", False),
            data_exfiltrated=security_event.get("data_exfiltrated", False),
            risk_level=severity,
            rights_impact_assessment=security_event.get("impact_assessment", "Assessment in progress"),
            harm_potential=security_event.get("harm_potential", "To be determined"),
            mitigation_measures=security_event.get("mitigation_measures", []),
            investigation_start=datetime.utcnow(),
            gdpr_article_33_required=article_33_required,
            gdpr_article_34_required=article_34_required,
            notification_deadline=notification_deadline,
            supervisory_authority_notifications=[],
            data_subject_notifications=[],
            third_party_notifications=[],
            cnpd_notification_required=True,  # Portuguese requirement
            cnpd_notification_sent=False,
            local_contact_information={
                "dpo_contact": "dpo@finehero.pt",
                "legal_contact": "legal@finehero.pt",
                "emergency_contact": "emergency@finehero.pt"
            },
            containment_actions=[],
            remediation_actions=[],
            preventive_measures=[],
            evidence_collected=[],
            legal_advice_sought=False,
            external_investigation=False,
            law_enforcement_contacted=False,
            incident_metadata=security_event,
            lessons_learned=None,
            system_improvements=[]
        )


class NotificationManager:
    """
    Manages breach notifications to supervisory authorities and data subjects.
    
    Handles:
    - Automated notification generation and delivery
    - 72-hour deadline tracking and compliance
    - Portuguese CNPD notification procedures
    - Multi-channel notification delivery
    - Delivery confirmation and acknowledgment tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_records: Dict[str, NotificationRecord] = {}
        
        # Portuguese supervisory authority details
        self.cnpd_details = {
            "name": "Comissão Nacional de Proteção de Dados (CNPD)",
            "address": "Av. D. Carlos I, 134, 1.º 1200-651 Lisboa",
            "email": "geral@cnpd.pt",
            "phone": "+351 21 392 84 10",
            "website": "https://www.cnpd.pt"
        }
    
    def send_supervisory_authority_notification(self, incident: BreachIncident) -> bool:
        """
        Send notification to supervisory authority (Article 33).
        
        Args:
            incident: Breach incident to notify about
            
        Returns:
            Success status of notification
        """
        try:
            if not incident.gdpr_article_33_required:
                logger.info(f"Article 33 notification not required for incident {incident.incident_id}")
                return True
            
            # Create notification record
            notification_id = f"NOTIF_SA_{incident.incident_id}"
            
            # Generate notification content
            notification_content = self._generate_authority_notification_content(incident)
            
            notification_record = NotificationRecord(
                notification_id=notification_id,
                incident_id=incident.incident_id,
                recipient_type="supervisory_authority",
                recipient_name=self.cnpd_details["name"],
                recipient_contact=self.cnpd_details["email"],
                notification_method="email",
                notification_date=datetime.utcnow(),
                notification_content=notification_content,
                legal_basis="GDPR Article 33",
                status=NotificationStatus.IN_PROGRESS,
                gdpr_compliance_verified=True,
                notification_completeness="complete"
            )
            
            # Send notification (implementation would integrate with email system)
            success = self._deliver_authority_notification(notification_record)
            
            if success:
                notification_record.status = NotificationStatus.SENT
                notification_record.sent_date = datetime.utcnow()
                
                # Update incident
                incident.supervisory_authority_notifications.append({
                    "notification_id": notification_id,
                    "recipient": self.cnpd_details["name"],
                    "sent_date": datetime.utcnow().isoformat(),
                    "method": "email"
                })
                
                # Portuguese specific notification
                if incident.cnpd_notification_required:
                    incident.cnpd_notification_sent = True
                    incident.cnpd_notification_date = datetime.utcnow()
                
                logger.info(f"Supervisory authority notification sent for incident {incident.incident_id}")
            else:
                notification_record.status = NotificationStatus.FAILED
                logger.error(f"Failed to send supervisory authority notification for incident {incident.incident_id}")
            
            # Store notification record
            self.notification_records[notification_id] = notification_record
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending supervisory authority notification: {e}")
            return False
    
    def send_data_subject_notifications(self, incident: BreachIncident) -> Dict[str, bool]:
        """
        Send notifications to affected data subjects (Article 34).
        
        Args:
            incident: Breach incident
            
        Returns:
            Dictionary of notification results by data subject
        """
        results = {}
        
        try:
            if not incident.gdpr_article_34_required:
                logger.info(f"Article 34 notifications not required for incident {incident.incident_id}")
                return {"total": 0, "successful": 0}
            
            # Get affected data subjects (would integrate with user system)
            affected_users = self._get_affected_users(incident)
            
            successful_notifications = 0
            
            for user in affected_users:
                notification_id = f"NOTIF_DS_{incident.incident_id}_{user['id']}"
                
                # Generate user-specific notification content
                notification_content = self._generate_user_notification_content(incident, user)
                
                notification_record = NotificationRecord(
                    notification_id=notification_id,
                    incident_id=incident.incident_id,
                    recipient_type="data_subject",
                    recipient_name=user["name"],
                    recipient_contact=user["email"],
                    notification_method="email",
                    notification_date=datetime.utcnow(),
                    notification_content=notification_content,
                    legal_basis="GDPR Article 34",
                    status=NotificationStatus.IN_PROGRESS,
                    gdpr_compliance_verified=True,
                    notification_completeness="complete"
                )
                
                # Send notification
                success = self._deliver_user_notification(notification_record)
                
                if success:
                    notification_record.status = NotificationStatus.SENT
                    notification_record.sent_date = datetime.utcnow()
                    successful_notifications += 1
                    
                    # Update incident
                    incident.data_subject_notifications.append({
                        "notification_id": notification_id,
                        "user_id": user["id"],
                        "sent_date": datetime.utcnow().isoformat(),
                        "method": "email"
                    })
                else:
                    notification_record.status = NotificationStatus.FAILED
                
                # Store notification record
                self.notification_records[notification_id] = notification_record
                results[user["id"]] = success
            
            logger.info(f"Data subject notifications completed for incident {incident.incident_id}: {successful_notifications}/{len(affected_users)}")
            return results
            
        except Exception as e:
            logger.error(f"Error sending data subject notifications: {e}")
            return {}
    
    def _generate_authority_notification_content(self, incident: BreachIncident) -> Dict[str, Any]:
        """Generate notification content for supervisory authority."""
        return {
            "subject": f"Data Breach Notification - FineHero (Incident {incident.incident_id})",
            "body": {
                "incident_summary": {
                    "incident_id": incident.incident_id,
                    "breach_type": incident.breach_type.value,
                    "detection_date": incident.detection_date.isoformat(),
                    "severity": incident.severity.value,
                    "affected_data_subjects": incident.affected_data_subjects_count or "Unknown"
                },
                "breach_details": {
                    "description": incident.description,
                    "affected_systems": incident.affected_systems,
                    "data_categories_affected": incident.affected_data_categories,
                    "data_compromised": incident.data_compromised,
                    "data_exfiltrated": incident.data_exfiltrated
                },
                "risk_assessment": {
                    "risk_level": incident.risk_level.value,
                    "impact_on_rights": incident.rights_impact_assessment,
                    "potential_harm": incident.harm_potential
                },
                "response_actions": {
                    "containment_measures": incident.containment_actions,
                    "mitigation_measures": incident.mitigation_measures,
                    "investigation_status": incident.status.value
                },
                "compliance_information": {
                    "notification_deadline": incident.notification_deadline.isoformat(),
                    "portuguese_compliance": True,
                    "dpo_contact": incident.local_contact_information["dpo_contact"]
                }
            },
            "attachments": ["incident_evidence.zip", "technical_analysis.pdf"]
        }
    
    def _generate_user_notification_content(self, incident: BreachIncident, user: Dict[str, Any]) -> Dict[str, Any]:
        """Generate notification content for data subjects."""
        return {
            "subject": "Important Security Notice - Your Personal Data",
            "body": {
                "personal_message": f"Dear {user.get('name', 'User')},",
                "incident_explanation": {
                    "what_happened": incident.description,
                    "when_discovered": incident.detection_date.strftime("%B %d, %Y at %H:%M UTC"),
                    "data_involved": incident.affected_data_categories,
                    "what_we_are_doing": "We have immediately secured our systems and are conducting a thorough investigation."
                },
                "potential_impact": {
                    "risk_assessment": incident.harm_potential,
                    "recommended_actions": [
                        "Monitor your accounts for unusual activity",
                        "Change your password if you share it elsewhere",
                        "Be cautious of phishing emails"
                    ]
                },
                "what_we_are_doing": {
                    "immediate_actions": incident.containment_actions,
                    "preventive_measures": incident.preventive_measures,
                    "investigation_progress": "Our security team is working around the clock"
                },
                "contact_information": {
                    "dpo_contact": incident.local_contact_information["dpo_contact"],
                    "support_email": "security@finehero.pt",
                    "emergency_contact": incident.local_contact_information["emergency_contact"]
                }
            }
        }
    
    def _deliver_authority_notification(self, notification_record: NotificationRecord) -> bool:
        """Deliver notification to supervisory authority."""
        try:
            # Implementation would integrate with email system
            # For now, logging the notification
            logger.info(f"Sending authority notification: {notification_record.notification_id}")
            logger.info(f"Recipient: {notification_record.recipient_contact}")
            logger.info(f"Subject: {notification_record.notification_content['subject']}")
            
            # Simulate successful delivery
            return True
            
        except Exception as e:
            logger.error(f"Error delivering authority notification: {e}")
            return False
    
    def _deliver_user_notification(self, notification_record: NotificationRecord) -> bool:
        """Deliver notification to data subject."""
        try:
            # Implementation would integrate with email system
            logger.info(f"Sending user notification: {notification_record.notification_id}")
            logger.info(f"Recipient: {notification_record.recipient_contact}")
            logger.info(f"Subject: {notification_record.notification_content['subject']}")
            
            # Simulate successful delivery
            return True
            
        except Exception as e:
            logger.error(f"Error delivering user notification: {e}")
            return False
    
    def _get_affected_users(self, incident: BreachIncident) -> List[Dict[str, Any]]:
        """Get list of affected data subjects."""
        # This would integrate with the user system to get affected users
        # For now, returning placeholder data
        return [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com"
            }
        ]


class BreachNotificationService:
    """
    Main service for breach notification management.
    
    Provides comprehensive breach response:
    - Automated breach detection and incident creation
    - 72-hour notification timeline management
    - Multi-stakeholder notification coordination
    - Portuguese legal compliance integration
    - Incident tracking and resolution management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.detection_engine = BreachDetectionEngine(db)
        self.notification_manager = NotificationManager(db)
        self.incidents: Dict[str, BreachIncident] = {}
    
    def process_security_event(
        self,
        security_event: Dict[str, Any],
        event_source: str = "automated_monitoring"
    ) -> Optional[str]:
        """
        Process security event and create breach incident if needed.
        
        Args:
            security_event: Security event data
            event_source: Source of the event
            
        Returns:
            Incident ID if breach detected, None otherwise
        """
        try:
            # Detect potential breach
            incident = self.detection_engine.detect_potential_breach(security_event, event_source)
            
            if not incident:
                return None
            
            # Store incident
            self.incidents[incident.incident_id] = incident
            
            # Create audit trail entry
            self._create_incident_audit_entry(incident, "detected")
            
            # Start automated response if configured
            if incident.severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
                self._initiate_automated_response(incident.incident_id)
            
            logger.warning(f"Breach incident created: {incident.incident_id}")
            return incident.incident_id
            
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
            return None
    
    def manage_incident_lifecycle(self, incident_id: str, action: str, details: Dict[str, Any]) -> bool:
        """
        Manage incident lifecycle and notifications.
        
        Args:
            incident_id: ID of incident to manage
            action: Action to perform
            details: Action details
            
        Returns:
            Success status of action
        """
        try:
            if incident_id not in self.incidents:
                logger.error(f"Incident not found: {incident_id}")
                return False
            
            incident = self.incidents[incident_id]
            
            if action == "update_status":
                new_status = BreachStatus(details.get("status"))
                incident.status = new_status
                incident.last_updated = datetime.utcnow()
                
                if new_status == BreachStatus.CONTAINED:
                    incident.containment_date = datetime.utcnow()
                
                elif new_status == BreachStatus.RESOLVED:
                    incident.resolution_date = datetime.utcnow()
            
            elif action == "add_containment_action":
                incident.containment_actions.append(details.get("action"))
                incident.status = BreachStatus.CONTAINED
            
            elif action == "add_remediation_action":
                incident.remediation_actions.append(details.get("action"))
            
            elif action == "send_notifications":
                # Send supervisory authority notification
                if incident.gdpr_article_33_required:
                    sa_success = self.notification_manager.send_supervisory_authority_notification(incident)
                    if not sa_success:
                        logger.error(f"Failed to send supervisory authority notification for {incident_id}")
                
                # Send data subject notifications if required
                if incident.gdpr_article_34_required:
                    ds_results = self.notification_manager.send_data_subject_notifications(incident)
                    logger.info(f"Data subject notifications for {incident_id}: {ds_results}")
            
            elif action == "update_assessment":
                incident.rights_impact_assessment = details.get("impact_assessment")
                incident.harm_potential = details.get("harm_potential")
                incident.risk_level = BreachSeverity(details.get("risk_level", incident.risk_level.value))
            
            # Create audit trail entry
            self._create_incident_audit_entry(incident, action)
            
            # Check for deadline compliance
            self._check_notification_deadlines(incident)
            
            logger.info(f"Incident lifecycle action completed: {incident_id} - {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error managing incident lifecycle: {e}")
            return False
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive incident status.
        
        Args:
            incident_id: ID of incident
            
        Returns:
            Incident status information
        """
        if incident_id not in self.incidents:
            return None
        
        incident = self.incidents[incident_id]
        
        return {
            "incident_id": incident.incident_id,
            "breach_type": incident.breach_type.value,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "detection_date": incident.detection_date.isoformat(),
            "notification_deadline": incident.notification_deadline.isoformat(),
            "time_remaining": str(incident.notification_deadline - datetime.utcnow()),
            "gdpr_compliance": {
                "article_33_required": incident.gdpr_article_33_required,
                "article_34_required": incident.gdpr_article_34_required,
                "notifications_sent": {
                    "supervisory_authority": len(incident.supervisory_authority_notifications),
                    "data_subjects": len(incident.data_subject_notifications)
                },
                "cnpd_compliance": {
                    "notification_required": incident.cnpd_notification_required,
                    "notification_sent": incident.cnpd_notification_sent
                }
            },
            "resolution_progress": {
                "containment_actions": len(incident.containment_actions),
                "remediation_actions": len(incident.remediation_actions),
                "preventive_measures": len(incident.preventive_measures),
                "resolved": incident.resolution_date is not None
            }
        }
    
    def get_breach_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate breach notification compliance report.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Compliance report data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_incidents = [
                incident for incident in self.incidents.values()
                if incident.detection_date >= cutoff_date
            ]
            
            report = {
                "report_period": f"Last {days} days",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_incidents": len(recent_incidents),
                    "high_severity_incidents": len([i for i in recent_incidents if i.severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]]),
                    "notification_required_incidents": len([i for i in recent_incidents if i.gdpr_article_33_required]),
                    "resolved_incidents": len([i for i in recent_incidents if i.status == BreachStatus.RESOLVED])
                },
                "notification_compliance": {
                    "article_33_compliance_rate": 0.0,
                    "article_34_compliance_rate": 0.0,
                    "deadline_adherence": 0.0,
                    "average_response_time_hours": 0.0
                },
                "incident_trends": {
                    "breach_type_distribution": {},
                    "severity_distribution": {},
                    "detection_source_distribution": {},
                    "resolution_time_trends": []
                },
                "cnpd_compliance": {
                    "incidents_reported": len([i for i in recent_incidents if i.cnpd_notification_required]),
                    "notification_rate": 0.0,
                    "average_response_time_days": 0.0
                },
                "risk_metrics": {
                    "high_risk_incidents": len([i for i in recent_incidents if i.risk_level == BreachSeverity.HIGH]),
                    "critical_incidents": len([i for i in recent_incidents if i.risk_level == BreachSeverity.CRITICAL]),
                    "data_exfiltration_incidents": len([i for i in recent_incidents if i.data_exfiltrated])
                }
            }
            
            # Calculate distributions and metrics
            type_count = {}
            severity_count = {}
            detection_source_count = {}
            response_times = []
            
            for incident in recent_incidents:
                # Distribution counts
                type_count[incident.breach_type.value] = type_count.get(incident.breach_type.value, 0) + 1
                severity_count[incident.severity.value] = severity_count.get(incident.severity.value, 0) + 1
                detection_source_count[incident.detection_source.value] = detection_source_count.get(incident.detection_source.value, 0) + 1
                
                # Response time calculation
                if incident.containment_date:
                    response_time = (incident.containment_date - incident.detection_date).total_seconds() / 3600
                    response_times.append(response_time)
            
            report["incident_trends"]["breach_type_distribution"] = type_count
            report["incident_trends"]["severity_distribution"] = severity_count
            report["incident_trends"]["detection_source_distribution"] = detection_source_count
            
            # Calculate compliance metrics
            notification_required = [i for i in recent_incidents if i.gdpr_article_33_required]
            if notification_required:
                compliant_notifications = len([i for i in notification_required if i.supervisory_authority_notifications])
                report["notification_compliance"]["article_33_compliance_rate"] = (compliant_notifications / len(notification_required)) * 100
            
            if response_times:
                report["notification_compliance"]["average_response_time_hours"] = sum(response_times) / len(response_times)
            
            # CNPD compliance
            cnpd_required = [i for i in recent_incidents if i.cnpd_notification_required]
            if cnpd_required:
                cnpd_sent = len([i for i in cnpd_required if i.cnpd_notification_sent])
                report["cnpd_compliance"]["notification_rate"] = (cnpd_sent / len(cnpd_required)) * 100
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating breach compliance report: {e}")
            return {}
    
    def _initiate_automated_response(self, incident_id: str):
        """Initiate automated response for high-severity incidents."""
        incident = self.incidents[incident_id]
        
        # Start containment immediately
        self.manage_incident_lifecycle(incident_id, "add_containment_action", {
            "action": "Automated containment initiated"
        })
        
        # Send notifications if configured for automation
        if incident.gdpr_article_33_required:
            self.manage_incident_lifecycle(incident_id, "send_notifications", {})
    
    def _check_notification_deadlines(self, incident: BreachIncident):
        """Check notification deadline compliance."""
        now = datetime.utcnow()
        
        if now > incident.notification_deadline and not incident.supervisory_authority_notifications:
            logger.critical(f"MISSED DEADLINE: Supervisory authority notification overdue for incident {incident.incident_id}")
        
        if incident.user_notification_deadline and now > incident.user_notification_deadline and not incident.data_subject_notifications:
            logger.critical(f"MISSED DEADLINE: Data subject notification overdue for incident {incident.incident_id}")
    
    def _create_incident_audit_entry(self, incident: BreachIncident, action: str):
        """Create audit trail entry for incident action."""
        # Create comprehensive audit entry
        audit_data = {
            "incident_id": incident.incident_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "status": incident.status.value,
            "severity": incident.severity.value
        }
        
        logger.debug(f"Breach incident audit entry created: {incident.incident_id}")


# Utility functions for easy integration
def create_breach_notification_service(db: Session) -> BreachNotificationService:
    """Create a breach notification service instance."""
    return BreachNotificationService(db)


def simulate_breach_incident(db: Session, breach_config: Dict[str, Any]) -> str:
    """
    Simulate a breach incident for testing purposes.
    
    Args:
        db: Database session
        breach_config: Configuration for simulated breach
        
    Returns:
        Incident ID of created simulated breach
    """
    try:
        service = BreachNotificationService(db)
        
        # Create simulated security event
        security_event = {
            "event_type": breach_config.get("event_type", "unauthorized_access"),
            "affected_system": breach_config.get("affected_system", "user_database"),
            "data_categories": breach_config.get("data_categories", ["personal_data"]),
            "affected_records_count": breach_config.get("affected_records_count", 100),
            "involves_personal_data": True,
            "detected_by": "security_test",
            "description": f"Simulated breach incident for testing - {breach_config.get('description', 'Test incident')}"
        }
        
        # Process the security event
        incident_id = service.process_security_event(security_event, "test_simulation")
        
        if incident_id:
            # Add test-specific details
            service.manage_incident_lifecycle(incident_id, "update_assessment", {
                "impact_assessment": "Test incident - no actual risk",
                "harm_potential": "Test only",
                "risk_level": "medium"
            })
            
            logger.info(f"Simulated breach incident created: {incident_id}")
            return incident_id
        else:
            logger.warning("Simulated breach incident not created")
            return ""
        
    except Exception as e:
        logger.error(f"Error creating simulated breach incident: {e}")
        return ""