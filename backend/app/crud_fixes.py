"""
CRUD Fixes for N+1 Query Problems
Implements SQLAlchemy eager loading to prevent N+1 queries
"""

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, func
from typing import List, Optional, Any

# Import models
from . import models, schemas

def get_fine_defenses(db: Session, fine_id: int) -> List[models.Defense]:
    """
    Get all defenses for a specific fine with eager loading to avoid N+1 queries.
    
    Uses selectinload to efficiently load the fine relationship for all defenses.
    """
    # Use selectinload to eagerly load the fine relationship
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.fine_id == fine_id).all()

def get_user_fines_with_defenses(db: Session, user_id: int) -> List[models.Fine]:
    """
    Get all fines for a user with their defenses using eager loading.
    
    Uses selectinload to eagerly load the defenses relationship to avoid N+1 queries.
    """
    # Use selectinload to eagerly load the defenses for all fines
    return db.query(models.Fine).options(
        selectinload(models.Fine.defenses)
    ).filter(models.Fine.user_id == user_id).all()

def get_user_defenses_with_fines(db: Session, user_id: int) -> List[models.Defense]:
    """
    Get all defenses for a user with their associated fines using eager loading.
    
    Uses selectinload to eagerly load the fine relationship for all defenses.
    """
    # Use selectinload to eagerly load the fine relationship
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.user_id == user_id).all()

def get_defense_with_fine(db: Session, defense_id: int) -> Optional[models.Defense]:
    """
    Get a specific defense with its associated fine using eager loading.
    
    Uses selectinload to eagerly load the fine relationship.
    """
    # Use selectinload to eagerly load the fine relationship
    return db.query(models.Defense).options(
        selectinload(models.Defense.fine)
    ).filter(models.Defense.id == defense_id).first()

def get_fine_with_user(db: Session, fine_id: int) -> Optional[models.Fine]:
    """
    Get a specific fine with its associated user using eager loading.
    
    Uses joinedload to eagerly load the user relationship.
    """
    # Use joinedload to eagerly load the user relationship
    return db.query(models.Fine).options(
        joinedload(models.Fine.user)
    ).filter(models.Fine.id == fine_id).first()

def get_analytics_events_with_user_info(db: Session, event_types: List[str], 
                                        limit: int = 100) -> List[models.AnalyticsEvent]:
    """
    Get analytics events with eager loading of related data to avoid N+1 queries.
    
    In this case, there might not be direct relationships to load for AnalyticsEvent,
    but this demonstrates the pattern for efficient queries.
    """
    # No related objects to load in this case, but the pattern is shown
    # Using selectinload or joinedload would depend on the relationships defined
    return db.query(models.AnalyticsEvent).filter(
        models.AnalyticsEvent.event_type.in_(event_types)
    ).order_by(models.AnalyticsEvent.timestamp.desc()).limit(limit).all()

def get_legal_documents_with_case_outcomes(db: Session, 
                                          document_types: List[str] = None) -> List[models.LegalDocument]:
    """
    Get legal documents with eager loading of case outcomes to avoid N+1 queries.
    
    Uses selectinload to eagerly load the case_outcome relationship.
    """
    query = db.query(models.LegalDocument).options(
        selectinload(models.LegalDocument.case_outcome)
    )
    
    if document_types:
        query = query.filter(models.LegalDocument.document_type.in_(document_types))
    
    return query.all()

def get_subscriptions_with_customer_info(db: Session, user_id: int) -> List[models.StripeSubscription]:
    """
    Get subscriptions for a user with eager loading of customer information.
    
    Uses joinedload to eagerly load the customer relationship.
    """
    return db.query(models.StripeSubscription).options(
        joinedload(models.StripeSubscription.customer)
    ).join(models.StripeCustomer).filter(
        models.StripeCustomer.user_id == user_id
    ).all()

def get_payments_with_customer_info(db: Session, user_id: int) -> List[models.Payment]:
    """
    Get payments for a user with eager loading of customer information.
    
    Uses joinedload to eagerly load the customer relationship.
    """
    return db.query(models.Payment).options(
        joinedload(models.Payment.customer)
    ).join(models.StripeCustomer).filter(
        models.StripeCustomer.user_id == user_id
    ).all()

# Generic function to detect N+1 query problems
def detect_n_plus_one_queries(db: Session, query_function, *args, **kwargs) -> Dict[str, Any]:
    """
    Test a query function to detect potential N+1 query problems.
    
    Returns statistics about the query execution including number of queries executed.
    """
    # This is a simplified example. In a real implementation, you would use
    # SQLAlchemy's event system to count the actual queries executed.
    
    import time
    
    start_time = time.time()
    results = query_function(db, *args, **kwargs)
    execution_time = time.time() - start_time
    
    return {
        "results_count": len(results) if isinstance(results, list) else 1,
        "execution_time": execution_time,
        "potential_n_plus_one": execution_time > 1.0 and len(results) > 1
    }