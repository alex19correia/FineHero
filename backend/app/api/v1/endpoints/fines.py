from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime

from ....app import crud, models, schemas
from ....app.crud_soft_delete import fine_crud, audit_trail_crud
from ....services.gdpr_compliance_service import GDPRComplianceService, create_gdpr_service
from .... import database

models.Base.metadata.create_all(bind=database.engine)

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user (simplified - would use proper auth in production)
def get_current_user(db: Session = Depends(get_db), request: Request = None):
    """
    Get current user from request headers or JWT token.
    In production, this would use proper JWT authentication.
    """
    user_id = request.headers.get("X-User-ID") if request else None
    if user_id:
        try:
            user_id = int(user_id)
            user = db.query(models.User).filter(
                models.User.id == user_id,
                models.User.is_deleted == False
            ).first()
            if user:
                return user
        except (ValueError, TypeError):
            pass
    
    # Return None for anonymous operations
    return None

@router.post("/fines/", response_model=schemas.Fine)
def create_fine(
    fine: schemas.FineCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
    request: Request = None
):
    """
    Create a new fine with audit trail logging.
    """
    try:
        user_id = current_user.id if current_user else None
        return fine_crud.create_with_audit(db=db, fine=fine, user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating fine: {str(e)}")

@router.get("/fines/", response_model=List[schemas.Fine])
def read_fines(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    """
    Retrieve multiple fines with soft delete filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return non-deleted records
        include_deleted: If True, include soft-deleted records
    """
    try:
        if include_deleted:
            # Admin only - would check permissions in production
            return fine_crud.get_multi_with_relationships(
                db, skip=skip, limit=limit, active_only=False
            )
        else:
            return fine_crud.get_multi_with_relationships(
                db, skip=skip, limit=limit, active_only=active_only
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving fines: {str(e)}")

@router.get("/fines/{fine_id}", response_model=schemas.Fine)
def read_fine(
    fine_id: int,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single fine by ID with optional soft-deleted records.
    """
    try:
        if include_deleted:
            # Admin only
            fine = fine_crud.get_with_deleted(db, id=fine_id)
        else:
            fine = fine_crud.get(db, id=fine_id)
            
        if fine is None:
            raise HTTPException(status_code=404, detail="Fine not found")
        return fine
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving fine: {str(e)}")

@router.put("/fines/{fine_id}", response_model=schemas.Fine)
def update_fine(
    fine_id: int,
    fine_update: schemas.FineUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
    request: Request = None
):
    """
    Update a fine with audit trail logging.
    """
    try:
        user_id = current_user.id if current_user else None
        return fine_crud.update_with_audit(
            db=db, id=fine_id, fine_update=fine_update, user_id=user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating fine: {str(e)}")

@router.delete("/fines/{fine_id}")
def soft_delete_fine(
    fine_id: int,
    reason: Optional[str] = "User requested deletion",
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
    request: Request = None
):
    """
    Soft delete a fine (marks as deleted but preserves for audit).
    """
    try:
        user_id = current_user.id if current_user else None
        fine = fine_crud.soft_delete(db=db, id=fine_id, user_id=user_id, reason=reason)
        
        if fine is None:
            raise HTTPException(status_code=404, detail="Fine not found")
            
        return {"message": "Fine soft deleted successfully", "fine_id": fine_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error soft deleting fine: {str(e)}")

@router.post("/fines/{fine_id}/restore")
def restore_fine(
    fine_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """
    Restore a soft-deleted fine.
    """
    try:
        user_id = current_user.id if current_user else None
        fine = fine_crud.restore(db=db, id=fine_id, user_id=user_id)
        
        if fine is None:
            raise HTTPException(status_code=404, detail="Soft-deleted fine not found")
            
        return {"message": "Fine restored successfully", "fine_id": fine_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring fine: {str(e)}")

@router.post("/fines/{fine_id}/permanent-delete")
def permanent_delete_fine(
    fine_id: int,
    reason: Optional[str] = "Permanent deletion requested",
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """
    Permanently delete a fine (hard delete - cannot be undone).
    
    WARNING: This operation cannot be undone and should only be used
    after legal review and proper notification periods.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Permanent deletion requires confirmation. Set confirm=true"
        )
    
    try:
        user_id = current_user.id if current_user else None
        success = fine_crud.permanent_delete(db=db, id=fine_id, user_id=user_id, reason=reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Fine not found")
            
        return {"message": "Fine permanently deleted", "fine_id": fine_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error permanently deleting fine: {str(e)}")

@router.get("/fines/{fine_id}/audit-trail")
def get_fine_audit_trail(
    fine_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get audit trail for a specific fine.
    """
    try:
        audit_trail = audit_trail_crud.get_by_table_and_record(
            db, table_name="fines", record_id=fine_id, limit=limit
        )
        
        return {
            "fine_id": fine_id,
            "audit_trail": [
                {
                    "action": entry.action,
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "additional_info": entry.additional_info,
                    "old_values": entry.old_values,
                    "new_values": entry.new_values
                }
                for entry in audit_trail
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit trail: {str(e)}")

@router.get("/fines/user/{user_id}")
def get_user_fines(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all fines for a specific user.
    """
    try:
        fines = fine_crud.get_user_fines(
            db, user_id=user_id, skip=skip, limit=limit
        )
        return fines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user fines: {str(e)}")

@router.get("/fines/statistics")
def get_fines_statistics(
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get statistics about fines (for admin dashboard).
    """
    try:
        total_count = fine_crud.count_records(db, include_deleted=include_deleted)
        active_count = fine_crud.count_records(db, include_deleted=False)
        deleted_count = total_count - active_count
        
        return {
            "total_fines": total_count,
            "active_fines": active_count,
            "deleted_fines": deleted_count,
            "deleted_percentage": round((deleted_count / total_count * 100), 2) if total_count > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

# GDPR Compliance Endpoints

@router.post("/fines/gdpr/export/{user_id}")
def export_user_fines_data(
    user_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """
    Export fines data for a specific user (GDPR compliance).
    
    This endpoint supports data portability requests under GDPR Article 20.
    """
    try:
        # Check if user is authorized to request this export
        if current_user and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to export this user's data")
        
        # Create GDPR service and export user data
        gdpr_service = create_gdpr_service(db)
        result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="export"
        )
        
        if result["status"] == "completed":
            return {
                "status": "success",
                "message": "User fines data exported successfully",
                "export_data": result.get("data", {})
            }
        else:
            raise HTTPException(status_code=500, detail="Data export failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting user data: {str(e)}")

@router.post("/fines/gdpr/delete/{user_id}")
def initiate_user_fines_deletion(
    user_id: int,
    reason: str = "User requested deletion",
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """
    Initiate soft deletion of user's fines data (GDPR compliance).
    
    This endpoint supports the right to erasure under GDPR Article 17.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deletion request requires confirmation. Set confirm=true"
        )
    
    try:
        # Check if user is authorized to request this deletion
        if current_user and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this user's data")
        
        # Create GDPR service and handle deletion request
        gdpr_service = create_gdpr_service(db)
        result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="delete",
            reason=reason,
            confirm_deletion=True
        )
        
        if result["status"] == "completed":
            return {
                "status": "success",
                "message": result["message"],
                "retention_days": result.get("retention_days", 730)
            }
        else:
            raise HTTPException(status_code=500, detail="Deletion request failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing deletion request: {str(e)}")

# Import database session (needed for dependencies)
SessionLocal = database.SessionLocal
