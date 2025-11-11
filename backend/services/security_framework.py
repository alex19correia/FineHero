"""
Enhanced Security Framework for FineHero

This module provides comprehensive security features including:
- Rate limiting and request throttling
- Input validation and sanitization  
- API key management
- GDPR compliance framework
- Security middleware
- Authentication and authorization
- Security audit logging
"""

import time
import secrets
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
import re
import bleach
from collections import defaultdict
import redis

Base = declarative_base()

# Security configuration
SECURITY_CONFIG = {
    "SECRET_KEY": "your-secret-key-here-change-in-production",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7,
    "PASSWORD_MIN_LENGTH": 8,
    "API_KEY_PREFIX": "finehero_",
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOGIN_LOCKOUT_TIME": 900,  # 15 minutes
    "RATE_LIMIT_REQUESTS": 100,
    "RATE_LIMIT_WINDOW": 3600,  # 1 hour
    "GDPR_DATA_RETENTION_DAYS": 2555,  # 7 years
    "ANONYMIZATION_DELAY_DAYS": 30
}

class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    severity: SecurityLevel = SecurityLevel.MEDIUM
    details: Optional[Dict[str, Any]] = None


class SecurityAuditLog(Base):
    """Database model for security audit logging."""
    __tablename__ = "security_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, index=True)
    user_id = Column(String, index=True, nullable=True)
    ip_address = Column(String, index=True)
    user_agent = Column(Text)
    endpoint = Column(String)
    severity = Column(String, index=True)
    details = Column(Text)  # JSON string
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)


class APIKey(Base):
    """Database model for API key management."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    key_hash = Column(String, unique=True, index=True)
    key_prefix = Column(String)
    name = Column(String)
    permissions = Column(Text)  # JSON string
    rate_limit = Column(Integer, default=1000)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)


class UserSession(Base):
    """Database model for user session management."""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    session_token = Column(String, unique=True, index=True)
    ip_address = Column(String, index=True)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
    is_active = Column(Boolean, default=True)


class GDPRDataRecord(Base):
    """Database model for GDPR compliance tracking."""
    __tablename__ = "gdpr_data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    data_type = Column(String, index=True)  # 'personal', 'behavioral', 'technical'
    retention_date = Column(DateTime, index=True)
    deletion_date = Column(DateTime, nullable=True)
    anonymized = Column(Boolean, default=False)
    consent_status = Column(String)  # 'granted', 'withdrawn', 'expired'
    consent_date = Column(DateTime)
    legal_basis = Column(String)  # 'consent', 'contract', 'legal_obligation', etc.
    processing_purposes = Column(Text)  # JSON string


class SecurityManager:
    """
    Comprehensive security management system
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        self._rate_limit_cache = defaultdict(list)
        
    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_api_key(self, user_id: str, name: str, permissions: List[str] = None) -> str:
        """Generate a new API key."""
        if permissions is None:
            permissions = ["read"]
        
        # Generate secure random key
        key = f"{SECURITY_CONFIG['API_KEY_PREFIX']}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Store in database
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key[:8],  # Store prefix for identification
            name=name,
            permissions=json.dumps(permissions),
            rate_limit=SECURITY_CONFIG["RATE_LIMIT_REQUESTS"],
            expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        return key
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate an API key and return associated record."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_record = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if api_key_record and api_key_record.expires_at > datetime.utcnow():
            # Update usage statistics
            api_key_record.last_used = datetime.utcnow()
            api_key_record.usage_count += 1
            self.db.commit()
            return api_key_record
        
        return None
    
    def check_rate_limit(self, identifier: str, limit: int = None, window: int = None) -> bool:
        """Check if request is within rate limits."""
        if limit is None:
            limit = SECURITY_CONFIG["RATE_LIMIT_REQUESTS"]
        if window is None:
            window = SECURITY_CONFIG["RATE_LIMIT_WINDOW"]
        
        current_time = time.time()
        window_start = current_time - window
        
        # Clean old entries
        self._rate_limit_cache[identifier] = [
            req_time for req_time in self._rate_limit_cache[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self._rate_limit_cache[identifier]) >= limit:
            return False
        
        # Add current request
        self._rate_limit_cache[identifier].append(current_time)
        return True
    
    def sanitize_input(self, input_text: str, allowed_tags: List[str] = None) -> str:
        """Sanitize user input to prevent XSS attacks."""
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u']
        
        # Clean HTML tags and attributes
        cleaned = bleach.clean(
            input_text,
            tags=allowed_tags,
            attributes={},
            protocols=['http', 'https', 'mailto'],
            strip=True
        )
        
        # Additional text sanitization
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        return cleaned.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength requirements."""
        errors = []
        score = 0
        
        # Length check
        if len(password) < SECURITY_CONFIG["PASSWORD_MIN_LENGTH"]:
            errors.append(f"Password must be at least {SECURITY_CONFIG['PASSWORD_MIN_LENGTH']} characters long")
        else:
            score += 1
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            errors.append("Password must contain lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            errors.append("Password must contain uppercase letters")
        
        if re.search(r'\d', password):
            score += 1
        else:
            errors.append("Password must contain numbers")
        
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
            score += 1
        else:
            errors.append("Password must contain special characters")
        
        # Calculate strength level
        if score < 2:
            strength = "weak"
        elif score < 4:
            strength = "medium"
        else:
            strength = "strong"
        
        return {
            "valid": len(errors) == 0,
            "strength": strength,
            "score": score,
            "errors": errors
        }
    
    def log_security_event(self, event: SecurityEvent):
        """Log security events for audit trail."""
        audit_log = SecurityAuditLog(
            event_type=event.event_type,
            user_id=event.user_id,
            ip_address=event.ip_address or "",
            user_agent=event.user_agent or "",
            endpoint=event.endpoint or "",
            severity=event.severity.value,
            details=json.dumps(event.details or {}),
            resolved=False
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def detect_suspicious_activity(self, user_id: str, ip_address: str, 
                                 endpoint: str) -> bool:
        """Detect potentially suspicious activity patterns."""
        current_time = datetime.utcnow()
        
        # Check for rapid successive requests
        recent_requests = self.db.query(SecurityAuditLog).filter(
            SecurityAuditLog.user_id == user_id,
            SecurityAuditLog.timestamp >= current_time - timedelta(minutes=5)
        ).count()
        
        if recent_requests > 50:  # More than 10 requests per minute
            self.log_security_event(SecurityEvent(
                event_type="suspicious_activity",
                user_id=user_id,
                ip_address=ip_address,
                endpoint=endpoint,
                severity=SecurityLevel.HIGH,
                details={"requests_in_5min": recent_requests}
            ))
            return True
        
        # Check for multiple IPs accessing same account
        ip_count = self.db.query(SecurityAuditLog).filter(
            SecurityAuditLog.user_id == user_id,
            SecurityAuditLog.timestamp >= current_time - timedelta(hours=1),
            SecurityAuditLog.ip_address != ip_address
        ).distinct(SecurityAuditLog.ip_address).count()
        
        if ip_count > 3:  # More than 3 different IPs in 1 hour
            self.log_security_event(SecurityEvent(
                event_type="multiple_ips",
                user_id=user_id,
                ip_address=ip_address,
                severity=SecurityLevel.MEDIUM,
                details={"different_ips": ip_count}
            ))
            return True
        
        return False
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SECURITY_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECURITY_CONFIG["SECRET_KEY"], algorithm=SECURITY_CONFIG["ALGORITHM"])
        return encoded_jwt
    
    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify JWT access token."""
        try:
            payload = jwt.decode(token, SECURITY_CONFIG["SECRET_KEY"], algorithms=[SECURITY_CONFIG["ALGORITHM"]])
            return payload
        except JWTError:
            return None
    
    def validate_file_upload(self, file_content: bytes, filename: str, 
                           allowed_extensions: List[str] = None) -> Dict[str, Any]:
        """Validate file uploads for security."""
        if allowed_extensions is None:
            allowed_extensions = ['.pdf', '.txt', '.doc', '.docx']
        
        # Check file extension
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            return {
                "valid": False,
                "error": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            }
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            return {
                "valid": False,
                "error": f"File too large. Maximum size: {max_size // (1024*1024)}MB"
            }
        
        # Check for malicious content patterns
        content_str = file_content.decode('utf-8', errors='ignore')
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                return {
                    "valid": False,
                    "error": "File contains potentially malicious content"
                }
        
        return {"valid": True}


class GDPRComplianceManager:
    """
    GDPR compliance management system
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def record_consent(self, user_id: str, data_type: str, consent_status: str,
                      legal_basis: str, processing_purposes: List[str]) -> bool:
        """Record user consent for data processing."""
        try:
            gdpr_record = GDPRDataRecord(
                user_id=user_id,
                data_type=data_type,
                retention_date=datetime.utcnow() + timedelta(days=SECURITY_CONFIG["GDPR_DATA_RETENTION_DAYS"]),
                consent_status=consent_status,
                consent_date=datetime.utcnow(),
                legal_basis=legal_basis,
                processing_purposes=json.dumps(processing_purposes)
            )
            
            self.db.add(gdpr_record)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False
    
    def withdraw_consent(self, user_id: str, data_type: str) -> bool:
        """Process consent withdrawal."""
        try:
            records = self.db.query(GDPRDataRecord).filter(
                GDPRDataRecord.user_id == user_id,
                GDPRDataRecord.data_type == data_type,
                GDPRDataRecord.consent_status == "granted"
            ).all()
            
            for record in records:
                record.consent_status = "withdrawn"
                # Schedule data deletion or anonymization
                record.deletion_date = datetime.utcnow() + timedelta(days=SECURITY_CONFIG["ANONYMIZATION_DELAY_DAYS"])
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False
    
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data for GDPR compliance."""
        try:
            # Update all user data records
            records = self.db.query(GDPRDataRecord).filter(
                GDPRDataRecord.user_id == user_id
            ).all()
            
            for record in records:
                record.anonymized = True
                record.user_id = f"anonymized_{record.id}"  # Replace with anonymized ID
            
            # Here you would also anonymize actual user data in other tables
            # This is a simplified implementation
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data for data portability."""
        try:
            # Get all user data records
            records = self.db.query(GDPRDataRecord).filter(
                GDPRDataRecord.user_id == user_id
            ).all()
            
            exported_data = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data_records": []
            }
            
            for record in records:
                exported_data["data_records"].append({
                    "data_type": record.data_type,
                    "retention_date": record.retention_date.isoformat(),
                    "consent_status": record.consent_status,
                    "consent_date": record.consent_date.isoformat(),
                    "legal_basis": record.legal_basis,
                    "processing_purposes": json.loads(record.processing_purposes),
                    "anonymized": record.anonymized
                })
            
            return exported_data
        except Exception as e:
            return {"error": f"Failed to export user data: {str(e)}"}
    
    def cleanup_expired_data(self) -> int:
        """Clean up data that has passed retention period."""
        try:
            expired_records = self.db.query(GDPRDataRecord).filter(
                GDPRDataRecord.retention_date < datetime.utcnow(),
                GDPRDataRecord.anonymized == False
            ).all()
            
            for record in expired_records:
                self.anonymize_user_data(record.user_id)
            
            return len(expired_records)
        except Exception as e:
            return 0


class SecurityMiddleware:
    """
    FastAPI security middleware
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.security_manager = SecurityManager(db_session)
        self.gdpr_manager = GDPRComplianceManager(db_session)
    
    async def __call__(self, request: Request, call_next):
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Rate limiting
        if not self.security_manager.check_rate_limit(client_ip):
            self.security_manager.log_security_event(SecurityEvent(
                event_type="rate_limit_exceeded",
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=str(request.url.path),
                severity=SecurityLevel.MEDIUM
            ))
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        
        # Log security events for suspicious activity
        if response.status_code >= 400:
            self.security_manager.log_security_event(SecurityEvent(
                event_type="error_response",
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=str(request.url.path),
                severity=SecurityLevel.LOW if response.status_code < 500 else SecurityLevel.MEDIUM,
                details={"status_code": response.status_code}
            ))
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"


# Pydantic models for request validation
class UserRegistration(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str
    name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    permissions: List[str] = ["read"]
    rate_limit: int = 1000
    expires_days: int = 365


class ConsentRequest(BaseModel):
    """Consent management model."""
    user_id: str
    data_type: str
    consent_status: str
    legal_basis: str
    processing_purposes: List[str]


# Security dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Get current authenticated user."""
    security_manager = SecurityManager(SessionLocal())
    payload = security_manager.verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_api_key(api_key: str = None, request: Request = None):
    """Dependency to validate API keys."""
    # Check for API key in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        api_key = auth_header.replace("Bearer ", "", 1)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    security_manager = SecurityManager(SessionLocal())
    key_record = security_manager.validate_api_key(api_key)
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return key_record


# Security-focused Pydantic validators
def validate_portuguese_phone(phone: str) -> bool:
    """Validate Portuguese phone number format."""
    pattern = r'^(\+351)?[0-9]{9}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None


def validate_nif(nif: str) -> bool:
    """Validate Portuguese NIF (tax number) format."""
    pattern = r'^[0-9]{9}$'
    if not re.match(pattern, nif):
        return False
    
    # Calculate validation checksum
    check_sum = sum(int(nif[i]) * (10 - i) for i in range(8))
    check_digit = check_sum % 11
    if check_digit < 10:
        return check_digit == int(nif[8])
    else:
        return 0 == int(nif[8])


def sanitize_html_content(content: str) -> str:
    """Sanitize HTML content for safe display."""
    return bleach.clean(
        content,
        tags=['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li'],
        attributes={},
        strip=True
    )


# Security configuration and setup
def setup_security_framework(app, db_session: Session):
    """Setup comprehensive security framework for the application."""
    
    # Initialize security components
    security_manager = SecurityManager(db_session)
    gdpr_manager = GDPRComplianceManager(db_session)
    security_middleware = SecurityMiddleware(db_session)
    
    # Add security middleware
    app.middleware("http")(security_middleware)
    
    # Add security endpoints
    @app.post("/api/v1/security/api-keys")
    async def create_api_key(key_data: APIKeyCreate, user=Depends(get_current_user)):
        """Create new API key for user."""
        api_key = security_manager.generate_api_key(
            user_id=user.get("sub"),
            name=key_data.name,
            permissions=key_data.permissions
        )
        return {
            "api_key": api_key,
            "message": "API key created successfully. Store this key securely as it won't be shown again."
        }
    
    @app.get("/api/v1/security/audit-logs")
    async def get_audit_logs(user=Depends(get_current_user)):
        """Get security audit logs (admin only)."""
        # Add role-based access control here
        logs = db_session.query(SecurityAuditLog).order_by(
            SecurityAuditLog.timestamp.desc()
        ).limit(100).all()
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "severity": log.severity,
                "endpoint": log.endpoint,
                "resolved": log.resolved
            }
            for log in logs
        ]
    
    @app.post("/api/v1/gdpr/consent")
    async def record_consent(consent_data: ConsentRequest):
        """Record user consent for GDPR compliance."""
        success = gdpr_manager.record_consent(
            user_id=consent_data.user_id,
            data_type=consent_data.data_type,
            consent_status=consent_data.consent_status,
            legal_basis=consent_data.legal_basis,
            processing_purposes=consent_data.processing_purposes
        )
        
        if success:
            return {"message": "Consent recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record consent")
    
    @app.get("/api/v1/gdpr/export/{user_id}")
    async def export_user_data(user_id: str):
        """Export user data for GDPR portability."""
        exported_data = gdpr_manager.export_user_data(user_id)
        
        if "error" in exported_data:
            raise HTTPException(status_code=404, detail=exported_data["error"])
        
        return exported_data
    
    @app.delete("/api/v1/gdpr/delete/{user_id}")
    async def delete_user_data(user_id: str):
        """Delete/anonymize user data for GDPR compliance."""
        success = gdpr_manager.anonymize_user_data(user_id)
        
        if success:
            return {"message": "User data anonymized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user data")
    
    return {
        "security_manager": security_manager,
        "gdpr_manager": gdpr_manager,
        "middleware": security_middleware
    }