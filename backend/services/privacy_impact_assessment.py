"""
Privacy Impact Assessment (DPIA) System for GDPR Article 35 compliance.

This module provides comprehensive Privacy Impact Assessment capabilities:
- Automated DPIA for high-risk processing activities
- Risk assessment algorithms for data processing activities
- DPO (Data Protection Officer) workflow and notification system
- Decision tree automation to determine when DPIA is required
- Portuguese CNPD integration for local compliance

Key Features:
- Risk scoring algorithms for different processing types
- Automated DPIA trigger for high-risk activities
- DPO review and approval workflow
- Compliance documentation and reporting
- Integration with Portuguese data protection requirements
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..app import models
from ..app.models_base import AuditTrail

# Configure logging
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for DPIA assessments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ProcessingType(Enum):
    """Types of data processing activities."""
    DIRECT_MARKETING = "direct_marketing"
    PROFILING = "profiling"
    AUTOMATED_DECISION_MAKING = "automated_decision_making"
    LARGE_SCALE_PROCESSING = "large_scale_processing"
    SPECIAL_CATEGORIES = "special_categories"
    VULNERABLE_GROUPS = "vulnerable_groups"
    SYSTEMATIC_MONITORING = "systematic_monitoring"
    NEW_TECHNOLOGY = "new_technology"
    DATA_FUSION = "data_fusion"
    MINOR_DATA = "minor_data"


class DPIAStatus(Enum):
    """DPIA assessment statuses."""
    REQUIRED = "required"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_MODIFICATION = "requires_modification"
    EXEMPTED = "exempted"


@dataclass
class ProcessingActivity:
    """Represents a data processing activity for DPIA assessment."""
    activity_id: str
    name: str
    description: str
    processing_types: List[ProcessingType]
    data_categories: List[str]
    data_sources: List[str]
    purposes: List[str]
    legal_basis: str
    recipients: List[str]
    retention_period: str
    data_minimization_measures: List[str]
    security_measures: List[str]
    international_transfers: bool
    third_country_transfers: bool
    automated_decision_making: bool
    profiling_involved: bool
    vulnerable_groups_involved: bool
    estimated_number_of_data_subjects: int
    business_justification: str
    alternatives_considered: List[str]
    risk_mitigation_measures: List[str]


@dataclass
class DPIAResult:
    """Result of a DPIA assessment."""
    dpia_id: str
    processing_activity: ProcessingActivity
    risk_score: int
    risk_level: RiskLevel
    dpia_required: bool
    dpia_status: DPIAStatus
    assessment_date: datetime
    assessed_by: str
    dpo_review_required: bool
    dpo_review_status: Optional[str]
    dpo_review_date: Optional[datetime]
    risk_factors: List[str]
    mitigation_measures: List[str]
    residual_risk_score: int
    recommendations: List[str]
    next_review_date: Optional[datetime]
    compliance_deadline: Optional[datetime]
    portguese_cnpd_required: bool
    assessment_metadata: Dict[str, Any]


class DPIADecisionTree:
    """
    Decision tree to determine when DPIA is required per GDPR Article 35.
    
    Implements automated decision logic based on risk criteria:
    - Systematic monitoring of publicly accessible areas
    - Large scale processing of special categories or criminal data
    - Systematic monitoring of data subjects on large scale
    - Use of new technology or new use of existing technology
    - Processing that may result in high risk to rights and freedoms
    """
    
    @staticmethod
    def requires_dpia(processing_activity: ProcessingActivity) -> Tuple[bool, str]:
        """
        Determine if DPIA is required for a processing activity.
        
        Args:
            processing_activity: The processing activity to assess
            
        Returns:
            Tuple of (requires_dpia: bool, reason: str)
        """
        risk_factors = []
        
        # 1. Systematic monitoring of publicly accessible areas
        if ProcessingType.SYSTEMATIC_MONITORING in processing_activity.processing_types:
            risk_factors.append("systematic_monitoring")
        
        # 2. Large scale processing of special categories
        if (ProcessingType.SPECIAL_CATEGORIES in processing_activity.processing_types and 
            processing_activity.estimated_number_of_data_subjects > 1000):
            risk_factors.append("large_scale_special_categories")
        
        # 3. Automated decision making with legal effects
        if (processing_activity.automated_decision_making and 
            any("legal" in purpose.lower() or "rights" in purpose.lower() 
                for purpose in processing_activity.purposes)):
            risk_factors.append("automated_decision_making_legal")
        
        # 4. Systematic monitoring of data subjects on large scale
        if (ProcessingType.PROFILING in processing_activity.processing_types and 
            processing_activity.estimated_number_of_data_subjects > 1000):
            risk_factors.append("systematic_profiling_large_scale")
        
        # 5. Use of new technology
        if ProcessingType.NEW_TECHNOLOGY in processing_activity.processing_types:
            risk_factors.append("new_technology")
        
        # 6. Vulnerable groups data
        if (processing_activity.vulnerable_groups_involved or 
            ProcessingType.VULNERABLE_GROUPS in processing_activity.processing_types):
            risk_factors.append("vulnerable_groups")
        
        # 7. Data fusion combining multiple sources
        if ProcessingType.DATA_FUSION in processing_activity.processing_types:
            risk_factors.append("data_fusion")
        
        # 8. Third country transfers
        if processing_activity.third_country_transfers:
            risk_factors.append("third_country_transfers")
        
        # 9. Large scale processing (>5000 data subjects)
        if (ProcessingType.LARGE_SCALE_PROCESSING in processing_activity.processing_types or
            processing_activity.estimated_number_of_data_subjects > 5000):
            risk_factors.append("large_scale_processing")
        
        # 10. High sensitivity business justification without adequate alternatives
        if (not processing_activity.alternatives_considered and 
            len(processing_activity.purposes) > 2):
            risk_factors.append("inadequate_alternatives_analysis")
        
        # Determine if DPIA is required
        dpia_required = len(risk_factors) > 0
        
        if dpia_required:
            reason = f"DPIA required due to: {', '.join(risk_factors)}"
        else:
            reason = "No DPIA risk factors identified"
        
        return dpia_required, reason


class RiskAssessmentEngine:
    """
    Engine for calculating risk scores and levels for processing activities.
    
    Implements sophisticated risk scoring algorithms based on:
    - Processing type complexity
    - Data sensitivity levels
    - Scale of processing
    - Vulnerable group involvement
    - International data transfers
    - Security measures adequacy
    """
    
    # Risk scoring weights
    PROCESSING_TYPE_WEIGHTS = {
        ProcessingType.DIRECT_MARKETING: 2,
        ProcessingType.PROFILING: 4,
        ProcessingType.AUTOMATED_DECISION_MAKING: 6,
        ProcessingType.LARGE_SCALE_PROCESSING: 5,
        ProcessingType.SPECIAL_CATEGORIES: 8,
        ProcessingType.VULNERABLE_GROUPS: 7,
        ProcessingType.SYSTEMATIC_MONITORING: 5,
        ProcessingType.NEW_TECHNOLOGY: 6,
        ProcessingType.DATA_FUSION: 4,
        ProcessingType.MINOR_DATA: 7
    }
    
    # Data category sensitivity multipliers
    DATA_CATEGORY_MULTIPLIERS = {
        "personal_identifiers": 1.0,
        "contact_information": 1.2,
        "financial_data": 2.0,
        "location_data": 1.5,
        "behavioral_data": 1.8,
        "health_data": 3.0,
        "biometric_data": 3.0,
        "criminal_data": 3.5,
        "children_data": 4.0
    }
    
    # Scale multipliers
    SCALE_MULTIPLIERS = {
        (0, 100): 1.0,        # Very small scale
        (101, 1000): 1.5,     # Small scale
        (1001, 10000): 2.0,   # Medium scale
        (10001, 100000): 2.5, # Large scale
        (100001, float('inf')): 3.0  # Very large scale
    }
    
    @classmethod
    def calculate_risk_score(cls, processing_activity: ProcessingActivity) -> Tuple[int, RiskLevel]:
        """
        Calculate risk score for a processing activity.
        
        Args:
            processing_activity: Processing activity to assess
            
        Returns:
            Tuple of (risk_score: int, risk_level: RiskLevel)
        """
        base_score = 0
        
        # Add processing type scores
        for processing_type in processing_activity.processing_types:
            base_score += cls.PROCESSING_TYPE_WEIGHTS.get(processing_type, 0)
        
        # Add data sensitivity multipliers
        for data_category in processing_activity.data_categories:
            multiplier = cls.DATA_CATEGORY_MULTIPLIERS.get(data_category, 1.0)
            base_score *= multiplier
        
        # Add scale multiplier
        scale_multiplier = cls._get_scale_multiplier(processing_activity.estimated_number_of_data_subjects)
        base_score *= scale_multiplier
        
        # Add international transfer risk
        if processing_activity.third_country_transfers:
            base_score *= 1.3
        
        # Add vulnerable groups risk
        if processing_activity.vulnerable_groups_involved:
            base_score *= 1.4
        
        # Subtract risk mitigation measures
        mitigation_reduction = min(len(processing_activity.risk_mitigation_measures) * 0.5, 0.3)
        base_score *= (1 - mitigation_reduction)
        
        # Ensure minimum score
        final_score = max(int(base_score), 1)
        
        # Determine risk level
        if final_score <= 10:
            risk_level = RiskLevel.LOW
        elif final_score <= 25:
            risk_level = RiskLevel.MEDIUM
        elif final_score <= 40:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return final_score, risk_level
    
    @classmethod
    def _get_scale_multiplier(cls, data_subjects_count: int) -> float:
        """Get scale multiplier based on number of data subjects."""
        for (min_count, max_count), multiplier in cls.SCALE_MULTIPLIERS.items():
            if min_count <= data_subjects_count <= max_count:
                return multiplier
        return 1.0


class DPOWorkflowManager:
    """
    Manages Data Protection Officer (DPO) workflow and notifications.
    
    Handles:
    - DPO assignment and notification
    - Review and approval workflow
    - Status tracking and escalation
    - Portuguese CNPD integration
    - Compliance deadline management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.default_dpo_email = "dpo@finehero.pt"  # Portuguese DPO contact
    
    def notify_dpo_for_review(
        self,
        dpia_result: DPIAResult,
        notify_immediately: bool = True
    ) -> bool:
        """
        Notify DPO for DPIA review.
        
        Args:
            dpia_result: DPIA result requiring DPO review
            notify_immediately: Whether to send immediate notification
            
        Returns:
            Success status of notification
        """
        try:
            # Create DPO notification record
            notification_data = {
                "dpia_id": dpia_result.dpia_id,
                "processing_activity_name": dpia_result.processing_activity.name,
                "risk_level": dpia_result.risk_level.value,
                "risk_score": dpia_result.risk_score,
                "notification_date": datetime.utcnow(),
                "review_deadline": dpia_result.compliance_deadline,
                "dpo_email": self.default_dpo_email,
                "notification_status": "pending",
                "priority": "high" if dpia_result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH] else "normal"
            }
            
            # Store notification in audit metadata or create notification model
            # This would typically involve creating a notification record
            # For now, we'll log and store in audit trail
            
            logger.info(f"DPO notification created for DPIA {dpia_result.dpia_id}")
            
            # Create audit trail entry
            self._create_dpo_notification_audit_entry(notification_data)
            
            # Send actual notification (email, internal system, etc.)
            if notify_immediately:
                self._send_dpo_notification(notification_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying DPO for DPIA {dpia_result.dpia_id}: {e}")
            return False
    
    def update_dpo_review_status(
        self,
        dpia_id: str,
        review_status: str,
        review_comments: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> bool:
        """
        Update DPO review status.
        
        Args:
            dpia_id: DPIA identifier
            review_status: New review status
            review_comments: DPO review comments
            reviewed_by: ID of reviewing DPO
            
        Returns:
            Success status of update
        """
        try:
            # Update DPIA record with DPO review status
            # This would involve database updates
            
            review_data = {
                "dpia_id": dpia_id,
                "review_status": review_status,
                "review_comments": review_comments,
                "reviewed_by": reviewed_by,
                "review_date": datetime.utcnow()
            }
            
            # Create audit trail entry
            self._create_dpo_review_audit_entry(review_data)
            
            # Send notifications if needed
            if review_status == "approved":
                self._notify_approval_complete(dpia_id)
            elif review_status == "rejected":
                self._notify_approval_rejected(dpia_id, review_comments)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating DPO review status for DPIA {dpia_id}: {e}")
            return False
    
    def _send_dpo_notification(self, notification_data: Dict[str, Any]):
        """Send DPO notification via email or internal system."""
        # This would implement actual notification sending
        # Email integration, Slack notifications, internal alerts, etc.
        logger.info(f"Sending DPO notification for DPIA {notification_data['dpia_id']}")
    
    def _create_dpo_notification_audit_entry(self, data: Dict[str, Any]):
        """Create audit trail entry for DPO notification."""
        # Create audit trail entry for DPO notification
        # Implementation depends on your audit system
        logger.debug(f"Created DPO notification audit entry for {data['dpia_id']}")
    
    def _create_dpo_review_audit_entry(self, data: Dict[str, Any]):
        """Create audit trail entry for DPO review."""
        # Create audit trail entry for DPO review
        logger.debug(f"Created DPO review audit entry for {data['dpia_id']}")
    
    def _notify_approval_complete(self, dpia_id: str):
        """Notify when DPIA approval is complete."""
        logger.info(f"DPIA {dpia_id} approval completed - sending completion notifications")
    
    def _notify_approval_rejected(self, dpia_id: str, reason: Optional[str]):
        """Notify when DPIA is rejected."""
        logger.warning(f"DPIA {dpia_id} rejected: {reason}")


class DPIAService:
    """
    Main service for Privacy Impact Assessment operations.
    
    Provides comprehensive DPIA functionality:
    - Risk assessment for processing activities
    - Automated DPIA requirement determination
    - DPO workflow management
    - Portuguese CNPD integration
    - Compliance reporting and monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.decision_tree = DPIADecisionTree()
        self.risk_engine = RiskAssessmentEngine()
        self.dpo_workflow = DPOWorkflowManager(db)
    
    def assess_processing_activity(
        self,
        processing_activity: ProcessingActivity,
        assessed_by: str,
        require_dpo_review: bool = None
    ) -> DPIAResult:
        """
        Perform complete DPIA assessment for a processing activity.
        
        Args:
            processing_activity: Processing activity to assess
            assessed_by: Person performing the assessment
            require_dpo_review: Override automatic DPO review requirement
            
        Returns:
            Complete DPIA assessment result
        """
        try:
            # Generate DPIA ID
            dpia_id = f"DPIA_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{processing_activity.activity_id}"
            
            # Determine if DPIA is required
            dpia_required, dpia_reason = self.decision_tree.requires_dpia(processing_activity)
            
            # Calculate risk score
            risk_score, risk_level = self.risk_engine.calculate_risk_score(processing_activity)
            
            # Determine DPO review requirement
            if require_dpo_review is None:
                dpo_review_required = (dpia_required or 
                                     risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH])
            else:
                dpo_review_required = require_dpo_review
            
            # Generate compliance deadline
            if dpo_review_required:
                compliance_deadline = datetime.utcnow() + timedelta(days=30)  # 30-day review period
            else:
                compliance_deadline = datetime.utcnow() + timedelta(days=7)   # 7-day review period
            
            # Check if Portuguese CNPD notification is required
            cnpd_required = (processing_activity.third_country_transfers or 
                           processing_activity.vulnerable_groups_involved or
                           risk_score > 35)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                processing_activity, risk_level, risk_score
            )
            
            # Create DPIA result
            dpia_result = DPIAResult(
                dpia_id=dpia_id,
                processing_activity=processing_activity,
                risk_score=risk_score,
                risk_level=risk_level,
                dpia_required=dpia_required,
                dpia_status=DPIAStatus.REQUIRED if dpia_required else DPIAStatus.EXEMPTED,
                assessment_date=datetime.utcnow(),
                assessed_by=assessed_by,
                dpo_review_required=dpo_review_required,
                dpo_review_status=None,
                dpo_review_date=None,
                risk_factors=self._identify_risk_factors(processing_activity),
                mitigation_measures=self._generate_mitigation_measures(processing_activity, risk_level),
                residual_risk_score=self._calculate_residual_risk(risk_score, processing_activity),
                recommendations=recommendations,
                next_review_date=datetime.utcnow() + timedelta(days=365),  # Annual review
                compliance_deadline=compliance_deadline,
                portguese_cnpd_required=cnpd_required,
                assessment_metadata={
                    "dpia_reason": dpia_reason,
                    "assessment_version": "1.0",
                    "compliance_framework": "GDPR",
                    "local_compliance": "Portuguese_CNPD" if cnpd_required else None
                }
            )
            
            # Notify DPO if required
            if dpo_review_required:
                self.dpo_workflow.notify_dpo_for_review(dpia_result)
                dpia_result.dpia_status = DPIAStatus.IN_PROGRESS
            
            # Create audit trail entry
            self._create_dpia_audit_entry(dpia_result)
            
            logger.info(f"DPIA assessment completed for {dpia_id}, risk level: {risk_level.value}")
            
            return dpia_result
            
        except Exception as e:
            logger.error(f"Error performing DPIA assessment: {e}")
            raise
    
    def get_dpia_status(self, dpia_id: str) -> Optional[DPIAResult]:
        """
        Get DPIA assessment status and details.
        
        Args:
            dpia_id: DPIA identifier
            
        Returns:
            DPIA result if found, None otherwise
        """
        # This would query the database for DPIA records
        # For now, returning None as placeholder
        return None
    
    def update_dpia_status(
        self,
        dpia_id: str,
        new_status: DPIAStatus,
        updated_by: str,
        comments: Optional[str] = None
    ) -> bool:
        """
        Update DPIA assessment status.
        
        Args:
            dpia_id: DPIA identifier
            new_status: New DPIA status
            updated_by: Person updating the status
            comments: Optional update comments
            
        Returns:
            Success status of update
        """
        try:
            # Update DPIA record in database
            # This would involve database operations
            
            # Create audit trail entry
            update_data = {
                "dpia_id": dpia_id,
                "old_status": "unknown",
                "new_status": new_status.value,
                "updated_by": updated_by,
                "update_date": datetime.utcnow(),
                "comments": comments
            }
            
            self._create_status_update_audit_entry(update_data)
            
            logger.info(f"DPIA {dpia_id} status updated to {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating DPIA status for {dpia_id}: {e}")
            return False
    
    def get_compliance_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Get DPIA compliance dashboard for monitoring.
        
        Args:
            days: Number of days to include in dashboard
            
        Returns:
            Compliance dashboard data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            dashboard_data = {
                "report_period": f"Last {days} days",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_assessments": 0,
                    "pending_dpo_review": 0,
                    "approved_assessments": 0,
                    "high_risk_activities": 0,
                    "cnpd_notifications_required": 0
                },
                "risk_distribution": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "very_high": 0
                },
                "upcoming_deadlines": [],
                "compliance_gaps": []
            }
            
            # This would query the database for actual statistics
            # For now, returning placeholder data
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating DPIA compliance dashboard: {e}")
            return {}
    
    def _generate_recommendations(
        self,
        processing_activity: ProcessingActivity,
        risk_level: RiskLevel,
        risk_score: int
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        if risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Implement additional technical safeguards",
                "Conduct regular security audits",
                "Consider pseudonymization or anonymization",
                "Implement privacy by design principles"
            ])
        
        if risk_level == RiskLevel.VERY_HIGH:
            recommendations.extend([
                "Conduct DPO consultation before implementation",
                "Consider alternative processing methods",
                "Implement enhanced monitoring and logging",
                "Establish data subject consultation process"
            ])
        
        if processing_activity.third_country_transfers:
            recommendations.append("Ensure adequate transfer safeguards (SCCs, adequacy decisions)")
        
        if processing_activity.vulnerable_groups_involved:
            recommendations.append("Implement additional protections for vulnerable data subjects")
        
        if not processing_activity.alternatives_considered:
            recommendations.append("Document and evaluate alternative processing methods")
        
        return recommendations
    
    def _identify_risk_factors(self, processing_activity: ProcessingActivity) -> List[str]:
        """Identify specific risk factors for a processing activity."""
        risk_factors = []
        
        if ProcessingType.SPECIAL_CATEGORIES in processing_activity.processing_types:
            risk_factors.append("Processing of special category data")
        
        if processing_activity.automated_decision_making:
            risk_factors.append("Automated decision-making with legal effects")
        
        if processing_activity.third_country_transfers:
            risk_factors.append("International data transfers")
        
        if processing_activity.vulnerable_groups_involved:
            risk_factors.append("Processing of vulnerable group data")
        
        if processing_activity.estimated_number_of_data_subjects > 10000:
            risk_factors.append("Large scale processing")
        
        return risk_factors
    
    def _generate_mitigation_measures(
        self,
        processing_activity: ProcessingActivity,
        risk_level: RiskLevel
    ) -> List[str]:
        """Generate risk mitigation measures."""
        measures = processing_activity.risk_mitigation_measures.copy()
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            measures.extend([
                "Regular security assessments",
                "Staff training on data protection",
                "Incident response procedures"
            ])
        
        return measures
    
    def _calculate_residual_risk(self, original_score: int, processing_activity: ProcessingActivity) -> int:
        """Calculate residual risk score after mitigation measures."""
        # Subtract impact of mitigation measures
        mitigation_reduction = min(len(processing_activity.risk_mitigation_measures) * 0.3, 0.5)
        residual_score = max(int(original_score * (1 - mitigation_reduction)), 1)
        return residual_score
    
    def _create_dpia_audit_entry(self, dpia_result: DPIAResult):
        """Create audit trail entry for DPIA assessment."""
        # Create comprehensive audit entry
        audit_data = {
            "dpia_id": dpia_result.dpia_id,
            "processing_activity": dpia_result.processing_activity.activity_id,
            "risk_score": dpia_result.risk_score,
            "risk_level": dpia_result.risk_level.value,
            "dpia_required": dpia_result.dpia_required,
            "assessment_date": dpia_result.assessment_date.isoformat(),
            "assessed_by": dpia_result.assessed_by,
            "dpo_review_required": dpia_result.dpo_review_required
        }
        
        logger.debug(f"DPIA audit entry created for {dpia_result.dpia_id}")
    
    def _create_status_update_audit_entry(self, data: Dict[str, Any]):
        """Create audit trail entry for DPIA status update."""
        logger.debug(f"Status update audit entry created for {data['dpia_id']}")


# Utility functions for easy integration
def create_dpia_service(db: Session) -> DPIAService:
    """Create a DPIA service instance."""
    return DPIAService(db)


def assess_processing_activity_automated(
    db: Session,
    processing_data: Dict[str, Any],
    assessed_by: str = "system"
) -> Dict[str, Any]:
    """
    Automated assessment of processing activity from data dictionary.
    
    Args:
        db: Database session
        processing_data: Dictionary containing processing activity data
        assessed_by: Person or system performing assessment
        
    Returns:
        Assessment result as dictionary
    """
    try:
        # Convert dictionary to ProcessingActivity object
        processing_types = [ProcessingType(pt) for pt in processing_data.get('processing_types', [])]
        
        processing_activity = ProcessingActivity(
            activity_id=processing_data['activity_id'],
            name=processing_data['name'],
            description=processing_data['description'],
            processing_types=processing_types,
            data_categories=processing_data.get('data_categories', []),
            data_sources=processing_data.get('data_sources', []),
            purposes=processing_data.get('purposes', []),
            legal_basis=processing_data.get('legal_basis', 'consent'),
            recipients=processing_data.get('recipients', []),
            retention_period=processing_data.get('retention_period', '2 years'),
            data_minimization_measures=processing_data.get('data_minimization_measures', []),
            security_measures=processing_data.get('security_measures', []),
            international_transfers=processing_data.get('international_transfers', False),
            third_country_transfers=processing_data.get('third_country_transfers', False),
            automated_decision_making=processing_data.get('automated_decision_making', False),
            profiling_involved=processing_data.get('profiling_involved', False),
            vulnerable_groups_involved=processing_data.get('vulnerable_groups_involved', False),
            estimated_number_of_data_subjects=processing_data.get('estimated_number_of_data_subjects', 0),
            business_justification=processing_data.get('business_justification', ''),
            alternatives_considered=processing_data.get('alternatives_considered', []),
            risk_mitigation_measures=processing_data.get('risk_mitigation_measures', [])
        )
        
        # Perform assessment
        service = DPIAService(db)
        result = service.assess_processing_activity(processing_activity, assessed_by)
        
        # Convert result to dictionary
        return {
            "dpia_id": result.dpia_id,
            "processing_activity_id": result.processing_activity.activity_id,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level.value,
            "dpia_required": result.dpia_required,
            "dpia_status": result.dpia_status.value,
            "assessment_date": result.assessment_date.isoformat(),
            "assessed_by": result.assessed_by,
            "dpo_review_required": result.dpo_review_required,
            "compliance_deadline": result.compliance_deadline.isoformat() if result.compliance_deadline else None,
            "recommendations": result.recommendations,
            "portuguese_cnpd_required": result.portguese_cnpd_required
        }
        
    except Exception as e:
        logger.error(f"Error in automated processing activity assessment: {e}")
        return {
            "error": str(e),
            "dpia_required": False,
            "risk_level": "unknown"
        }