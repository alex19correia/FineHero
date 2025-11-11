"""
Stripe Payment Service
Handles all Stripe API operations including customers, subscriptions, payments, and webhooks.
"""

import json
import os
import stripe
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone

from ..app.models import (
    StripeCustomer, StripeSubscription, Payment, PaymentMethod, 
    WebhookEvent, User, PaymentStatus, SubscriptionStatus
)


class StripeService:
    """
    Service class for handling Stripe API operations.
    """
    
    def __init__(self):
        """Initialize Stripe with API key from environment."""
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.stripe_api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
        
        # Initialize Stripe client
        stripe.api_key = self.stripe_api_key
        
        # Stripe webhook endpoint secret
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    def create_customer(self, db: Session, user_id: int, email: str, name: str = None, 
                       description: str = None, metadata: Dict[str, Any] = None) -> StripeCustomer:
        """
        Create a Stripe customer for a user.
        """
        # Create Stripe customer
        stripe_params = {
            "email": email,
            "metadata": {
                "user_id": str(user_id),
                **(metadata or {})
            }
        }
        
        if name:
            stripe_params["name"] = name
        if description:
            stripe_params["description"] = description
            
        stripe_customer = stripe.Customer.create(**stripe_params)
        
        # Create local database record
        db_customer = StripeCustomer(
            user_id=user_id,
            stripe_customer_id=stripe_customer.id,
            email=email,
            name=name,
            description=description,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        return db_customer
    
    def get_or_create_customer(self, db: Session, user_id: int) -> Optional[StripeCustomer]:
        """
        Get existing customer or create new one.
        """
        customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == user_id
        ).first()
        
        if customer:
            return customer
        
        # Create new customer
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        return self.create_customer(
            db=db,
            user_id=user_id,
            email=user.email,
            name=user.full_name,
            metadata={"subscription_tier": user.subscription_tier}
        )
    
    def create_payment_intent(self, db: Session, customer_id: int, amount: int, 
                            currency: str = "eur", description: str = None,
                            metadata: Dict[str, Any] = None, 
                            customer_email: str = None) -> Payment:
        """
        Create a payment intent for processing payments.
        """
        # Get customer
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == customer_id
        ).first()
        
        if not stripe_customer:
            raise ValueError(f"Stripe customer for user {customer_id} not found")
        
        # Create Stripe payment intent
        params = {
            "amount": amount,
            "currency": currency,
            "customer": stripe_customer.stripe_customer_id,
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never"
            },
            "metadata": {
                "user_id": str(customer_id),
                **(metadata or {})
            }
        }
        
        if description:
            params["description"] = description
        if customer_email:
            params["receipt_email"] = customer_email
            
        stripe_payment_intent = stripe.PaymentIntent.create(**params)
        
        # Create local payment record
        payment = Payment(
            customer_id=stripe_customer.id,
            stripe_payment_intent_id=stripe_payment_intent.id,
            amount=amount,
            currency=currency,
            description=description,
            receipt_email=customer_email,
            client_secret=stripe_payment_intent.client_secret,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return payment
    
    def create_subscription(self, db: Session, user_id: int, price_id: str,
                          trial_days: int = None, metadata: Dict[str, Any] = None) -> StripeSubscription:
        """
        Create a subscription for a user.
        """
        # Get customer
        stripe_customer = self.get_or_create_customer(db, user_id)
        
        # Retrieve price information from Stripe
        price = stripe.Price.retrieve(price_id)
        
        # Create subscription parameters
        subscription_params = {
            "customer": stripe_customer.stripe_customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "payment_settings": {
                "save_default_payment_method": "on_subscription"
            },
            "expand": ["latest_invoice.payment_intent"],
            "metadata": {
                "user_id": str(user_id),
                **(metadata or {})
            }
        }
        
        if trial_days:
            subscription_params["trial_period_days"] = trial_days
        
        stripe_subscription = stripe.Subscription.create(**subscription_params)
        
        # Create local subscription record
        subscription = StripeSubscription(
            customer_id=stripe_customer.id,
            stripe_subscription_id=stripe_subscription.id,
            status=SubscriptionStatus(stripe_subscription.status),
            price_id=price_id,
            product_id=price.product,
            currency=stripe_subscription.currency,
            amount=price.unit_amount if price.unit_amount else 0,
            current_period_start=datetime.fromtimestamp(
                stripe_subscription.current_period_start, tz=timezone.utc
            ),
            current_period_end=datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            ),
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    def get_subscription(self, db: Session, subscription_id: str) -> StripeSubscription:
        """
        Get subscription from database.
        """
        return db.query(StripeSubscription).filter(
            StripeSubscription.stripe_subscription_id == subscription_id
        ).first()
    
    def update_subscription(self, db: Session, subscription_id: str, 
                           price_id: str = None, metadata: Dict[str, Any] = None) -> StripeSubscription:
        """
        Update an existing subscription.
        """
        # Get subscription
        subscription = self.get_subscription(db, subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Update in Stripe
        update_params = {}
        if price_id:
            update_params["items"] = [{"price": price_id}]
        if metadata:
            update_params["metadata"] = {
                **json.loads(subscription.metadata or "{}"),
                **metadata
            }
        
        stripe_subscription = stripe.Subscription.modify(
            subscription_id, **update_params
        )
        
        # Update local record
        subscription.status = SubscriptionStatus(stripe_subscription.status)
        if price_id:
            subscription.price_id = price_id
        if metadata:
            subscription.metadata = json.dumps(metadata)
            
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    def cancel_subscription(self, db: Session, subscription_id: str, 
                          prorate: bool = True) -> StripeSubscription:
        """
        Cancel a subscription.
        """
        # Get subscription
        subscription = self.get_subscription(db, subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Cancel in Stripe
        stripe_subscription = stripe.Subscription.cancel(
            subscription_id, prorate=prorate
        )
        
        # Update local record
        subscription.status = SubscriptionStatus(stripe_subscription.status)
        subscription.canceled_at = datetime.fromtimestamp(
            stripe_subscription.canceled_at, tz=timezone.utc
        ) if stripe_subscription.canceled_at else None
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    def create_customer_portal_session(self, customer_id: int, 
                                      return_url: str = None) -> Dict[str, Any]:
        """
        Create a Stripe customer portal session.
        """
        # Get Stripe customer ID
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == customer_id
        ).first()
        
        if not stripe_customer:
            raise ValueError(f"Stripe customer for user {customer_id} not found")
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer.stripe_customer_id,
            return_url=return_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
        )
        
        return {"url": portal_session.url}
    
    def construct_webhook_event(self, payload: bytes, signature: str) -> stripe.Event:
        """
        Construct and validate webhook event.
        """
        try:
            if not self.webhook_secret:
                raise ValueError("STRIPE_WEBHOOK_SECRET is required for webhook validation")
            
            return stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError as e:
            raise ValueError(f"Invalid webhook signature: {e}")
        except Exception as e:
            raise ValueError(f"Error constructing webhook event: {e}")
    
    def handle_webhook_event(self, db: Session, event: stripe.Event) -> bool:
        """
        Handle incoming webhook events.
        """
        # Check if event already processed
        existing_event = db.query(WebhookEvent).filter(
            WebhookEvent.stripe_event_id == event.id
        ).first()
        
        if existing_event:
            return existing_event.processed
        
        # Create webhook event record
        webhook_event = WebhookEvent(
            stripe_event_id=event.id,
            event_type=event.type,
            api_version=event.api_version,
            created=datetime.fromtimestamp(event.created, tz=timezone.utc),
            data=json.dumps(event.data.object.to_dict()),
            livemode=event.livemode
        )
        
        db.add(webhook_event)
        
        try:
            # Handle specific event types
            if event.type == "payment_intent.succeeded":
                self._handle_payment_intent_succeeded(db, event.data.object)
            elif event.type == "payment_intent.payment_failed":
                self._handle_payment_intent_failed(db, event.data.object)
            elif event.type == "customer.subscription.created":
                self._handle_subscription_created(db, event.data.object)
            elif event.type == "customer.subscription.updated":
                self._handle_subscription_updated(db, event.data.object)
            elif event.type == "customer.subscription.deleted":
                self._handle_subscription_deleted(db, event.data.object)
            elif event.type == "invoice.payment_succeeded":
                self._handle_invoice_payment_succeeded(db, event.data.object)
            elif event.type == "invoice.payment_failed":
                self._handle_invoice_payment_failed(db, event.data.object)
            
            # Mark event as processed
            webhook_event.processed = True
            webhook_event.processed_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            # Log error and mark as failed
            webhook_event.error_message = str(e)
            db.commit()
            print(f"Error processing webhook event {event.id}: {e}")
            return False
    
    def _handle_payment_intent_succeeded(self, db: Session, payment_intent: stripe.PaymentIntent):
        """Handle successful payment intent."""
        # Update payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.succeeded
            payment.updated_at = datetime.utcnow()
    
    def _handle_payment_intent_failed(self, db: Session, payment_intent: stripe.PaymentIntent):
        """Handle failed payment intent."""
        # Update payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.failed
            payment.updated_at = datetime.utcnow()
    
    def _handle_subscription_created(self, db: Session, subscription: stripe.Subscription):
        """Handle subscription creation."""
        # Find customer
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.stripe_customer_id == subscription.customer
        ).first()
        
        if stripe_customer:
            # Update or create subscription record
            existing_sub = db.query(StripeSubscription).filter(
                StripeSubscription.stripe_subscription_id == subscription.id
            ).first()
            
            if existing_sub:
                existing_sub.status = SubscriptionStatus(subscription.status)
            else:
                # Create new subscription record
                new_subscription = StripeSubscription(
                    customer_id=stripe_customer.id,
                    stripe_subscription_id=subscription.id,
                    status=SubscriptionStatus(subscription.status),
                    price_id=subscription.items.data[0].price.id if subscription.items.data else None,
                    product_id=subscription.items.data[0].price.product if subscription.items.data else None,
                    currency=subscription.currency,
                    amount=subscription.items.data[0].price.unit_amount if subscription.items.data and subscription.items.data[0].price.unit_amount else 0,
                    current_period_start=datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                    current_period_end=datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
                )
                db.add(new_subscription)
    
    def _handle_subscription_updated(self, db: Session, subscription: stripe.Subscription):
        """Handle subscription updates."""
        # Find and update subscription record
        existing_sub = db.query(StripeSubscription).filter(
            StripeSubscription.stripe_subscription_id == subscription.id
        ).first()
        
        if existing_sub:
            existing_sub.status = SubscriptionStatus(subscription.status)
            existing_sub.current_period_start = datetime.fromtimestamp(
                subscription.current_period_start, tz=timezone.utc
            )
            existing_sub.current_period_end = datetime.fromtimestamp(
                subscription.current_period_end, tz=timezone.utc
            )
            existing_sub.cancel_at = datetime.fromtimestamp(
                subscription.cancel_at, tz=timezone.utc
            ) if subscription.cancel_at else None
            existing_sub.cancel_at_period_end = subscription.cancel_at_period_end
            existing_sub.canceled_at = datetime.fromtimestamp(
                subscription.canceled_at, tz=timezone.utc
            ) if subscription.canceled_at else None
    
    def _handle_subscription_deleted(self, db: Session, subscription: stripe.Subscription):
        """Handle subscription deletion."""
        # Find and mark as canceled
        existing_sub = db.query(StripeSubscription).filter(
            StripeSubscription.stripe_subscription_id == subscription.id
        ).first()
        
        if existing_sub:
            existing_sub.status = SubscriptionStatus.canceled
            existing_sub.canceled_at = datetime.fromtimestamp(
                subscription.canceled_at, tz=timezone.utc
            ) if subscription.canceled_at else None
    
    def _handle_invoice_payment_succeeded(self, db: Session, invoice: stripe.Invoice):
        """Handle successful invoice payment."""
        # Update subscription status if needed
        if invoice.subscription:
            subscription = db.query(StripeSubscription).filter(
                StripeSubscription.stripe_subscription_id == invoice.subscription
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.active
    
    def _handle_invoice_payment_failed(self, db: Session, invoice: stripe.Invoice):
        """Handle failed invoice payment."""
        # Update subscription status if needed
        if invoice.subscription:
            subscription = db.query(StripeSubscription).filter(
                StripeSubscription.stripe_subscription_id == invoice.subscription
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.past_due
    
    def get_user_subscriptions(self, db: Session, user_id: int) -> List[StripeSubscription]:
        """Get all subscriptions for a user."""
        return db.query(StripeSubscription).join(StripeCustomer).filter(
            StripeCustomer.user_id == user_id
        ).all()
    
    def get_user_payments(self, db: Session, user_id: int) -> List[Payment]:
        """Get all payments for a user."""
        return db.query(Payment).join(StripeCustomer).filter(
            StripeCustomer.user_id == user_id
        ).order_by(Payment.created_at.desc()).all()
    
    def get_customer_portal_url(self, db: Session, user_id: int) -> str:
        """Get Stripe customer portal URL for a user."""
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == user_id
        ).first()
        
        if not stripe_customer:
            raise ValueError(f"Stripe customer for user {user_id} not found")
        
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer.stripe_customer_id,
            return_url=os.getenv("FRONTEND_URL", "http://localhost:3000/dashboard")
        )
        
        return portal_session.url