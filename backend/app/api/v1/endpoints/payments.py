"""
Stripe Payment Endpoints
REST API endpoints for Stripe payment operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import os

from ....app import schemas_payment as schemas
from ....app.models import User
from ....services.stripe_service import StripeService
from .fines import get_db  # Reuse the get_db dependency

router = APIRouter()
stripe_service = StripeService()


# Customer Management Endpoints
@router.post("/customers", response_model=schemas.StripeCustomerResponse)
def create_customer(
    customer_data: schemas.StripeCustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Create a Stripe customer for the current user.
    """
    try:
        customer = stripe_service.create_customer(
            db=db,
            user_id=current_user.id,
            email=customer_data.email,
            name=customer_data.name,
            description=customer_data.description,
            metadata=customer_data.metadata
        )
        return customer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create customer: {str(e)}")


@router.get("/customers/me", response_model=schemas.StripeCustomerResponse)
def get_my_customer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get the current user's Stripe customer information.
    """
    try:
        customer = stripe_service.get_or_create_customer(db, current_user.id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.put("/customers/me", response_model=schemas.StripeCustomerResponse)
def update_my_customer(
    customer_data: schemas.StripeCustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Update the current user's Stripe customer information.
    """
    # Note: This would need to be implemented in StripeService
    # For now, return a placeholder response
    raise HTTPException(status_code=501, detail="Customer update not yet implemented")


# Payment Intent Endpoints
@router.post("/payments/intents", response_model=schemas.PaymentIntentResponse)
def create_payment_intent(
    payment_data: schemas.PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Create a payment intent for processing payments.
    """
    try:
        payment = stripe_service.create_payment_intent(
            db=db,
            customer_id=current_user.id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            metadata=payment_data.metadata,
            customer_email=payment_data.receipt_email
        )
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment intent: {str(e)}")


@router.get("/payments", response_model=schemas.PaymentsList)
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get all payments for the current user.
    """
    try:
        payments = stripe_service.get_user_payments(db, current_user.id)
        return schemas.PaymentsList(payments=payments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payments: {str(e)}")


@router.get("/payments/{payment_intent_id}", response_model=schemas.PaymentIntentResponse)
def get_payment(
    payment_intent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get a specific payment intent.
    """
    try:
        payment = db.query(models.Payment).join(models.StripeCustomer).filter(
            models.Payment.stripe_payment_intent_id == payment_intent_id,
            models.StripeCustomer.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return payment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment: {str(e)}")


# Subscription Management Endpoints
@router.post("/subscriptions", response_model=schemas.SubscriptionResponse)
def create_subscription(
    subscription_data: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Create a new subscription for the current user.
    """
    try:
        subscription = stripe_service.create_subscription(
            db=db,
            user_id=current_user.id,
            price_id=subscription_data.price_id,
            trial_days=subscription_data.trial_days,
            metadata=subscription_data.metadata
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/subscriptions", response_model=schemas.SubscriptionsList)
def get_my_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get all subscriptions for the current user.
    """
    try:
        subscriptions = stripe_service.get_user_subscriptions(db, current_user.id)
        return schemas.SubscriptionsList(subscriptions=subscriptions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscriptions: {str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=schemas.SubscriptionResponse)
def update_subscription(
    subscription_id: str,
    subscription_data: schemas.SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Update an existing subscription.
    """
    try:
        subscription = stripe_service.update_subscription(
            db=db,
            subscription_id=subscription_id,
            price_id=subscription_data.price_id,
            metadata=subscription_data.metadata
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")


@router.delete("/subscriptions/{subscription_id}", response_model=schemas.SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    prorate: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Cancel a subscription.
    """
    try:
        subscription = stripe_service.cancel_subscription(
            db=db,
            subscription_id=subscription_id,
            prorate=prorate
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


# Customer Portal Endpoints
@router.post("/portal-session", response_model=schemas.CustomerPortalResponse)
def create_customer_portal_session(
    portal_data: schemas.CustomerPortalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Create a Stripe customer portal session for billing management.
    """
    try:
        portal_url = stripe_service.create_customer_portal_session(
            customer_id=current_user.id,
            return_url=portal_data.return_url
        )
        return portal_url
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@router.get("/portal-url", response_model=schemas.CustomerPortalResponse)
def get_customer_portal_url(
    return_url: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get the Stripe customer portal URL for the current user.
    """
    try:
        portal_url = stripe_service.get_customer_portal_url(db, current_user.id)
        return schemas.CustomerPortalResponse(url=portal_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portal URL: {str(e)}")


# Billing Overview Endpoint
@router.get("/billing-overview", response_model=schemas.BillingOverview)
def get_billing_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get comprehensive billing information for the current user.
    """
    try:
        # Get customer
        customer = stripe_service.get_or_create_customer(db, current_user.id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get subscriptions
        subscriptions = stripe_service.get_user_subscriptions(db, current_user.id)
        
        # Get payments
        payments = stripe_service.get_user_payments(db, current_user.id)
        
        # Calculate totals
        total_monthly_amount = sum(
            sub.amount for sub in subscriptions 
            if sub.status.value == "active"
        )
        
        active_subscription_count = len([
            sub for sub in subscriptions 
            if sub.status.value == "active"
        ])
        
        return schemas.BillingOverview(
            customer=customer,
            subscriptions=subscriptions,
            payments=payments[:10],  # Limit to last 10 payments
            total_monthly_amount=total_monthly_amount,
            active_subscription_count=active_subscription_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing overview: {str(e)}")


# Customer Statistics Endpoint
@router.get("/stats", response_model=schemas.CustomerStats)
def get_customer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Will be added when auth is implemented
):
    """
    Get billing statistics for the current user.
    """
    try:
        payments = stripe_service.get_user_payments(db, current_user.id)
        subscriptions = stripe_service.get_user_subscriptions(db, current_user.id)
        
        # Calculate stats
        total_spent = sum(payment.amount for payment in payments if payment.status.value == "succeeded")
        total_payments = len(payments)
        successful_payments = len([p for p in payments if p.status.value == "succeeded"])
        failed_payments = len([p for p in payments if p.status.value == "failed"])
        active_subscriptions = len([s for s in subscriptions if s.status.value == "active"])
        
        last_payment_date = None
        subscription_start_date = None
        
        if successful_payments > 0:
            last_payment = max([p for p in payments if p.status.value == "succeeded"], key=lambda p: p.created_at)
            last_payment_date = last_payment.created_at
        
        if active_subscriptions > 0:
            earliest_sub = min([s for s in subscriptions if s.status.value == "active"], key=lambda s: s.created_at)
            subscription_start_date = earliest_sub.created_at
        
        return schemas.CustomerStats(
            total_spent=total_spent,
            total_payments=total_payments,
            successful_payments=successful_payments,
            failed_payments=failed_payments,
            active_subscriptions=active_subscriptions,
            last_payment_date=last_payment_date,
            subscription_start_date=subscription_start_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer stats: {str(e)}")


# Product and Price Information Endpoints
@router.get("/products", response_model=schemas.ProductsList)
def get_products():
    """
    Get available products from Stripe.
    """
    try:
        import stripe
        products = stripe.Product.list(limit=100)
        return schemas.ProductsList(products=[
            schemas.ProductInfo(
                id=product.id,
                name=product.name,
                description=product.description,
                images=product.images,
                metadata=product.metadata
            )
            for product in products.data
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")


@router.get("/prices", response_model=schemas.PricesList)
def get_prices():
    """
    Get available prices from Stripe.
    """
    try:
        import stripe
        prices = stripe.Price.list(limit=100, active=True)
        return schemas.PricesList(prices=[
            schemas.PriceInfo(
                id=price.id,
                product=price.product,
                nickname=price.nickname,
                unit_amount=price.unit_amount,
                currency=price.currency,
                recurring=price.recurring,
                metadata=price.metadata
            )
            for price in prices.data
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prices: {str(e)}")


# Webhook Endpoints (no auth required)
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.
    """
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # Construct and validate webhook event
        event = stripe_service.construct_webhook_event(payload, signature)
        
        # Handle the event
        success = stripe_service.handle_webhook_event(db, event)
        
        if success:
            return {"status": "success", "message": "Webhook processed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process webhook")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# Health Check Endpoint
@router.get("/health")
def payment_health_check():
    """
    Health check endpoint for the payment system.
    """
    try:
        # Test Stripe connection
        import stripe
        stripe.Account.retrieve()
        return {"status": "healthy", "stripe": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "stripe": f"disconnected: {str(e)}"}


# Import proper authentication dependencies from existing auth system
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

# Reuse the OAuth2 scheme and authentication logic from auth endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Secure JWT token-based authentication dependency.
    Replaces the insecure placeholder with proper token validation.
    """
    from app.auth import verify_token
    from app.models import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user