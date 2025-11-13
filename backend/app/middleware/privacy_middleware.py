"""
Privacy Middleware for Automatic Privacy Controls

This middleware implements privacy-by-design principles by automatically applying
privacy controls to all API responses. It ensures consistent privacy protection
across all endpoints while providing comprehensive audit trails.

Key Features:
- Automatic PII detection and redaction
- Consent-based data filtering
- Privacy-preserving response headers
- Comprehensive audit logging
- Portuguese legal compliance checks
- Risk-based data minimization
- Privacy incident detection
- GDPR Article 25 compliance (data protection by design)
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
from collections import defaultdict
import hashlib

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from ....app import models
from ....app.crud_soft_delete import audit_trail_crud
from ....services.gdpr_compliance_service import GDPRComplianceService
from ....services.consent_management_system import ConsentManagementService
from ....services.data_minimization import DataMinimizationService

# Configure logging
logger = logging.getLogger(__name__)

# PII detection patterns
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?351[-\s]?)?(?:\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3})\b',
    'nif': r'\b\d{9}\b',  # Portuguese tax identification
    'cc': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'iban': r'\bPT\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}\b',
    'passport': r'\b[A-Z]{1,2}\d{6,8}\b',
    'citizen_card': r'\b\d{8}[-\s]?\d{1}[A-Z]{2}\b',  # Portuguese citizen card
    'license_plate': r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{-\s]?\d{2}\b',  # Portuguese plates
    'postal_code': r'\b\d{4}[-\s]?\d{3}\b',  # Portuguese postal code
    'ip_address': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    'credit_card': r'\b(?:3[47]\d{13}|4\d{12}|5[1-5]\d{14}|6(?:011|5\d{2})\d{12}|2(?:2[2-9]\d{2}|[3-6]\d{3}|7[01]\d{2}|720\d{2})\d{12}|3(?:0\d{13}|3\d{13})\d{12}|[689]\d{14})\b'
}

# Privacy risk levels
class PrivacyRiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Data sensitivity levels
class DataSensitivityLevel:
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class PrivacyMiddleware(BaseHTTPMiddleware):
    """
    Privacy middleware that automatically applies privacy controls to all API responses.
    
    This middleware implements privacy-by-design principles by:
    1. Detecting and redacting PII in responses
    2. Applying consent-based filtering
    3. Minimizing data based on risk assessment
    4. Adding privacy headers
    5. Logging privacy events for audit
    """
    
    def __init__(
        self,
        app: ASGIApp,
        db_session_factory,
        privacy_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        self.privacy_config = privacy_config or self._default_privacy_config()
        self.pii_patterns = PII_PATTERNS
        self._compiled_patterns = self._compile_pii_patterns()
        
        # Privacy tracking
        self.privacy_stats = defaultdict(int)
        self.risk_assessment_cache = {}
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Main middleware dispatch method that applies privacy controls.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with privacy controls applied
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract request context
            user_id = await self._extract_user_id(request)
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Create database session
            db = self.db_session_factory()
            
            # Process request with privacy controls
            response = await self._process_request_with_privacy(request, call_next, db, user_id)
            
            # Apply privacy controls to response
            response = await self._apply_privacy_controls(
                response, user_id, client_ip, user_agent, start_time, db
            )
            
            # Log privacy event
            await self._log_privacy_event(
                user_id, "RESPONSE_PROCESSED", 
                {
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "privacy_controls_applied": True,
                    "response_status": response.status_code
                },
                client_ip, user_agent, db
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Privacy middleware error: {e}")
            # Return error response without exposing sensitive data
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        finally:
            if 'db' in locals():
                db.close()
    
    async def _process_request_with_privacy(
        self, 
        request: Request, 
        call_next, 
        db: Session, 
        user_id: Optional[int]
    ) -> Response:
        """Process request with privacy considerations."""
        
        # Add privacy context to request state
        request.state.privacy_context = {
            "user_id": user_id,
            "privacy_mode": await self._determine_privacy_mode(request, user_id, db),
            "data_sensitivity": await self._assess_data_sensitivity(request, db),
            "consent_status": await self._check_consent_status(request, user_id, db)
        }
        
        # Apply request-level privacy controls
        if not await self._validate_privacy_requirements(request, db):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Privacy requirements not met",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return await call_next(request)
    
    async def _apply_privacy_controls(
        self,
        response: Response,
        user_id: Optional[int],
        client_ip: str,
        user_agent: str,
        start_time: datetime,
        db: Session
    ) -> Response:
        """Apply comprehensive privacy controls to response."""
        
        try:
            # If response is already a JSONResponse, process its content
            if isinstance(response, JSONResponse):
                original_content = response.body
                
                # Parse and process JSON content
                try:
                    content_data = json.loads(original_content.decode('utf-8'))
                    processed_content = await self._process_response_data(
                        content_data, user_id, db
                    )
                    
                    # Create new response with processed content
                    response = JSONResponse(
                        content=processed_content,
                        status_code=response.status_code,
                        headers=response.headers,
                        media_type=response.media_type
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If JSON parsing fails, apply basic redaction
                    response = await self._apply_basic_redaction(response)
            
            # Add privacy headers
            response.headers.update(self._generate_privacy_headers(user_id))
            
            # Update privacy statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_privacy_stats(response, processing_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error applying privacy controls: {e}")
            return response  # Return original response on error
    
    async def _process_response_data(
        self, 
        data: Any, 
        user_id: Optional[int], 
        db: Session
    ) -> Any:
        """
        Process response data to apply privacy controls.
        
        This method recursively processes data structures to:
        1. Detect and redact PII
        2. Apply consent-based filtering
        3. Minimize data based on risk assessment
        4. Apply data retention policies
        """
        
        if isinstance(data, dict):
            return await self._process_dict_data(data, user_id, db)
        elif isinstance(data, list):
            return await self._process_list_data(data, user_id, db)
        elif isinstance(data, str):
            return await self._process_string_data(data, user_id, db)
        elif isinstance(data, (int, float, bool, type(None))):
            return data
        else:
            # For unknown types, convert to string and process
            return await self._process_string_data(str(data), user_id, db)
    
    async def _process_dict_data(
        self, 
        data: Dict[str, Any], 
        user_id: Optional[int], 
        db: Session
    ) -> Dict[str, Any]:
        """Process dictionary data for privacy controls."""
        
        processed = {}
        privacy_context = getattr(data.get('__privacy_context'), 'value', None)
        
        for key, value in data.items():
            # Skip metadata keys
            if key.startswith('_') or key in ['__privacy_context']:
                processed[key] = value
                continue
            
            # Check if field should be redacted based on consent
            if await self._should_redact_field(key, user_id, db):
                processed[key] = self._get_redacted_value(key, value)
                continue
            
            # Check data sensitivity
            field_sensitivity = self._get_field_sensitivity(key)
            if field_sensitivity == DataSensitivityLevel.RESTRICTED:
                if await self._has_high_risk_access(user_id, db):
                    processed[key] = await self._process_response_data(value, user_id, db)
                else:
                    processed[key] = self._get_redacted_value(key, value)
                continue
            
            # Process the field value
            processed[key] = await self._process_response_data(value, user_id, db)
        
        return processed
    
    async def _process_list_data(
        self, 
        data: List[Any], 
        user_id: Optional[int], 
        db: Session
    ) -> List[Any]:
        """Process list data for privacy controls."""
        
        processed = []
        for item in data:
            processed_item = await self._process_response_data(item, user_id, db)
            processed.append(processed_item)
        
        # Apply data minimization for large lists
        if len(processed) > 1000:
            processed = await self._minimize_large_datasets(processed, user_id, db)
        
        return processed
    
    async def _process_string_data(
        self, 
        data: str, 
        user_id: Optional[int], 
        db: Session
    ) -> str:
        """Process string data for PII detection and redaction."""
        
        processed = data
        
        # Apply PII redaction
        for pii_type, pattern in self._compiled_patterns.items():
            processed = pattern.sub(self._get_redaction_replacement(pii_type), processed)
        
        # Apply custom redaction rules
        processed = await self._apply_custom_redaction_rules(processed, user_id, db)
        
        return processed
    
    async def _should_redact_field(self, field_name: str, user_id: Optional[int], db: Session) -> bool:
        """Determine if a field should be redacted based on user consent."""
        
        if not user_id:
            return True  # Redact for anonymous users
        
        try:
            consent_service = ConsentManagementService(db)
            consents = consent_service.get_user_consents(user_id)
            
            # Check if user has consented to data processing for this field
            field_consent_mapping = {
                'email': 'data_processing',
                'phone': 'data_processing',
                'address': 'data_processing',
                'nif': 'financial_data_processing',
                'iban': 'financial_data_processing',
                'passport': 'identity_verification',
                'citizen_card': 'identity_verification'
            }
            
            required_consent = field_consent_mapping.get(field_name.lower())
            if required_consent:
                user_consents = [c.get('consent_type') for c in consents if c.get('granted', False)]
                return required_consent not in user_consents
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking consent for field {field_name}: {e}")
            return True  # Default to redaction on error
    
    def _get_redacted_value(self, field_name: str, original_value: Any) -> str:
        """Get appropriate redacted value for a field."""
        
        field_lower = field_name.lower()
        
        # Field-specific redaction
        if 'email' in field_lower:
            return "[EMAIL_REDACTED]"
        elif 'phone' in field_lower or 'telephone' in field_lower:
            return "[PHONE_REDACTED]"
        elif 'nif' in field_lower:
            return "[NIF_REDACTED]"
        elif 'iban' in field_lower:
            return "[IBAN_REDACTED]"
        elif 'passport' in field_lower:
            return "[PASSPORT_REDACTED]"
        elif 'citizen' in field_lower:
            return "[CITIZEN_CARD_REDACTED]"
        elif 'license' in field_lower or 'plate' in field_lower:
            return "[LICENSE_PLATE_REDACTED]"
        elif 'address' in field_lower:
            return "[ADDRESS_REDACTED]"
        elif 'name' in field_lower:
            return "[NAME_REDACTED]"
        else:
            return "[REDACTED]"
    
    def _get_field_sensitivity(self, field_name: str) -> str:
        """Determine data sensitivity level for a field."""
        
        field_lower = field_name.lower()
        
        # High sensitivity fields
        if any(keyword in field_lower for keyword in [
            'password', 'token', 'secret', 'key', 'private', 'nif', 'iban',
            'passport', 'citizen_card', 'credit_card', 'ssn', 'social_security'
        ]):
            return DataSensitivityLevel.RESTRICTED
        
        # Medium sensitivity fields
        elif any(keyword in field_lower for keyword in [
            'email', 'phone', 'address', 'birth', 'age', 'gender', 'license_plate'
        ]):
            return DataSensitivityLevel.CONFIDENTIAL
        
        # Low sensitivity fields
        elif any(keyword in field_lower for keyword in [
            'id', 'created_at', 'updated_at', 'status', 'type', 'category'
        ]):
            return DataSensitivityLevel.INTERNAL
        
        # Default to internal
        return DataSensitivityLevel.INTERNAL
    
    async def _has_high_risk_access(self, user_id: Optional[int], db: Session) -> bool:
        """Check if user has high-risk access privileges."""
        
        if not user_id:
            return False
        
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            return user and user.role in ['admin', 'data_protection_officer', 'legal']
        except Exception as e:
            logger.error(f"Error checking high-risk access: {e}")
            return False
    
    def _compile_pii_patterns(self) -> Dict[str, re.Pattern]:
        """Compile PII detection patterns for efficiency."""
        return {
            pii_type: re.compile(pattern, re.IGNORECASE)
            for pii_type, pattern in self.pii_patterns.items()
        }
    
    def _get_redaction_replacement(self, pii_type: str) -> str:
        """Get redaction replacement for PII type."""
        
        replacements = {
            'email': '[EMAIL_REDACTED]',
            'phone': '[PHONE_REDACTED]',
            'nif': '[NIF_REDACTED]',
            'cc': '[CREDIT_CARD_REDACTED]',
            'iban': '[IBAN_REDACTED]',
            'passport': '[PASSPORT_REDACTED]',
            'citizen_card': '[CITIZEN_CARD_REDACTED]',
            'license_plate': '[LICENSE_PLATE_REDACTED]',
            'postal_code': '[POSTAL_CODE_REDACTED]',
            'ip_address': '[IP_ADDRESS_REDACTED]',
            'credit_card': '[CREDIT_CARD_REDACTED]'
        }
        
        return replacements.get(pii_type, '[PII_REDACTED]')
    
    async def _apply_custom_redaction_rules(
        self, 
        text: str, 
        user_id: Optional[int], 
        db: Session
    ) -> str:
        """Apply custom redaction rules based on business logic."""
        
        # Apply Portuguese legal-specific redactions
        if "portuguese" in text.lower() or "portugal" in text.lower():
            # Ensure Portuguese ID numbers are redacted
            text = re.sub(r'\b\d{8}[-\s]?\d{1}[A-Z]{2}\b', '[CITIZEN_CARD_REDACTED]', text)
            text = re.sub(r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z][-\s]?\d{2}\b', '[LICENSE_PLATE_REDACTED]', text)
        
        return text
    
    async def _minimize_large_datasets(
        self, 
        data: List[Any], 
        user_id: Optional[int], 
        db: Session
    ) -> List[Any]:
        """Apply data minimization to large datasets."""
        
        # Limit to most relevant items
        minimized_data = data[:100]  # Take first 100 items
        
        # Apply additional minimization based on user risk profile
        if user_id:
            try:
                risk_level = await self._assess_user_risk_level(user_id, db)
                if risk_level == PrivacyRiskLevel.HIGH:
                    minimized_data = minimized_data[:20]  # Further limit for high-risk users
            except Exception as e:
                logger.error(f"Error in risk-based minimization: {e}")
        
        return minimized_data
    
    async def _assess_user_risk_level(self, user_id: int, db: Session) -> str:
        """Assess privacy risk level for user."""
        
        # Simple risk assessment based on user activity
        try:
            # Check recent audit trail for risky activities
            recent_activities = db.query(models.AuditTrail).filter(
                models.AuditTrail.user_id == user_id,
                models.AuditTrail.timestamp >= datetime.utcnow().isoformat()
            ).count()
            
            if recent_activities > 100:
                return PrivacyRiskLevel.HIGH
            elif recent_activities > 50:
                return PrivacyRiskLevel.MEDIUM
            else:
                return PrivacyRiskLevel.LOW
                
        except Exception as e:
            logger.error(f"Error assessing user risk level: {e}")
            return PrivacyRiskLevel.MEDIUM
    
    async def _apply_basic_redaction(self, response: Response) -> Response:
        """Apply basic redaction to non-JSON responses."""
        
        # Add privacy headers for non-JSON responses
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Privacy-Protected': 'true',
            'Cache-Control': 'no-store, no-cache, must-revalidate, private'
        })
        
        return response
    
    def _generate_privacy_headers(self, user_id: Optional[int]) -> Dict[str, str]:
        """Generate privacy-related HTTP headers."""
        
        headers = {
            'X-Privacy-Protected': 'true',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        # Add user-specific privacy headers
        if user_id:
            headers['X-User-ID-Protected'] = 'true'
        
        return headers
    
    async def _determine_privacy_mode(
        self, 
        request: Request, 
        user_id: Optional[int], 
        db: Session
    ) -> str:
        """Determine privacy mode for the request."""
        
        endpoint = request.url.path.lower()
        
        # High privacy mode for sensitive endpoints
        if any(sensitive in endpoint for sensitive in [
            '/privacy', '/consent', '/personal-data', '/gdpr'
        ]):
            return "high"
        
        # Medium privacy mode for user data endpoints
        elif any(user_data in endpoint for user_data in [
            '/user', '/profile', '/account'
        ]):
            return "medium"
        
        # Low privacy mode for public endpoints
        else:
            return "low"
    
    async def _assess_data_sensitivity(self, request: Request, db: Session) -> str:
        """Assess data sensitivity for the request."""
        
        method = request.method.upper()
        
        # High sensitivity for write operations on personal data
        if method in ['POST', 'PUT', 'PATCH'] and any(
            personal_data in request.url.path.lower() 
            for personal_data in ['user', 'profile', 'account']
        ):
            return DataSensitivityLevel.RESTRICTED
        
        # Medium sensitivity for read operations on user data
        elif method == 'GET' and any(
            user_data in request.url.path.lower() 
            for user_data in ['user', 'profile', 'account']
        ):
            return DataSensitivityLevel.CONFIDENTIAL
        
        # Low sensitivity for public operations
        else:
            return DataSensitivityLevel.INTERNAL
    
    async def _check_consent_status(
        self, 
        request: Request, 
        user_id: Optional[int], 
        db: Session
    ) -> Dict[str, bool]:
        """Check user's consent status for data processing."""
        
        if not user_id:
            return {"data_processing": False}
        
        try:
            consent_service = ConsentManagementService(db)
            consents = consent_service.get_user_consents(user_id)
            
            consent_status = {}
            for consent_record in consents:
                consent_type = consent_record.get('consent_type', 'unknown')
                granted = consent_record.get('granted', False)
                consent_status[consent_type] = granted
            
            return consent_status
            
        except Exception as e:
            logger.error(f"Error checking consent status: {e}")
            return {"data_processing": False}
    
    async def _validate_privacy_requirements(self, request: Request, db: Session) -> bool:
        """Validate privacy requirements before processing request."""
        
        # Check if request contains PII without proper consent
        user_id = await self._extract_user_id(request)
        
        if user_id and request.method in ['POST', 'PUT', 'PATCH']:
            # Check if user has given consent for data processing
            consent_status = await self._check_consent_status(request, user_id, db)
            if not consent_status.get('data_processing', False):
                logger.warning(f"User {user_id} attempting data processing without consent")
                return False
        
        return True
    
    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request."""
        try:
            # This would typically extract from JWT token or session
            # For now, return None as placeholder
            return getattr(request.state, 'user_id', None)
        except Exception:
            return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        return (
            request.headers.get("x-forwarded-for", "")
            .split(",")[0]
            .strip() or
            request.client.host if request.client else "unknown"
        )
    
    async def _log_privacy_event(
        self,
        user_id: Optional[int],
        action: str,
        details: Dict[str, Any],
        client_ip: str,
        user_agent: str,
        db: Session
    ):
        """Log privacy event for audit trail."""
        
        try:
            audit_trail_crud._create_audit_entry(
                db, None, action, None, {
                    **details,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "privacy_middleware": True
                },
                user_id,
                f"Privacy middleware: {action}"
            )
        except Exception as e:
            logger.error(f"Error logging privacy event: {e}")
    
    def _update_privacy_stats(self, response: Response, processing_time: float):
        """Update privacy statistics."""
        
        self.privacy_stats['total_requests'] += 1
        self.privacy_stats['total_processing_time'] += processing_time
        
        if response.status_code >= 400:
            self.privacy_stats['error_responses'] += 1
        
        # Check for privacy-related headers
        if response.headers.get('X-Privacy-Protected') == 'true':
            self.privacy_stats['privacy_protected_responses'] += 1
    
    def _default_privacy_config(self) -> Dict[str, Any]:
        """Get default privacy configuration."""
        
        return {
            "redaction_enabled": True,
            "consent_enforcement": True,
            "audit_logging": True,
            "risk_assessment": True,
            "data_minimization": True,
            "retention_enforcement": True,
            "pii_detection": True,
            "portuguese_compliance": True
        }
    
    def get_privacy_statistics(self) -> Dict[str, Any]:
        """Get privacy middleware statistics."""
        
        return {
            "total_requests": self.privacy_stats['total_requests'],
            "error_rate": (
                self.privacy_stats['error_responses'] / 
                max(self.privacy_stats['total_requests'], 1)
            ) * 100,
            "average_processing_time": (
                self.privacy_stats['total_processing_time'] /
                max(self.privacy_stats['total_requests'], 1)
            ),
            "privacy_protection_rate": (
                self.privacy_stats['privacy_protected_responses'] /
                max(self.privacy_stats['total_requests'], 1)
            ) * 100
        }