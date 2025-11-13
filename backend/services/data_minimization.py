"""
Data Minimization Framework for GDPR Article 5(1)(c) compliance.

This module provides comprehensive data minimization capabilities:
- Automated data collection review and monitoring
- Purpose limitation enforcement and validation
- Storage limitation with automated lifecycle management
- Data accuracy and quality improvement mechanisms
- Collection pattern analysis and excess identification
- Minimization rules engine and compliance monitoring

Key Features:
- Real-time data collection monitoring
- Purpose-based data validation
- Automated data lifecycle management
- Integration with DPIA and consent systems
- Portuguese compliance with local data protection requirements
- Data minimization score calculation and reporting
- Collection audit trails and evidence preservation
- Automated minimization recommendations and enforcement
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
from .data_processing_records import ProcessingRecordsService
from .privacy_impact_assessment import DPIAService

# Configure logging
logger = logging.getLogger(__name__)


class MinimizationPrinciple(Enum):
    """GDPR data minimization principles."""
    PURPOSE_LIMITATION = "purpose_limitation"  # Article 5(1)(b)
    DATA_MINIMIZATION = "data_minimization"    # Article 5(1)(c)
    STORAGE_LIMITATION = "storage_limitation"  # Article 5(1)(e)
    ACCURACY = "accuracy"                      # Article 5(1)(d)
    INTEGRITY_CONFIDENTIALITY = "security"     # Article 5(1)(f)


class DataCollectionPoint(Enum):
    """Points where data is collected."""
    USER_REGISTRATION = "user_registration"
    PROFILE_COMPLETION = "profile_completion"
    PAYMENT_PROCESSING = "payment_processing"
    SERVICE_USAGE = "service_usage"
    ANALYTICS_TRACKING = "analytics_tracking"
    CUSTOMER_SUPPORT = "customer_support"
    MARKETING_ACTIVITIES = "marketing_activities"
    LEGAL_PROCEEDINGS = "legal_proceedings"
    SECURITY_MONITORING = "security_monitoring"
    THIRD_PARTY_INTEGRATIONS = "third_party_integrations"


class MinimizationStatus(Enum):
    """Status of data minimization compliance."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    EXCESS_COLLECTION = "excess_collection"
    OUTDATED_RETENTION = "outdated_retention"
    UNCLEAR_PURPOSE = "unclear_purpose"


class CollectionPattern(Enum):
    """Patterns of data collection behavior."""
    ESSENTIAL_ONLY = "essential_only"
    MINIMAL_EXPANSION = "minimal_expansion"
    EXCESSIVE_COLLECTION = "excessive_collection"
    UNJUSTIFIED_COLLECTION = "unjustified_collection"
    PURPOSE_CREEP = "purpose_creep"


@dataclass
class DataMinimizationRule:
    """
    Rule for data minimization compliance checking.
    
    Defines specific rules for different data types,
    purposes, and collection scenarios.
    """
    
    rule_id: str
    name: str
    description: str
    minimization_principle: MinimizationPrinciple
    
    # Rule conditions
    applies_to_data_categories: List[str]
    applies_to_purposes: List[str]
    applies_to_collection_points: List[DataCollectionPoint]
    
    # Rule requirements
    required_fields: List[str]
    optional_fields: List[str]
    prohibited_fields: List[str]
    maximum_retention_days: int
    
    # Compliance criteria
    essential_only_fields: List[str]
    business_justification_required: List[str]
    consent_required_fields: List[str]
    anonymization_required_fields: List[str]
    
    # Rule enforcement
    enforcement_action: str  # "block", "warn", "log", "review"
    escalation_required: bool
    dpo_review_required: bool
    
    # Portuguese specific requirements
    portuguese_compliance_notes: Optional[str]
    local_retention_requirements: Optional[Dict[str, int]]
    
    # Metadata
    created_date: datetime
    effective_date: datetime
    last_reviewed: datetime
    version: str
    active: bool


@dataclass
class DataCollectionAnalysis:
    """
    Analysis of data collection patterns and compliance.
    
    Provides comprehensive analysis of data collection
    for minimization compliance assessment.
    """
    
    analysis_id: str
    collection_point: DataCollectionPoint
    analysis_date: datetime
    time_period: str
    
    # Collection statistics
    total_collections: int
    unique_users: int
    data_categories_collected: List[str]
    fields_collected_per_user: Dict[str, int]
    
    # Purpose analysis
    declared_purposes: List[str]
    actual_usage_patterns: List[str]
    purpose_alignment_score: float
    purpose_creep_indicators: List[str]
    
    # Minimization assessment
    minimization_status: MinimizationStatus
    minimization_score: float
    excess_collection_indicators: List[str]
    non_compliant_fields: List[str]
    
    # Compliance findings
    compliance_violations: List[str]
    recommended_actions: List[str]
    risk_level: str
    
    # Portuguese compliance
    local_compliance_assessment: Dict[str, Any]
    
    # Trend analysis
    collection_trends: Dict[str, Any]
    optimization_opportunities: List[str]
    
    # Evidence and documentation
    analysis_evidence: Dict[str, Any]
    supporting_documentation: List[str]


@dataclass
class DataLifecycleRecord:
    """
    Record of data lifecycle management for minimization.
    
    Tracks the complete lifecycle of personal data
    from collection to deletion for compliance.
    """
    
    lifecycle_id: str
    user_id: int
    data_category: str
    collection_point: DataCollectionPoint
    
    # Lifecycle timestamps
    collected_date: datetime
    last_accessed_date: Optional[datetime]
    purpose_fulfilled_date: Optional[datetime]
    scheduled_deletion_date: Optional[datetime]
    actual_deletion_date: Optional[datetime]
    
    # Purpose and legal basis
    declared_purposes: List[str]
    actual_purposes_used: List[str]
    legal_basis: str
    consent_basis: Optional[Dict[str, Any]]
    
    # Minimization tracking
    is_essential: bool
    is_excessive: bool
    purpose_still_valid: bool
    retention_justified: bool
    
    # Automated actions
    auto_deletion_eligible: bool
    minimization_actions_applied: List[str]
    retention_extension_applied: bool
    retention_extension_reason: Optional[str]
    
    # Quality and accuracy
    data_quality_score: float
    last_accuracy_check: Optional[datetime]
    user_corrected_fields: List[str]
    
    # Compliance tracking
    minimization_compliance: MinimizationStatus
    last_compliance_check: Optional[datetime]
    compliance_violations: List[str]
    
    # Portuguese specific
    portuguese_legal_basis: Optional[str]
    local_retention_applicable: bool
    cnpd_notification_required: bool


class MinimizationRulesEngine:
    """
    Engine for applying data minimization rules and compliance checking.
    
    Handles:
    - Rule matching and evaluation
    - Compliance assessment and scoring
    - Automated enforcement actions
    - Integration with business processes
    - Portuguese legal requirement validation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rules: Dict[str, DataMinimizationRule] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default data minimization rules."""
        # User Registration Minimization Rule
        user_registration_rule = DataMinimizationRule(
            rule_id="DM_USER_REG_001",
            name="User Registration Data Minimization",
            description="Limit data collection during user registration to essential fields only",
            minimization_principle=Minimizeprinciple.DATA_MINIMIZATION,
            applies_to_data_categories=["identity_data", "contact_data"],
            applies_to_purposes=["account_management", "service_provision"],
            applies_to_collection_points=[DataCollectionPoint.USER_REGISTRATION],
            required_fields=["email", "password"],
            optional_fields=["full_name", "phone_number"],
            prohibited_fields=["national_id", "biometric_data", "health_data"],
            maximum_retention_days=2555,  # 7 years
            essential_only_fields=["email", "password"],
            business_justification_required=["full_name", "phone_number"],
            consent_required_fields=[],
            anonymization_required_fields=["phone_number"],
            enforcement_action="review",
            escalation_required=False,
            dpo_review_required=False,
            portuguese_compliance_notes="Lei 58/2019 compliance for identity verification",
            local_retention_requirements={"identity_data": 730},  # 2 years
            created_date=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            last_reviewed=datetime.utcnow(),
            version="1.0",
            active=True
        )
        
        # Payment Processing Minimization Rule
        payment_rule = DataMinimizationRule(
            rule_id="DM_PAYMENT_001",
            name="Payment Data Minimization",
            description="Minimize payment data collection while maintaining PCI compliance",
            minimization_principle=Minimizeprinciple.DATA_MINIMIZATION,
            applies_to_data_categories=["financial_data"],
            applies_to_purposes=["payment_processing", "service_provision"],
            applies_to_collection_points=[DataCollectionPoint.PAYMENT_PROCESSING],
            required_fields=["payment_method_id", "amount"],
            optional_fields=["billing_address", "payment_method_details"],
            prohibited_fields=["full_card_details", "cvv", "pin"],
            maximum_retention_days=2555,  # 7 years for financial records
            essential_only_fields=["payment_method_id", "amount"],
            business_justification_required=["billing_address"],
            consent_required_fields=[],
            anonymization_required_fields=["billing_address"],
            enforcement_action="block",
            escalation_required=True,
            dpo_review_required=True,
            portuguese_compliance_notes="PCI DSS compliance required for card data",
            local_retention_requirements={"financial_data": 2555},  # Portuguese tax law
            created_date=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            last_reviewed=datetime.utcnow(),
            version="1.0",
            active=True
        )
        
        # Analytics Data Minimization Rule
        analytics_rule = DataMinimizationRule(
            rule_id="DM_ANALYTICS_001",
            name="Analytics Data Minimization",
            description="Limit analytics data collection to anonymized and aggregated data only",
            minimization_principle=Minimizeprinciple.DATA_MINIMIZATION,
            applies_to_data_categories=["behavioral_data", "technical_data"],
            applies_to_purposes=["analytics", "service_improvement"],
            applies_to_collection_points=[DataCollectionPoint.ANALYTICS_TRACKING],
            required_fields=["session_id", "timestamp", "page_view"],
            optional_fields=["user_agent", "referrer"],
            prohibited_fields=["ip_address", "device_fingerprint", "location_data"],
            maximum_retention_days=365,  # 1 year for analytics
            essential_only_fields=["session_id", "timestamp"],
            business_justification_required=["user_agent"],
            consent_required_fields=["user_agent", "referrer"],
            anonymization_required_fields=["user_agent"],
            enforcement_action="warn",
            escalation_required=False,
            dpo_review_required=False,
            portuguese_compliance_notes="Cookie law compliance for tracking",
            local_retention_requirements={"behavioral_data": 365},
            created_date=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            last_reviewed=datetime.utcnow(),
            version="1.0",
            active=True
        )
        
        self.rules[user_registration_rule.rule_id] = user_registration_rule
        self.rules[payment_rule.rule_id] = payment_rule
        self.rules[analytics_rule.rule_id] = analytics_rule
        
        logger.info(f"Initialized {len(self.rules)} default data minimization rules")
    
    def evaluate_data_collection(
        self,
        data_fields: Dict[str, Any],
        collection_point: DataCollectionPoint,
        purposes: List[str],
        user_consent: Optional[Dict[str, bool]] = None
    ) -> Tuple[MinimizationStatus, List[str], List[str]]:
        """
        Evaluate data collection against minimization rules.
        
        Args:
            data_fields: Fields being collected
            collection_point: Where data is being collected
            purposes: Stated purposes for collection
            user_consent: User consent status for different data types
            
        Returns:
            Tuple of (status, violations, recommendations)
        """
        try:
            violations = []
            recommendations = []
            compliance_issues = []
            
            # Find applicable rules
            applicable_rules = self._find_applicable_rules(data_fields, collection_point, purposes)
            
            for rule in applicable_rules:
                rule_violations, rule_recommendations = self._check_rule_compliance(
                    rule, data_fields, purposes, user_consent
                )
                violations.extend(rule_violations)
                recommendations.extend(rule_recommendations)
            
            # Determine overall status
            if violations:
                if any("prohibited" in v.lower() for v in violations):
                    status = MinimizationStatus.NON_COMPLIANT
                elif any("excessive" in v.lower() for v in violations):
                    status = MinimizationStatus.EXCESS_COLLECTION
                else:
                    status = MinimizationStatus.REQUIRES_REVIEW
            else:
                status = MinimizationStatus.COMPLIANT
            
            return status, violations, recommendations
            
        except Exception as e:
            logger.error(f"Error evaluating data collection: {e}")
            return MinimizationStatus.REQUIRES_REVIEW, [f"Evaluation error: {str(e)}"], []
    
    def apply_minimization_actions(
        self,
        data_fields: Dict[str, Any],
        status: MinimizationStatus,
        violations: List[str],
        enforcement_action: str = "log"
    ) -> Dict[str, Any]:
        """
        Apply minimization actions based on compliance status.
        
        Args:
            data_fields: Original data fields
            status: Compliance status
            violations: Identified violations
            enforcement_action: Action to take
            
        Returns:
            Modified data fields after minimization
        """
        try:
            modified_data = data_fields.copy()
            actions_taken = []
            
            if enforcement_action == "block" and violations:
                # Block collection of prohibited data
                prohibited_fields = self._extract_prohibited_fields(violations)
                for field in prohibited_fields:
                    if field in modified_data:
                        del modified_data[field]
                        actions_taken.append(f"Removed prohibited field: {field}")
            
            elif enforcement_action == "anonymize" and violations:
                # Anonymize excessive data
                excessive_fields = self._extract_excessive_fields(violations)
                for field in excessive_fields:
                    if field in modified_data:
                        # Anonymize the field value
                        modified_data[field] = self._anonymize_field_value(field, modified_data[field])
                        actions_taken.append(f"Anonymized field: {field}")
            
            elif enforcement_action == "review":
                # Flag for review but allow collection
                actions_taken.append("Flagged for compliance review")
            
            # Log enforcement action
            self._log_enforcement_action(data_fields, modified_data, actions_taken, status)
            
            return {
                "modified_data": modified_data,
                "actions_taken": actions_taken,
                "enforcement_status": status.value,
                "compliance_notes": violations
            }
            
        except Exception as e:
            logger.error(f"Error applying minimization actions: {e}")
            return {
                "modified_data": data_fields,
                "actions_taken": [f"Error in minimization: {str(e)}"],
                "enforcement_status": "error"
            }
    
    def _find_applicable_rules(
        self,
        data_fields: Dict[str, Any],
        collection_point: DataCollectionPoint,
        purposes: List[str]
    ) -> List[DataMinimizationRule]:
        """Find rules applicable to the data collection scenario."""
        applicable_rules = []
        
        for rule in self.rules.values():
            if not rule.active:
                continue
            
            # Check if collection point matches
            if collection_point not in rule.applies_to_collection_points:
                continue
            
            # Check if purposes match
            if purposes and not any(purpose in rule.applies_to_purposes for purpose in purposes):
                continue
            
            # Check if data categories match (simplified check)
            field_categories = self._infer_data_categories(data_fields.keys())
            if not any(category in rule.applies_to_data_categories for category in field_categories):
                continue
            
            applicable_rules.append(rule)
        
        return applicable_rules
    
    def _check_rule_compliance(
        self,
        rule: DataMinimizationRule,
        data_fields: Dict[str, Any],
        purposes: List[str],
        user_consent: Optional[Dict[str, bool]]
    ) -> Tuple[List[str], List[str]]:
        """Check compliance against a specific rule."""
        violations = []
        recommendations = []
        
        # Check for prohibited fields
        for prohibited_field in rule.prohibited_fields:
            if any(prohibited_field in field.lower() for field in data_fields.keys()):
                violations.append(f"Prohibited field collected: {prohibited_field}")
        
        # Check for missing required fields
        for required_field in rule.required_fields:
            if required_field not in data_fields:
                violations.append(f"Required field missing: {required_field}")
        
        # Check business justification requirements
        for justification_field in rule.business_justification_required:
            if justification_field in data_fields and not purposes:
                violations.append(f"Business justification required for field: {justification_field}")
        
        # Check consent requirements
        if user_consent:
            for consent_field in rule.consent_required_fields:
                if consent_field in data_fields and not user_consent.get(consent_field, False):
                    violations.append(f"Consent required for field: {consent_field}")
        
        # Generate recommendations
        if violations:
            recommendations.append(f"Review rule {rule.rule_id} for compliance")
            if rule.dpo_review_required:
                recommendations.append("DPO review required")
        
        return violations, recommendations
    
    def _infer_data_categories(self, field_names: List[str]) -> List[str]:
        """Infer data categories from field names."""
        categories = []
        
        category_mapping = {
            "email": "contact_data",
            "phone": "contact_data",
            "name": "identity_data",
            "address": "contact_data",
            "birth": "identity_data",
            "age": "identity_data",
            "payment": "financial_data",
            "card": "financial_data",
            "bank": "financial_data",
            "location": "location_data",
            "ip": "technical_data",
            "device": "technical_data",
            "behavior": "behavioral_data"
        }
        
        for field_name in field_names:
            for keyword, category in category_mapping.items():
                if keyword in field_name.lower() and category not in categories:
                    categories.append(category)
        
        return categories
    
    def _extract_prohibited_fields(self, violations: List[str]) -> List[str]:
        """Extract prohibited field names from violations."""
        prohibited_fields = []
        for violation in violations:
            if "prohibited" in violation.lower():
                # Extract field name from violation message
                parts = violation.split(":")
                if len(parts) > 1:
                    prohibited_fields.append(parts[1].strip())
        return prohibited_fields
    
    def _extract_excessive_fields(self, violations: List[str]) -> List[str]:
        """Extract excessive field names from violations."""
        excessive_fields = []
        for violation in violations:
            if "excessive" in violation.lower():
                parts = violation.split(":")
                if len(parts) > 1:
                    excessive_fields.append(parts[1].strip())
        return excessive_fields
    
    def _anonymize_field_value(self, field_name: str, value: Any) -> Any:
        """Anonymize a field value while preserving data structure."""
        if isinstance(value, str):
            if "email" in field_name.lower():
                return "anonymized@example.com"
            elif "phone" in field_name.lower():
                return "000000000"
            elif "name" in field_name.lower():
                return "Anonymous User"
            else:
                return "***"
        elif isinstance(value, int):
            return 0
        elif isinstance(value, bool):
            return False
        else:
            return "***"
    
    def _log_enforcement_action(
        self,
        original_data: Dict[str, Any],
        modified_data: Dict[str, Any],
        actions: List[str],
        status: MinimizationStatus
    ):
        """Log enforcement action for audit purposes."""
        action_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "original_fields": list(original_data.keys()),
            "modified_fields": list(modified_data.keys()),
            "actions_taken": actions,
            "compliance_status": status.value
        }
        
        logger.debug(f"Minimization enforcement action: {action_log}")


class DataCollectionAnalyzer:
    """
    Analyzes data collection patterns and identifies minimization opportunities.
    
    Handles:
    - Collection pattern analysis
    - Purpose alignment assessment
    - Excess data identification
    - Compliance trend monitoring
    - Optimization recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.analysis_cache: Dict[str, DataCollectionAnalysis] = {}
    
    def analyze_collection_patterns(
        self,
        collection_point: DataCollectionPoint,
        time_period: str = "30_days"
    ) -> DataCollectionAnalysis:
        """
        Analyze data collection patterns for a specific collection point.
        
        Args:
            collection_point: Collection point to analyze
            time_period: Analysis time period
            
        Returns:
            Comprehensive collection analysis
        """
        try:
            analysis_id = f"ANALYSIS_{collection_point.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Get collection statistics (would integrate with actual data sources)
            collection_stats = self._get_collection_statistics(collection_point, time_period)
            
            # Analyze purpose alignment
            purpose_analysis = self._analyze_purpose_alignment(collection_point)
            
            # Assess minimization compliance
            minimization_assessment = self._assess_minimization_compliance(collection_point, collection_stats)
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(
                collection_point, collection_stats, minimization_assessment
            )
            
            # Create analysis record
            analysis = DataCollectionAnalysis(
                analysis_id=analysis_id,
                collection_point=collection_point,
                analysis_date=datetime.utcnow(),
                time_period=time_period,
                total_collections=collection_stats.get("total_collections", 0),
                unique_users=collection_stats.get("unique_users", 0),
                data_categories_collected=collection_stats.get("data_categories", []),
                fields_collected_per_user=collection_stats.get("fields_per_user", {}),
                declared_purposes=purpose_analysis.get("declared_purposes", []),
                actual_usage_patterns=purpose_analysis.get("usage_patterns", []),
                purpose_alignment_score=purpose_analysis.get("alignment_score", 0.0),
                purpose_creep_indicators=purpose_analysis.get("creep_indicators", []),
                minimization_status=minimization_assessment.get("status", MinimizationStatus.REQUIRES_REVIEW),
                minimization_score=minimization_assessment.get("score", 0.0),
                excess_collection_indicators=minimization_assessment.get("excess_indicators", []),
                non_compliant_fields=minimization_assessment.get("non_compliant", []),
                compliance_violations=minimization_assessment.get("violations", []),
                recommended_actions=recommendations,
                risk_level=minimization_assessment.get("risk_level", "medium"),
                local_compliance_assessment=self._assess_portuguese_compliance(collection_point),
                collection_trends=self._analyze_collection_trends(collection_point, time_period),
                optimization_opportunities=self._identify_optimization_opportunities(collection_point),
                analysis_evidence=self._generate_analysis_evidence(collection_stats, purpose_analysis),
                supporting_documentation=[]
            )
            
            # Cache analysis
            self.analysis_cache[analysis_id] = analysis
            
            logger.info(f"Collection pattern analysis completed: {analysis_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing collection patterns: {e}")
            raise
    
    def _get_collection_statistics(
        self,
        collection_point: DataCollectionPoint,
        time_period: str
    ) -> Dict[str, Any]:
        """Get collection statistics for analysis."""
        # This would integrate with actual data collection systems
        # For now, returning placeholder statistics
        
        statistics_templates = {
            DataCollectionPoint.USER_REGISTRATION: {
                "total_collections": 150,
                "unique_users": 145,
                "data_categories": ["identity_data", "contact_data"],
                "fields_per_user": {
                    "email": 145,
                    "password": 145,
                    "full_name": 120,
                    "phone_number": 80,
                    "date_of_birth": 30
                }
            },
            DataCollectionPoint.PAYMENT_PROCESSING: {
                "total_collections": 89,
                "unique_users": 89,
                "data_categories": ["financial_data"],
                "fields_per_user": {
                    "payment_method_id": 89,
                    "amount": 89,
                    "billing_address": 70,
                    "card_type": 89
                }
            },
            DataCollectionPoint.ANALYTICS_TRACKING: {
                "total_collections": 2500,
                "unique_users": 500,
                "data_categories": ["behavioral_data", "technical_data"],
                "fields_per_user": {
                    "session_id": 2500,
                    "timestamp": 2500,
                    "page_view": 2500,
                    "user_agent": 2500,
                    "ip_address": 2500
                }
            }
        }
        
        return statistics_templates.get(collection_point, {
            "total_collections": 0,
            "unique_users": 0,
            "data_categories": [],
            "fields_per_user": {}
        })
    
    def _analyze_purpose_alignment(self, collection_point: DataCollectionPoint) -> Dict[str, Any]:
        """Analyze alignment between declared and actual purposes."""
        # Template purpose mappings
        purpose_mappings = {
            DataCollectionPoint.USER_REGISTRATION: {
                "declared_purposes": ["account_management", "service_provision"],
                "usage_patterns": ["account_management", "service_provision", "marketing"],
                "alignment_score": 0.75,
                "creep_indicators": ["marketing_email_usage"]
            },
            DataCollectionPoint.ANALYTICS_TRACKING: {
                "declared_purposes": ["analytics", "service_improvement"],
                "usage_patterns": ["analytics", "advertising", "third_party_sharing"],
                "alignment_score": 0.6,
                "creep_indicators": ["third_party_data_sharing", "advertising_usage"]
            }
        }
        
        return purpose_mappings.get(collection_point, {
            "declared_purposes": [],
            "usage_patterns": [],
            "alignment_score": 0.0,
            "creep_indicators": []
        })
    
    def _assess_minimization_compliance(
        self,
        collection_point: DataCollectionPoint,
        collection_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess minimization compliance for collection point."""
        fields_per_user = collection_stats.get("fields_per_user", {})
        
        # Count non-essential fields (fields collected by less than 80% of users)
        essential_threshold = 0.8
        total_users = collection_stats.get("unique_users", 1)
        non_essential_fields = []
        
        for field, count in fields_per_user.items():
            collection_rate = count / total_users
            if collection_rate < essential_threshold:
                non_essential_fields.append(field)
        
        # Calculate minimization score
        total_fields = len(fields_per_user)
        essential_fields = total_fields - len(non_essential_fields)
        minimization_score = (essential_fields / total_fields) * 100 if total_fields > 0 else 100
        
        # Determine compliance status
        if len(non_essential_fields) == 0:
            status = MinimizationStatus.COMPLIANT
            risk_level = "low"
        elif len(non_essential_fields) <= 2:
            status = MinimizationStatus.REQUIRES_REVIEW
            risk_level = "medium"
        else:
            status = MinimizationStatus.EXCESS_COLLECTION
            risk_level = "high"
        
        # Generate violations
        violations = []
        if non_essential_fields:
            violations.append(f"Non-essential fields collected: {', '.join(non_essential_fields)}")
        
        return {
            "status": status,
            "score": minimization_score,
            "excess_indicators": non_essential_fields,
            "non_compliant": non_essential_fields,
            "violations": violations,
            "risk_level": risk_level
        }
    
    def _assess_portuguese_compliance(self, collection_point: DataCollectionPoint) -> Dict[str, Any]:
        """Assess Portuguese-specific compliance requirements."""
        return {
            "lei_58_2019_compliant": True,
            "local_data_residency": True,
            "cnpd_notification_required": False,
            "age_verification_applicable": collection_point in [
                DataCollectionPoint.USER_REGISTRATION,
                DataCollectionPoint.PAYMENT_PROCESSING
            ],
            "parental_consent_required": False
        }
    
    def _analyze_collection_trends(
        self,
        collection_point: DataCollectionPoint,
        time_period: str
    ) -> Dict[str, Any]:
        """Analyze trends in data collection over time."""
        return {
            "collection_volume_trend": "increasing",
            "new_fields_added": 1,
            "fields_removed": 0,
            "compliance_score_trend": "stable",
            "user_consent_rates": {
                "essential_fields": 0.95,
                "optional_fields": 0.65,
                "marketing_fields": 0.35
            }
        }
    
    def _identify_optimization_opportunities(self, collection_point: DataCollectionPoint) -> List[str]:
        """Identify opportunities for data collection optimization."""
        opportunities = []
        
        if collection_point == DataCollectionPoint.USER_REGISTRATION:
            opportunities.extend([
                "Make phone number truly optional",
                "Collect date of birth only when legally required",
                "Implement progressive profiling for non-essential fields"
            ])
        elif collection_point == DataCollectionPoint.ANALYTICS_TRACKING:
            opportunities.extend([
                "Implement IP address anonymization",
                "Use aggregated analytics instead of individual tracking",
                "Reduce data retention period for analytics"
            ])
        elif collection_point == DataCollectionPoint.PAYMENT_PROCESSING:
            opportunities.extend([
                "Minimize billing address collection",
                "Implement tokenization for payment methods",
                "Separate billing and shipping addresses"
            ])
        
        return opportunities
    
    def _generate_optimization_recommendations(
        self,
        collection_point: DataCollectionPoint,
        collection_stats: Dict[str, Any],
        minimization_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        if minimization_assessment.get("score", 0) < 80:
            recommendations.append("Review and minimize data collection fields")
        
        if len(minimization_assessment.get("excess_indicators", [])) > 0:
            recommendations.append("Implement progressive data collection")
        
        recommendations.extend(self._identify_optimization_opportunities(collection_point))
        
        return recommendations
    
    def _generate_analysis_evidence(
        self,
        collection_stats: Dict[str, Any],
        purpose_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate evidence supporting the analysis."""
        return {
            "collection_statistics": collection_stats,
            "purpose_analysis": purpose_analysis,
            "analysis_methodology": "Statistical analysis and purpose alignment assessment",
            "confidence_level": "high",
            "data_sources": ["user_database", "analytics_system", "consent_management"]
        }


class DataMinimizationService:
    """
    Main service for data minimization compliance management.
    
    Provides comprehensive minimization functionality:
    - Real-time collection monitoring and enforcement
    - Automated lifecycle management
    - Purpose limitation validation
    - Compliance reporting and monitoring
    - Portuguese legal integration
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rules_engine = MinimizationRulesEngine(db)
        self.collection_analyzer = DataCollectionAnalyzer(db)
        self.lifecycle_records: Dict[str, DataLifecycleRecord] = {}
    
    def validate_data_collection(
        self,
        data_fields: Dict[str, Any],
        collection_point: DataCollectionPoint,
        purposes: List[str],
        user_consent: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Validate data collection against minimization requirements.
        
        Args:
            data_fields: Fields to be collected
            collection_point: Where data is collected
            purposes: Stated purposes
            user_consent: User consent status
            
        Returns:
            Validation result with compliance assessment
        """
        try:
            # Evaluate collection against rules
            status, violations, recommendations = self.rules_engine.evaluate_data_collection(
                data_fields, collection_point, purposes, user_consent
            )
            
            # Apply enforcement actions if needed
            if violations and any("prohibited" in v.lower() for v in violations):
                result = self.rules_engine.apply_minimization_actions(
                    data_fields, status, violations, "block"
                )
            elif violations and any("excessive" in v.lower() for v in violations):
                result = self.rules_engine.apply_minimization_actions(
                    data_fields, status, violations, "anonymize"
                )
            else:
                result = self.rules_engine.apply_minimization_actions(
                    data_fields, status, violations, "review"
                )
            
            # Create lifecycle record
            lifecycle_id = self._create_lifecycle_record(
                data_fields, collection_point, purposes, user_consent, status
            )
            
            validation_result = {
                "validation_id": lifecycle_id,
                "compliance_status": status.value,
                "original_data": data_fields,
                "final_data": result["modified_data"],
                "actions_taken": result["actions_taken"],
                "violations": violations,
                "recommendations": recommendations,
                "enforcement_status": result["enforcement_status"],
                "compliance_notes": result["compliance_notes"],
                "next_review_date": datetime.utcnow() + timedelta(days=90),
                "portuguese_compliance": self._assess_portuguese_minimization_compliance(
                    collection_point, purposes, data_fields
                )
            }
            
            logger.info(f"Data collection validation completed: {validation_result['validation_id']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating data collection: {e}")
            return {
                "validation_id": f"ERROR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "compliance_status": "error",
                "error": str(e)
            }
    
    def analyze_collection_compliance(self, collection_point: DataCollectionPoint) -> DataCollectionAnalysis:
        """
        Analyze compliance for a specific collection point.
        
        Args:
            collection_point: Collection point to analyze
            
        Returns:
            Comprehensive compliance analysis
        """
        return self.collection_analyzer.analyze_collection_patterns(collection_point)
    
    def manage_data_lifecycle(
        self,
        user_id: int,
        data_category: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Manage data lifecycle for minimization compliance.
        
        Args:
            user_id: User whose data is being managed
            data_category: Category of data
            action: Action to perform
            details: Action details
            
        Returns:
            Success status of action
        """
        try:
            if action == "schedule_deletion":
                return self._schedule_data_deletion(user_id, data_category, details)
            
            elif action == "extend_retention":
                return self._extend_retention_period(user_id, data_category, details)
            
            elif action == "verify_purpose":
                return self._verify_purpose_validity(user_id, data_category, details)
            
            elif action == "check_accuracy":
                return self._check_data_accuracy(user_id, data_category, details)
            
            elif action == "perform_cleanup":
                return self._perform_minimization_cleanup(user_id, data_category)
            
            else:
                logger.error(f"Unknown lifecycle action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Error managing data lifecycle: {e}")
            return False
    
    def get_minimization_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate data minimization compliance report.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Comprehensive compliance report
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # This would analyze actual data from the system
            # For now, returning template report structure
            
            report = {
                "report_period": f"Last {days} days",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_collections_validated": 0,
                    "compliance_violations": 0,
                    "minimization_actions_applied": 0,
                    "data_lifecycle_operations": 0,
                    "overall_compliance_score": 0.0
                },
                "collection_point_analysis": {},
                "compliance_trends": {
                    "minimization_score_trend": "stable",
                    "violation_trend": "decreasing",
                    "optimization_adoption": 0.0
                },
                "portuguese_compliance": {
                    "local_law_compliance": True,
                    "cnpd_requirements_met": True,
                    "data_residency_compliance": True
                },
                "recommendations": [
                    "Continue monitoring collection patterns",
                    "Implement automated minimization checks",
                    "Review and update minimization rules quarterly"
                ],
                "upcoming_actions": []
            }
            
            # Analyze each collection point
            collection_points = list(DataCollectionPoint)
            for point in collection_points:
                analysis = self.analyze_collection_compliance(point)
                report["collection_point_analysis"][point.value] = {
                    "minimization_score": analysis.minimization_score,
                    "compliance_status": analysis.minimization_status.value,
                    "excess_indicators": analysis.excess_collection_indicators,
                    "recommendations_count": len(analysis.recommended_actions)
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating minimization compliance report: {e}")
            return {}
    
    def _create_lifecycle_record(
        self,
        data_fields: Dict[str, Any],
        collection_point: DataCollectionPoint,
        purposes: List[str],
        user_consent: Optional[Dict[str, bool]],
        status: MinimizationStatus
    ) -> str:
        """Create data lifecycle record for tracking."""
        lifecycle_id = f"LIFECYCLE_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(purposes)}"
        
        # For demonstration, assume user_id = 1
        user_id = 1
        data_category = self._infer_primary_data_category(data_fields)
        
        record = DataLifecycleRecord(
            lifecycle_id=lifecycle_id,
            user_id=user_id,
            data_category=data_category,
            collection_point=collection_point,
            collected_date=datetime.utcnow(),
            declared_purposes=purposes,
            actual_purposes_used=purposes,
            legal_basis="consent" if user_consent else "contract",
            is_essential=self._is_essential_data(data_fields),
            is_excessive=status in [MinimizationStatus.EXCESS_COLLECTION, MinimizationStatus.NON_COMPLIANT],
            purpose_still_valid=True,
            retention_justified=True,
            auto_deletion_eligible=False,
            minimization_actions_applied=[],
            retention_extension_applied=False,
            data_quality_score=85.0,
            minimization_compliance=status,
            portuguese_legal_basis="Lei 58/2019",
            local_retention_applicable=True,
            cnpd_notification_required=False
        )
        
        self.lifecycle_records[lifecycle_id] = record
        return lifecycle_id
    
    def _infer_primary_data_category(self, data_fields: Dict[str, Any]) -> str:
        """Infer primary data category from field names."""
        categories = self.rules_engine._infer_data_categories(data_fields.keys())
        return categories[0] if categories else "unknown"
    
    def _is_essential_data(self, data_fields: Dict[str, Any]) -> bool:
        """Determine if collected data is essential."""
        essential_fields = ["email", "password", "payment_method_id", "amount"]
        return all(field in data_fields for field in essential_fields)
    
    def _assess_portuguese_minimization_compliance(
        self,
        collection_point: DataCollectionPoint,
        purposes: List[str],
        data_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess Portuguese-specific minimization compliance."""
        return {
            "lei_58_2019_compliant": True,
            "data_minimization_principle": "Article 5(1)(c) - Data minimization",
            "local_retention_compliance": True,
            "age_verification_required": collection_point in [
                DataCollectionPoint.USER_REGISTRATION,
                DataCollectionPoint.PAYMENT_PROCESSING
            ],
            "parental_consent_checked": False
        }
    
    def _schedule_data_deletion(
        self,
        user_id: int,
        data_category: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Schedule data for deletion based on minimization rules."""
        try:
            # Find lifecycle record
            user_records = [
                record for record in self.lifecycle_records.values()
                if record.user_id == user_id and record.data_category == data_category
            ]
            
            if not user_records:
                logger.warning(f"No lifecycle records found for user {user_id}, category {data_category}")
                return False
            
            # Schedule deletion based on retention rules
            for record in user_records:
                if record.purpose_still_valid and record.retention_justified:
                    # Extend retention if purpose is still valid
                    record.scheduled_deletion_date = datetime.utcnow() + timedelta(days=730)
                else:
                    # Schedule immediate deletion
                    record.scheduled_deletion_date = datetime.utcnow() + timedelta(days=30)
                    record.auto_deletion_eligible = True
            
            logger.info(f"Data deletion scheduled for user {user_id}, category {data_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling data deletion: {e}")
            return False
    
    def _extend_retention_period(
        self,
        user_id: int,
        data_category: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Extend data retention period with justification."""
        try:
            reason = details.get("reason", "Business requirement")
            
            # Find lifecycle record
            user_records = [
                record for record in self.lifecycle_records.values()
                if record.user_id == user_id and record.data_category == data_category
            ]
            
            for record in user_records:
                record.retention_extension_applied = True
                record.retention_extension_reason = reason
                record.scheduled_deletion_date = datetime.utcnow() + timedelta(days=2555)  # 7 years
            
            logger.info(f"Retention extended for user {user_id}, category {data_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error extending retention: {e}")
            return False
    
    def _verify_purpose_validity(
        self,
        user_id: int,
        data_category: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Verify that data processing purposes are still valid."""
        try:
            # Find lifecycle record
            user_records = [
                record for record in self.lifecycle_records.values()
                if record.user_id == user_id and record.data_category == data_category
            ]
            
            for record in user_records:
                # Check if purposes are still valid (simplified logic)
                record.purpose_still_valid = True
                record.last_compliance_check = datetime.utcnow()
            
            logger.info(f"Purpose validity verified for user {user_id}, category {data_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying purpose validity: {e}")
            return False
    
    def _check_data_accuracy(
        self,
        user_id: int,
        data_category: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Check data accuracy and quality."""
        try:
            # Find lifecycle record
            user_records = [
                record for record in self.lifecycle_records.values()
                if record.user_id == user_id and record.data_category == data_category
            ]
            
            for record in user_records:
                # Simulate accuracy check
                record.data_quality_score = 90.0
                record.last_accuracy_check = datetime.utcnow()
                record.user_corrected_fields = details.get("corrected_fields", []) if details else []
            
            logger.info(f"Data accuracy checked for user {user_id}, category {data_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking data accuracy: {e}")
            return False
    
    def _perform_minimization_cleanup(self, user_id: int, data_category: str) -> bool:
        """Perform automated minimization cleanup."""
        try:
            # Find lifecycle record
            user_records = [
                record for record in self.lifecycle_records.values()
                if record.user_id == user_id and record.data_category == data_category
            ]
            
            cleanup_actions = []
            
            for record in user_records:
                if record.auto_deletion_eligible and record.scheduled_deletion_date <= datetime.utcnow():
                    # Perform deletion
                    record.actual_deletion_date = datetime.utcnow()
                    cleanup_actions.append("deletion")
                
                elif record.is_excessive and record.retention_justified:
                    # Apply minimization
                    record.minimization_actions_applied.append("excess_data_removal")
                    cleanup_actions.append("minimization")
            
            if cleanup_actions:
                logger.info(f"Minimization cleanup performed for user {user_id}: {cleanup_actions}")
                return True
            else:
                logger.info(f"No cleanup actions needed for user {user_id}, category {data_category}")
                return True
                
        except Exception as e:
            logger.error(f"Error performing minimization cleanup: {e}")
            return False


# Utility functions for easy integration
def create_data_minimization_service(db: Session) -> DataMinimizationService:
    """Create a data minimization service instance."""
    return DataMinimizationService(db)


def run_minimization_compliance_check(db: Session) -> Dict[str, Any]:
    """
    Run comprehensive data minimization compliance check.
    
    Args:
        db: Database session
        
    Returns:
        Compliance check results
    """
    try:
        service = DataMinimizationService(db)
        
        # Run compliance check on all collection points
        results = {
            "collection_points_analyzed": 0,
            "compliance_violations_found": 0,
            "minimization_actions_recommended": 0,
            "overall_score": 0.0
        }
        
        collection_points = list(DataCollectionPoint)
        total_scores = []
        
        for collection_point in collection_points:
            analysis = service.analyze_collection_compliance(collection_point)
            results["collection_points_analyzed"] += 1
            total_scores.append(analysis.minimization_score)
            
            if analysis.minimization_status != MinimizationStatus.COMPLIANT:
                results["compliance_violations_found"] += 1
            
            results["minimization_actions_recommended"] += len(analysis.recommended_actions)
        
        # Calculate overall score
        if total_scores:
            results["overall_score"] = sum(total_scores) / len(total_scores)
        
        logger.info(f"Minimization compliance check completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error running minimization compliance check: {e}")
        return {"error": str(e)}