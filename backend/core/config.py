from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import Dict, Any

load_dotenv()

class Settings(BaseSettings):
    """
    Application settings including GDPR compliance and audit trail configuration.
    """
    APP_NAME: str = "FineHero AI"
    DATABASE_URL: str = "sqlite:///./finehero.db"
    
    # External API Keys
    GOOGLE_AI_API_KEY: str = ""
    
    # JWT Configuration
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Other settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # GDPR Compliance Configuration
    GDPR_COMPLIANCE_ENABLED: bool = True
    DATA_RETENTION_AUTOMATION: bool = True
    AUTO_CLEANUP_ENABLED: bool = True
    
    # Data Retention Policies (in days)
    RETENTION_FINANCIAL_DATA_DAYS: int = 2555  # 7 years for financial data
    RETENTION_USER_DATA_DAYS: int = 730        # 2 years for user data
    RETENTION_AUDIT_DATA_DAYS: int = 2555      # 7 years for audit data
    RETENTION_SYSTEM_DATA_DAYS: int = 365      # 1 year for system data
    RETENTION_LEGAL_DATA_DAYS: int = 2555      # 7 years for legal data
    
    # Audit Trail Configuration
    AUDIT_TRAIL_ENABLED: bool = True
    AUDIT_LEVEL: str = "COMPREHENSIVE"  # Options: MINIMAL, STANDARD, COMPREHENSIVE
    AUDIT_CLEANUP_ENABLED: bool = True
    AUDIT_IP_TRACKING: bool = True
    AUDIT_USER_AGENT_TRACKING: bool = True
    
    # Data Retention Automation Schedule
    RETENTION_CLEANUP_CRON_HOUR: int = 2      # Run cleanup at 2 AM
    RETENTION_CLEANUP_CRON_MINUTE: int = 0    # Run cleanup at minute 0
    RETENTION_CLEANUP_CRON_DAY_OF_WEEK: str = "SUN"  # Run on Sundays
    
    # GDPR Compliance Settings
    GDPR_CONSENT_REQUIRED: bool = True
    GDPR_DATA_EXPORT_ENABLED: bool = True
    GDPR_RIGHT_TO_ERASURE_ENABLED: bool = True
    GDPR_DATA_ANONYMIZATION_ENABLED: bool = True
    GDPR_COMPLIANCE_NOTIFICATIONS: bool = True
    
    # Data Anonymization Settings
    ANONYMIZATION_REPLACE_EMAIL_DOMAIN: str = "finehero.invalid"
    ANONYMIZATION_REPLACE_USERNAME_PATTERN: str = "anonymized_user_{id}"
    ANONYMIZATION_REPLACE_NAME: str = "Anonymized User"
    
    # Security and Privacy Settings
    ENCRYPT_SENSITIVE_DATA: bool = True
    LOG_DATA_ACCESS: bool = True
    REQUIRE_USER_CONSENT_FOR_PROCESSING: bool = True
    DATA_MINIMIZATION_ENABLED: bool = True
    
    # Compliance Reporting
    COMPLIANCE_REPORTING_ENABLED: bool = True
    COMPLIANCE_REPORT_FREQUENCY: str = "MONTHLY"  # Options: DAILY, WEEKLY, MONTHLY, QUARTERLY
    AUDIT_TRAIL_EXPORT_ENABLED: bool = True
    
    # API Security for GDPR Endpoints
    GDPR_ENDPOINT_RATE_LIMIT: int = 10  # Requests per hour per user
    GDPR_ENDPOINT_AUTHENTICATION_REQUIRED: bool = True
    GDPR_EXPORT_FORMAT: str = "JSON"    # Options: JSON, CSV, XML
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_retention_policy(self, data_type: str, table_name: str = None) -> Dict[str, Any]:
        """
        Get retention policy for specific data type and table.
        
        Args:
            data_type: Type of data (financial, user_data, audit_data, system_data, legal)
            table_name: Specific table name (optional)
            
        Returns:
            Dictionary with retention policy configuration
        """
        base_policies = {
            "financial": {
                "retention_days": self.RETENTION_FINANCIAL_DATA_DAYS,
                "description": "Financial data (7 years for compliance)",
                "tables": ["payments", "stripe_subscriptions", "stripe_customers", "payment_methods"]
            },
            "user_data": {
                "retention_days": self.RETENTION_USER_DATA_DAYS,
                "description": "User personal data (2 years after account closure)",
                "tables": ["users", "fines", "defenses"]
            },
            "audit_data": {
                "retention_days": self.RETENTION_AUDIT_DATA_DAYS,
                "description": "Audit trail data (7 years for compliance)",
                "tables": ["audit_trails", "fines", "defenses", "legal_documents", "case_outcomes"]
            },
            "system_data": {
                "retention_days": self.RETENTION_SYSTEM_DATA_DAYS,
                "description": "System operational data (1 year)",
                "tables": ["webhook_events", "defense_templates"]
            },
            "legal": {
                "retention_days": self.RETENTION_LEGAL_DATA_DAYS,
                "description": "Legal reference data (7 years)",
                "tables": ["legal_documents", "case_outcomes"]
            }
        }
        
        policy = base_policies.get(data_type, {
            "retention_days": 730,
            "description": "Default retention policy",
            "tables": []
        })
        
        # Add table-specific overrides if needed
        if table_name and table_name in policy["tables"]:
            policy["table_specific"] = True
            policy["current_table"] = table_name
        
        return policy
    
    def get_audit_configuration(self) -> Dict[str, Any]:
        """
        Get audit trail configuration.
        
        Returns:
            Dictionary with audit configuration
        """
        return {
            "enabled": self.AUDIT_TRAIL_ENABLED,
            "level": self.AUDIT_LEVEL,
            "cleanup_enabled": self.AUDIT_CLEANUP_ENABLED,
            "track_ip": self.AUDIT_IP_TRACKING,
            "track_user_agent": self.AUDIT_USER_AGENT_TRACKING,
            "cleanup_retention_days": self.RETENTION_AUDIT_DATA_DAYS
        }
    
    def get_gdpr_configuration(self) -> Dict[str, Any]:
        """
        Get GDPR compliance configuration.
        
        Returns:
            Dictionary with GDPR configuration
        """
        return {
            "compliance_enabled": self.GDPR_COMPLIANCE_ENABLED,
            "consent_required": self.GDPR_CONSENT_REQUIRED,
            "data_export_enabled": self.GDPR_DATA_EXPORT_ENABLED,
            "right_to_erasure_enabled": self.GDPR_RIGHT_TO_ERASURE_ENABLED,
            "data_anonymization_enabled": self.GDPR_DATA_ANONYMIZATION_ENABLED,
            "compliance_notifications": self.GDPR_COMPLIANCE_NOTIFICATIONS,
            "retention_automation_enabled": self.DATA_RETENTION_AUTOMATION,
            "endpoint_rate_limit": self.GDPR_ENDPOINT_RATE_LIMIT,
            "endpoint_auth_required": self.GDPR_ENDPOINT_AUTHENTICATION_REQUIRED,
            "export_format": self.GDPR_EXPORT_FORMAT
        }
    
    def get_anonymization_configuration(self) -> Dict[str, Any]:
        """
        Get data anonymization configuration.
        
        Returns:
            Dictionary with anonymization configuration
        """
        return {
            "replace_email_domain": self.ANONYMIZATION_REPLACE_EMAIL_DOMAIN,
            "username_pattern": self.ANONYMIZATION_REPLACE_USERNAME_PATTERN,
            "name_replacement": self.ANONYMIZATION_REPLACE_NAME,
            "encryption_enabled": self.ENCRYPT_SENSITIVE_DATA
        }
    
    def is_compliance_mode_enabled(self) -> bool:
        """
        Check if compliance mode is fully enabled.
        
        Returns:
            True if GDPR compliance is enabled and configured
        """
        return (
            self.GDPR_COMPLIANCE_ENABLED and
            self.AUDIT_TRAIL_ENABLED and
            self.DATA_RETENTION_AUTOMATION
        )
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of compliance configuration.
        
        Returns:
            Dictionary with compliance configuration summary
        """
        return {
            "gdpr_compliance": self.get_gdpr_configuration(),
            "audit_configuration": self.get_audit_configuration(),
            "retention_policies": {
                "financial_data_days": self.RETENTION_FINANCIAL_DATA_DAYS,
                "user_data_days": self.RETENTION_USER_DATA_DAYS,
                "audit_data_days": self.RETENTION_AUDIT_DATA_DAYS,
                "system_data_days": self.RETENTION_SYSTEM_DATA_DAYS,
                "legal_data_days": self.RETENTION_LEGAL_DATA_DAYS
            },
            "anonymization": self.get_anonymization_configuration(),
            "automation": {
                "retention_cleanup_enabled": self.AUTO_CLEANUP_ENABLED,
                "cleanup_schedule": f"{self.RETENTION_CLEANUP_CRON_MINUTE} {self.RETENTION_CLEANUP_CRON_HOUR} * * {self.RETENTION_CLEANUP_CRON_DAY_OF_WEEK}",
                "compliance_reporting": self.COMPLIANCE_REPORTING_ENABLED,
                "report_frequency": self.COMPLIANCE_REPORT_FREQUENCY
            },
            "compliance_mode_enabled": self.is_compliance_mode_enabled()
        }

settings = Settings()

# Validate configuration
def validate_compliance_config():
    """
    Validate compliance configuration and provide warnings for potential issues.
    """
    warnings = []
    
    # Check GDPR compliance settings
    if not settings.GDPR_COMPLIANCE_ENABLED:
        warnings.append("GDPR compliance is disabled. Ensure this is intentional.")
    
    if not settings.AUDIT_TRAIL_ENABLED:
        warnings.append("Audit trail is disabled. Compliance may be compromised.")
    
    # Check retention periods
    if settings.RETENTION_USER_DATA_DAYS < 365:
        warnings.append("User data retention period is less than 1 year. Verify GDPR compliance.")
    
    if settings.RETENTION_AUDIT_DATA_DAYS < 2555:
        warnings.append("Audit data retention period is less than 7 years. May not meet compliance requirements.")
    
    # Check automation settings
    if settings.DATA_RETENTION_AUTOMATION and not settings.AUTO_CLEANUP_ENABLED:
        warnings.append("Data retention automation is enabled but cleanup is disabled.")
    
    # Security warnings
    if not settings.ENCRYPT_SENSITIVE_DATA and settings.DEBUG:
        warnings.append("Sensitive data encryption is disabled in debug mode.")
    
    return warnings

# Run configuration validation on startup
config_warnings = validate_compliance_config()
if config_warnings:
    print("⚠️  Configuration Warnings:")
    for warning in config_warnings:
        print(f"   - {warning}")

# Validate SECRET_KEY is set and not empty
if not settings.SECRET_KEY:
    if not settings.DEBUG:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set in production. "
            "Set SECRET_KEY in your .env file or environment."
        )
    else:
        # For development, generate a random secret if not set
        import secrets
        settings.SECRET_KEY = secrets.token_urlsafe(32)

# Export settings for easy access
__all__ = ["settings", "validate_compliance_config"]
