# FineHero Database Audit Trail and Soft Delete Implementation Guide

## Overview

This documentation provides comprehensive guidance for the **FineHero Database Audit Trail and Soft Delete System**, a GDPR-compliant data management solution that ensures complete auditability, data recovery capabilities, and privacy protection.

## Table of Contents

1. [System Overview](#system-overview)
2. [Features and Capabilities](#features-and-capabilities)
3. [Migration Guide](#migration-guide)
4. [Usage Guide](#usage-guide)
5. [API Documentation](#api-documentation)
6. [Configuration](#configuration)
7. [Best Practices](#best-practices)
8. [GDPR Compliance](#gdpr-compliance)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## System Overview

### What is the Soft Delete and Audit Trail System?

The FineHero system now implements a comprehensive **soft delete and audit trail system** that provides:

- **Soft Delete Capabilities**: Safe data recovery with `deleted_at` and `is_deleted` fields
- **Complete Audit Trail**: Full change tracking with user attribution and timestamps
- **GDPR Compliance**: Automated data retention policies and user data rights
- **Data Recovery**: Restore deleted records without data loss
- **Legal Compliance**: Meets Portuguese and EU data protection requirements

### Key Components

1. **SoftDeleteMixin**: Base class providing soft delete functionality
2. **AuditMixin**: Base class providing audit trail logging
3. **AuditTrail Model**: Dedicated table for comprehensive change tracking
4. **CRUD Operations**: Enhanced database operations with audit logging
5. **GDPR Service**: Compliance automation and data protection
6. **API Endpoints**: RESTful endpoints for all operations
7. **Configuration**: Flexible retention policies and audit settings

---

## Features and Capabilities

### 🗃️ Soft Delete Features

- **Safe Deletion**: Records marked as deleted, not permanently removed
- **Restore Capability**: Recover soft-deleted records with full data integrity
- **Automatic Filtering**: Active queries exclude soft-deleted records by default
- **Admin Access**: Special endpoints for viewing deleted records
- **Bulk Operations**: Efficient soft delete of multiple records

### 📊 Audit Trail Features

- **Complete Change Tracking**: All CREATE, UPDATE, DELETE operations logged
- **User Attribution**: Track who made changes with user IDs and metadata
- **Timestamp Accuracy**: Precise timing for all operations
- **Data Preservation**: Before/after values stored for accountability
- **Compliance Logging**: IP addresses, user agents, and request context

### 🔒 GDPR Compliance Features

- **Data Portability**: Export complete user data in portable formats
- **Right to Erasure**: Automated soft deletion upon user request
- **Data Anonymization**: Privacy-preserving data handling
- **Retention Automation**: Automatic deletion based on legal requirements
- **Consent Management**: Track and manage user consent preferences
- **Compliance Reporting**: Generate audit reports for regulators

### ⚙️ Configuration Features

- **Flexible Retention Policies**: Configure data retention periods per data type
- **Audit Level Control**: Minimal, Standard, or Comprehensive audit logging
- **Automation Scheduling**: Automated cleanup based on configurable schedules
- **Security Settings**: Encryption and data minimization options
- **Rate Limiting**: Protect GDPR endpoints from abuse

---

## Migration Guide

### Prerequisites

Before running the migration, ensure you have:

1. **Database Backup**: Full backup of your current database
2. **Application Downtime**: Plan for brief downtime during migration
3. **Environment Configuration**: Updated configuration files
4. **Testing Environment**: Test migration in staging first

### Running the Migration

```bash
# Navigate to the backend directory
cd backend

# Run the migration script
python infrastructure/migrations/add_soft_deletes_audit_trails.py

# Or dry run to see what would be changed
python infrastructure/migrations/add_soft_deletes_audit_trails.py dry-run

# To rollback if needed (WARNING: destructive operation)
python infrastructure/migrations/add_soft_deletes_audit_trails.py rollback
```

### Migration Process

1. **Audit Trails Table**: Creates new `audit_trails` table
2. **Soft Delete Fields**: Adds `deleted_at` and `is_deleted` columns
3. **Audit Fields**: Adds `created_at`, `updated_at`, `created_by`, `updated_by`, `audit_metadata` columns
4. **Data Migration**: Sets default values for existing records
5. **Index Creation**: Creates performance indexes
6. **Validation**: Verifies migration success

### Post-Migration Steps

1. **Verify Data Integrity**: Check that existing data is preserved
2. **Test Operations**: Verify CRUD operations work correctly
3. **Update Application Code**: Ensure code uses new CRUD methods
4. **Configure Retention Policies**: Set appropriate retention periods
5. **Monitor Logs**: Watch for any migration-related errors

---

## Usage Guide

### Basic Soft Delete Operations

```python
from backend.app.crud_soft_delete import fine_crud
from sqlalchemy.orm import Session

# Soft delete a record
def delete_fine(db: Session, fine_id: int, user_id: int):
    return fine_crud.soft_delete(
        db=db, 
        id=fine_id, 
        user_id=user_id, 
        reason="User requested deletion"
    )

# Restore a soft-deleted record
def restore_fine(db: Session, fine_id: int, user_id: int):
    return fine_crud.restore(db=db, id=fine_id, user_id=user_id)

# Permanent delete (cannot be undone)
def permanent_delete_fine(db: Session, fine_id: int, user_id: int):
    return fine_crud.permanent_delete(
        db=db, 
        id=fine_id, 
        user_id=user_id, 
        reason="Legal requirement for permanent deletion"
    )
```

### Audit Trail Operations

```python
from backend.app.crud_soft_delete import audit_trail_crud

# Get audit trail for a specific record
def get_fine_audit_trail(db: Session, fine_id: int):
    return audit_trail_crud.get_by_table_and_record(
        db=db,
        table_name="fines",
        record_id=fine_id,
        limit=50
    )

# Get audit trail for a user
def get_user_audit_trail(db: Session, user_id: int):
    return audit_trail_crud.get_by_user(db=db, user_id=user_id)

# Clean up old audit data
def cleanup_audit_data(db: Session):
    return audit_trail_crud.cleanup_old_audit_data(
        db=db, 
        retention_days=2555  # 7 years
    )
```

### Enhanced CRUD Operations

```python
# Create with audit logging
def create_fine_with_audit(db: Session, fine_data: dict, user_id: int):
    return fine_crud.create_with_audit(
        db=db,
        fine=fine_data,
        user_id=user_id
    )

# Update with audit logging
def update_fine_with_audit(db: Session, fine_id: int, update_data: dict, user_id: int):
    return fine_crud.update_with_audit(
        db=db,
        id=fine_id,
        fine_update=update_data,
        user_id=user_id
    )

# Get active records only
def get_active_fines(db: Session, skip: int = 0, limit: int = 100):
    return fine_crud.get_active_records(db=db, skip=skip, limit=limit)
```

### GDPR Compliance Operations

```python
from backend.services.gdpr_compliance_service import create_gdpr_service

# Handle data subject request
def handle_gdpr_request(db: Session, user_id: int, request_type: str):
    gdpr_service = create_gdpr_service(db)
    
    if request_type == "export":
        # Data portability request
        return gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="export"
        )
    elif request_type == "delete":
        # Right to erasure request
        return gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="delete",
            reason="User requested deletion",
            confirm_deletion=True
        )
    elif request_type == "anonymize":
        # Data anonymization request
        return gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="anonymize",
            reason="User requested anonymization"
        )

# Run automated data retention cleanup
def run_retention_cleanup(db: Session, dry_run: bool = False):
    from backend.services.gdpr_compliance_service import run_scheduled_retention_cleanup
    return run_scheduled_retention_cleanup(db=db, dry_run=dry_run)
```

---

## API Documentation

### Fine Management Endpoints

#### Create Fine
```http
POST /api/v1/fines/
Content-Type: application/json
X-User-ID: 123

{
  "date": "2024-01-15",
  "location": "Lisbon, Portugal",
  "infractor": "John Doe",
  "fine_amount": 100.0,
  "infraction_code": "ART-048"
}
```

#### Get Fines
```http
GET /api/v1/fines/?skip=0&limit=100&active_only=true&include_deleted=false
```

#### Get Fine by ID
```http
GET /api/v1/fines/{fine_id}?include_deleted=false
```

#### Update Fine
```http
PUT /api/v1/fines/{fine_id}
Content-Type: application/json
X-User-ID: 123

{
  "location": "Updated Location",
  "fine_amount": 120.0
}
```

#### Soft Delete Fine
```http
DELETE /api/v1/fines/{fine_id}?reason=User%20requested%20deletion
```

#### Restore Fine
```http
POST /api/v1/fines/{fine_id}/restore
X-User-ID: 123
```

#### Permanent Delete Fine
```http
POST /api/v1/fines/{fine_id}/permanent-delete?reason=Legal%20requirement&confirm=true
```

#### Get Audit Trail
```http
GET /api/v1/fines/{fine_id}/audit-trail?limit=50
```

#### Get User Fines
```http
GET /api/v1/fines/user/{user_id}?skip=0&limit=100&active_only=true
```

#### Get Statistics
```http
GET /api/v1/fines/statistics?include_deleted=false
```

### GDPR Compliance Endpoints

#### Export User Data
```http
POST /api/v1/fines/gdpr/export/{user_id}?format=json
X-User-ID: 123
```

#### Initiate Data Deletion
```http
POST /api/v1/fines/gdpr/delete/{user_id}?reason=User%20requested%20deletion&confirm=true
X-User-ID: 123
```

### Response Formats

#### Success Response
```json
{
  "id": 123,
  "date": "2024-01-15",
  "location": "Lisbon, Portugal",
  "infractor": "John Doe",
  "fine_amount": 100.0,
  "infraction_code": "ART-048",
  "is_deleted": false,
  "deleted_at": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "created_by": 123,
  "updated_by": 123,
  "audit_metadata": {"created_from": "api"}
}
```

#### Error Response
```json
{
  "detail": "Error message describing the issue"
}
```

#### GDPR Export Response
```json
{
  "status": "success",
  "message": "User fines data exported successfully",
  "export_data": {
    "export_timestamp": "2024-01-15T10:00:00Z",
    "user_id": 123,
    "data": {
      "user_profile": { ... },
      "fines": [ ... ],
      "audit_trail": [ ... ]
    }
  }
}
```

---

## Configuration

### Environment Variables

Create or update your `.env` file with the following GDPR and audit settings:

```bash
# GDPR Compliance Configuration
GDPR_COMPLIANCE_ENABLED=true
DATA_RETENTION_AUTOMATION=true
AUTO_CLEANUP_ENABLED=true

# Data Retention Policies (in days)
RETENTION_FINANCIAL_DATA_DAYS=2555  # 7 years
RETENTION_USER_DATA_DAYS=730        # 2 years
RETENTION_AUDIT_DATA_DAYS=2555      # 7 years
RETENTION_SYSTEM_DATA_DAYS=365      # 1 year
RETENTION_LEGAL_DATA_DAYS=2555      # 7 years

# Audit Trail Configuration
AUDIT_TRAIL_ENABLED=true
AUDIT_LEVEL=COMPREHENSIVE
AUDIT_CLEANUP_ENABLED=true
AUDIT_IP_TRACKING=true
AUDIT_USER_AGENT_TRACKING=true

# GDPR Compliance Settings
GDPR_CONSENT_REQUIRED=true
GDPR_DATA_EXPORT_ENABLED=true
GDPR_RIGHT_TO_ERASURE_ENABLED=true
GDPR_DATA_ANONYMIZATION_ENABLED=true
GDPR_COMPLIANCE_NOTIFICATIONS=true

# Automation Schedule
RETENTION_CLEANUP_CRON_HOUR=2
RETENTION_CLEANUP_CRON_MINUTE=0
RETENTION_CLEANUP_CRON_DAY_OF_WEEK=SUN

# Security Settings
ENCRYPT_SENSITIVE_DATA=true
LOG_DATA_ACCESS=true
REQUIRE_USER_CONSENT_FOR_PROCESSING=true
DATA_MINIMIZATION_ENABLED=true

# API Security
GDPR_ENDPOINT_RATE_LIMIT=10
GDPR_ENDPOINT_AUTHENTICATION_REQUIRED=true
GDPR_EXPORT_FORMAT=JSON
```

### Runtime Configuration

You can also configure settings programmatically:

```python
from backend.core.config import settings

# Get retention policy for specific data type
policy = settings.get_retention_policy("user_data", "fines")
print(f"Retention period: {policy['retention_days']} days")

# Get audit configuration
audit_config = settings.get_audit_configuration()
print(f"Audit level: {audit_config['level']}")

# Get GDPR configuration
gdpr_config = settings.get_gdpr_configuration()
print(f"Compliance enabled: {gdpr_config['compliance_enabled']}")

# Check if compliance mode is fully enabled
if settings.is_compliance_mode_enabled():
    print("GDPR compliance is fully configured and enabled")

# Get compliance summary
summary = settings.get_compliance_summary()
print(json.dumps(summary, indent=2))
```

---

## Best Practices

### 🛡️ Security Best Practices

1. **Enable Encryption**: Always enable `ENCRYPT_SENSITIVE_DATA` in production
2. **Secure API Keys**: Never commit API keys or secrets to version control
3. **Rate Limiting**: Implement rate limiting for GDPR endpoints
4. **Access Control**: Restrict access to soft-deleted data to authorized personnel only
5. **Audit Logging**: Enable comprehensive audit logging for all data operations

### 📊 Audit Trail Best Practices

1. **Comprehensive Logging**: Enable `AUDIT_LEVEL=COMPREHENSIVE` for full compliance
2. **Regular Cleanup**: Schedule regular audit data cleanup based on retention policies
3. **Monitor Access**: Monitor audit trail access and unusual patterns
4. **Backup Audit Data**: Regularly backup audit trail data separately
5. **Test Recovery**: Regularly test audit trail data recovery procedures

### 🔒 GDPR Compliance Best Practices

1. **Data Minimization**: Only collect and store data that is necessary
2. **Consent Management**: Implement proper consent collection and management
3. **Data Portability**: Regularly test data export functionality
4. **Right to Erasure**: Process deletion requests promptly and completely
5. **Retention Automation**: Enable automated data retention cleanup
6. **Legal Review**: Have legal counsel review retention periods and policies

### 🗃️ Soft Delete Best Practices

1. **Always Use Soft Delete**: Never perform permanent deletes unless legally required
2. **Document Reasons**: Always provide clear reasons for soft deletions
3. **Regular Reviews**: Regularly review soft-deleted data for permanent deletion opportunities
4. **User Communication**: Inform users when their data is soft deleted
5. **Testing**: Regularly test soft delete and restore functionality

### ⚙️ Configuration Best Practices

1. **Environment-Specific Settings**: Use different settings for development, staging, and production
2. **Backup Configuration**: Backup configuration files regularly
3. **Version Control**: Keep configuration files in version control (without secrets)
4. **Validation**: Validate configuration changes before deploying
5. **Monitoring**: Monitor configuration changes and their effects

### 📈 Performance Best Practices

1. **Index Usage**: Ensure proper indexing for soft delete queries
2. **Batch Operations**: Use bulk operations for large-scale data changes
3. **Pagination**: Always use pagination for large result sets
4. **Query Optimization**: Optimize queries to minimize database load
5. **Connection Pooling**: Use database connection pooling in production

---

## GDPR Compliance

### Legal Requirements Met

This implementation meets the following GDPR requirements:

- **Article 17 (Right to Erasure)**: Automated soft deletion with configurable retention
- **Article 20 (Data Portability)**: Complete data export in portable formats
- **Article 30 (Records of Processing)**: Comprehensive audit trail
- **Article 32 (Security of Processing)**: Data encryption and access controls
- **Article 33 (Breach Notification)**: Audit trail for incident investigation

### Portuguese Data Protection

The system also supports Portuguese data protection requirements:

- **Lei 58/2019**: Portuguese implementation of GDPR
- **Commercial Law**: 7-year retention for financial data
- **Tax Law**: Proper retention for tax-related information
- **Legal Documentation**: Indefinite retention for legal reference materials

### Compliance Workflows

#### Data Subject Access Request (DSAR)
1. **User Request**: User requests their data export or deletion
2. **Authentication**: Verify user's identity and authorization
3. **Data Collection**: Gather all user data across all systems
4. **Data Processing**: Export or delete data according to request
5. **Audit Logging**: Log all actions taken for compliance
6. **Response**: Provide data or confirmation to user

#### Data Retention Automation
1. **Policy Definition**: Configure retention periods for different data types
2. **Automated Scanning**: Regular scanning for expired data
3. **Soft Deletion**: Mark expired data as deleted
4. **Retention Period**: Hold soft-deleted data for legal requirements
5. **Permanent Deletion**: Finally delete data after retention period
6. **Audit Logging**: Log all deletion actions

#### Consent Management
1. **Consent Collection**: Collect explicit consent for data processing
2. **Consent Storage**: Store consent records with timestamps and context
3. **Consent Updates**: Allow users to update consent preferences
4. **Consent Enforcement**: Enforce consent requirements in data processing
5. **Consent Audit**: Log all consent-related activities

---

## Troubleshooting

### Common Issues

#### Migration Issues

**Problem**: Migration script fails with database errors
```bash
Error: no such column: deleted_at
```
**Solution**: 
1. Ensure database schema is up to date
2. Check database permissions
3. Run migration with proper database URL

**Problem**: Data migration takes too long
```bash
Migration is running slowly...
```
**Solution**:
1. Run migration during off-peak hours
2. Consider chunked migration for large datasets
3. Optimize database indexes before migration

#### Soft Delete Issues

**Problem**: Soft-deleted records still appearing in queries
```python
# Records still showing in get_active_records()
```
**Solution**:
1. Verify soft delete fields are properly indexed
2. Check query filters for `is_deleted = False`
3. Clear ORM session cache and reload

**Problem**: Restore operation fails
```python
# Restore returns None or fails
```
**Solution**:
1. Verify record exists and is soft-deleted
2. Check foreign key constraints
3. Ensure user has proper permissions

#### Audit Trail Issues

**Problem**: Audit entries not being created
```python
# No audit trail entries for operations
```
**Solution**:
1. Check audit trail configuration
2. Verify CRUD operations use audit-enabled methods
3. Check database permissions for audit table

**Problem**: Large audit table impacting performance
```sql
-- Slow queries on audit_trails table
```
**Solution**:
1. Enable audit cleanup automation
2. Add proper indexes to audit table
3. Consider partitioning audit table by date

#### GDPR Compliance Issues

**Problem**: Data export fails or is incomplete
```python
# Export request returns partial data or errors
```
**Solution**:
1. Check user data relationships
2. Verify GDPR service configuration
3. Review error logs for specific failures

**Problem**: Data retention cleanup not working
```python
# Old data not being automatically deleted
```
**Solution**:
1. Verify retention automation is enabled
2. Check cleanup schedule configuration
3. Run cleanup manually to test functionality

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Configuration Validation

Validate your configuration:

```python
from backend.core.config import settings, validate_compliance_config

# Get configuration warnings
warnings = validate_compliance_config()
for warning in warnings:
    print(f"⚠️ {warning}")

# Check compliance status
summary = settings.get_compliance_summary()
print(f"Compliance Mode: {summary['compliance_mode_enabled']}")
```

---

## Examples

### Complete User Workflow Example

```python
from backend.app.crud_soft_delete import fine_crud, defense_crud, user_crud, audit_trail_crud
from backend.services.gdpr_compliance_service import create_gdpr_service

def complete_user_workflow(db: Session, user_data: dict, fine_data: dict, defense_data: dict):
    # 1. Create user with audit logging
    user = user_crud.create_with_audit(db=db, user=UserCreate(**user_data))
    user_id = user.id
    
    # 2. Create fine with audit logging
    fine = fine_crud.create_with_audit(
        db=db, 
        fine=FineCreate(**fine_data), 
        user_id=user_id
    )
    
    # 3. Create defense with audit logging
    defense = defense_crud.create_with_audit(
        db=db,
        defense=DefenseCreate(**defense_data),
        fine_id=fine.id,
        user_id=user_id
    )
    
    # 4. Update fine with audit logging
    updated_fine = fine_crud.update_with_audit(
        db=db,
        id=fine.id,
        fine_update=FineUpdate(fine_amount=120.0),
        user_id=user_id
    )
    
    # 5. Get audit trail for all operations
    user_audit = audit_trail_crud.get_by_user(db=db, user_id=user_id)
    fine_audit = audit_trail_crud.get_by_table_and_record(
        db=db, 
        table_name="fines", 
        record_id=fine.id
    )
    
    # 6. Soft delete fine
    deleted_fine = fine_crud.soft_delete(
        db=db,
        id=fine.id,
        user_id=user_id,
        reason="User requested deletion"
    )
    
    # 7. Get statistics
    stats = fine_crud.count_records(db=db)
    
    # 8. GDPR compliance: Handle data export request
    gdpr_service = create_gdpr_service(db)
    export_result = gdpr_service.handle_data_subject_request(
        user_id=user_id,
        request_type="export"
    )
    
    return {
        "user": user,
        "fine": fine,
        "defense": defense,
        "updated_fine": updated_fine,
        "audit_trail": user_audit,
        "statistics": stats,
        "gdpr_export": export_result
    }
```

### Bulk Operations Example

```python
def bulk_fine_operations(db: Session, user_id: int, fine_ids: list):
    # Bulk soft delete
    deleted_count = fine_crud.bulk_soft_delete(
        db=db,
        ids=fine_ids,
        user_id=user_id,
        reason="Bulk deletion requested"
    )
    
    # Get statistics before bulk restore
    stats_before = fine_crud.count_records(db=db)
    
    # Bulk restore some records
    restore_ids = fine_ids[:len(fine_ids)//2]
    restored_count = 0
    for fine_id in restore_ids:
        restored_fine = fine_crud.restore(db=db, id=fine_id, user_id=user_id)
        if restored_fine:
            restored_count += 1
    
    # Get statistics after operations
    stats_after = fine_crud.count_records(db=db)
    
    return {
        "deleted_count": deleted_count,
        "restored_count": restored_count,
        "stats_before": stats_before,
        "stats_after": stats_after
    }
```

### GDPR Compliance Example

```python
def handle_comprehensive_gdpr_request(db: Session, user_id: int, request_type: str):
    gdpr_service = create_gdpr_service(db)
    
    if request_type == "full_compliance":
        # 1. Export all user data
        export_result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="export"
        )
        
        # 2. Get compliance report
        compliance_report = gdpr_service.get_compliance_report(days=30)
        
        # 3. Clean up old audit data
        cleanup_result = gdpr_service.data_retention_service.run_retention_cleanup(
            dry_run=True
        )
        
        # 4. Get user consents
        consents = gdpr_service.consent_management_service.get_user_consents(user_id)
        
        return {
            "data_export": export_result,
            "compliance_report": compliance_report,
            "retention_cleanup_preview": cleanup_result,
            "user_consents": consents
        }
    
    elif request_type == "deletion":
        # Initiate deletion process
        deletion_result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="delete",
            reason="User GDPR deletion request",
            confirm_deletion=True
        )
        
        # Schedule permanent deletion after retention period
        return {
            "deletion_initiated": True,
            "retention_period_days": 730,
            "permanent_deletion_date": "2026-01-15",
            "deletion_result": deletion_result
        }
    
    elif request_type == "anonymization":
        # Anonymize user data
        anonymization_result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="anonymize",
            reason="User requested anonymization"
        )
        
        return {
            "anonymization_completed": True,
            "data_preserved_for_audit": True,
            "anonymization_result": anonymization_result
        }
```

### Scheduled Retention Cleanup Example

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def scheduled_retention_cleanup():
    """Function to run scheduled retention cleanup"""
    from backend.services.gdpr_compliance_service import run_scheduled_retention_cleanup
    from backend.app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Run cleanup in dry-run mode first
        dry_run_results = run_scheduled_retention_cleanup(db=db, dry_run=True)
        print(f"Dry run results: {dry_run_results}")
        
        # If dry run looks good, run actual cleanup
        if dry_run_results:
            actual_results = run_scheduled_retention_cleanup(db=db, dry_run=False)
            print(f"Actual cleanup results: {actual_results}")
            
            # Log results for audit
            audit_trail_crud._create_audit_entry(
                db,
                None,  # System operation
                'RETENTION_CLEANUP',
                None,
                actual_results,
                None,
                "Automated retention cleanup"
            )
        
    except Exception as e:
        print(f"Error during retention cleanup: {e}")
    finally:
        db.close()

# Set up scheduler
def setup_cleanup_scheduler():
    scheduler = BackgroundScheduler()
    
    # Run cleanup every Sunday at 2 AM
    scheduler.add_job(
        scheduled_retention_cleanup,
        'cron',
        day_of_week='sun',
        hour=2,
        minute=0
    )
    
    scheduler.start()
    return scheduler
```

---

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review audit trail logs for unusual patterns
2. **Monthly**: Generate compliance reports and review retention policies
3. **Quarterly**: Update retention policies based on legal requirements
4. **Annually**: Full system audit and compliance review

### Monitoring

Monitor these key metrics:

- **Audit Trail Growth**: Track size and growth rate of audit_trails table
- **Soft Delete Rate**: Monitor soft delete operations and restore patterns
- **GDPR Requests**: Track data export and deletion requests
- **Retention Cleanup**: Monitor automated cleanup success rates
- **Performance**: Monitor impact on database performance

### Backup Strategy

1. **Database Backups**: Include audit_trails table in regular backups
2. **Configuration Backups**: Backup configuration files regularly
3. **Audit Trail Exports**: Regular exports of critical audit data
4. **Disaster Recovery**: Test restoration procedures regularly

### Updates and Patches

1. **Security Updates**: Apply security patches promptly
2. **Legal Updates**: Update retention policies when laws change
3. **Feature Updates**: Stay current with new GDPR compliance features
4. **Testing**: Thoroughly test all updates in staging environment

---

## Conclusion

The FineHero Soft Delete and Audit Trail System provides a comprehensive, GDPR-compliant solution for data management, audit logging, and privacy protection. With proper configuration and following best practices, this system ensures:

- **Complete Data Protection**: Safe data recovery and privacy compliance
- **Legal Compliance**: Meets EU and Portuguese data protection requirements
- **Operational Excellence**: Comprehensive audit trails for accountability
- **User Rights**: Full support for GDPR data subject rights
- **Automated Compliance**: Reduces manual compliance burden through automation

For additional support or questions, refer to the troubleshooting section or contact the development team.

---

*Last Updated: November 12, 2024*  
*Version: 1.0*  
*Compliance: GDPR, Lei 58/2019 (Portuguese Data Protection)*