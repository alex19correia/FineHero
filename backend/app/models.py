from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
from .models_base import SoftDeleteMixin, AuditMixin, TimestampMixin, AuditTrail, Base

# Re-export Base for compatibility
Base = Base

# Enums for payment status
class PaymentStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"

class SubscriptionStatus(enum.Enum):
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"

class Fine(SoftDeleteMixin, AuditMixin):
    """
    Database model for a traffic fine with soft delete and audit capabilities.
    """
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    location = Column(String, index=True)
    infractor = Column(String, index=True)
    fine_amount = Column(Float)
    infraction_code = Column(String, index=True)
    pdf_reference = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="fines")
    defenses = relationship("Defense", back_populates="fine")

class Defense(SoftDeleteMixin, AuditMixin):
    """
    Database model for a defense with soft delete and audit capabilities.
    """
    __tablename__ = "defenses"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    fine_id = Column(Integer, ForeignKey("fines.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    fine = relationship("Fine", back_populates="defenses")
    user = relationship("User", back_populates="defenses")

class LegalDocument(SoftDeleteMixin, AuditMixin):
    """
    Database model for a scraped legal document with soft delete and audit capabilities.
    """
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    document_type = Column(String, index=True) # e.g., 'law', 'precedent', 'defense', 'regulation'
    jurisdiction = Column(String, index=True) # e.g., 'Portugal', 'Lisbon'
    publication_date = Column(Date, nullable=True)
    retrieval_date = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String, unique=True, index=True)
    file_path = Column(String, nullable=True) # Local path to the stored document (e.g., PDF)
    extracted_text = Column(Text)
    
    # Quality Scoring
    quality_score = Column(Float, default=0.0) # Overall quality score
    relevance_score = Column(Float, default=0.0) # Relevance to traffic fines
    freshness_score = Column(Float, default=0.0) # How recent the document is
    authority_score = Column(Float, default=0.0) # Authority level of the source

    # Relationships
    case_outcome_id = Column(Integer, ForeignKey("case_outcomes.id"), nullable=True)
    case_outcome = relationship("CaseOutcome", back_populates="legal_documents")

class CaseOutcome(SoftDeleteMixin, AuditMixin):
    """
    Database model to store information about the outcome of a legal case with soft delete and audit capabilities.
    """
    __tablename__ = "case_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    outcome_type = Column(String, index=True) # e.g., 'successful defense', 'fine upheld', 'appeal granted'
    outcome_date = Column(Date, nullable=True)
    summary = Column(Text, nullable=True)
    citation = Column(String, nullable=True) # Legal citation for the case

    legal_documents = relationship("LegalDocument", back_populates="case_outcome")

class User(SoftDeleteMixin, AuditMixin):
    """
    Database model for user accounts with soft delete and audit capabilities.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(String, default="free") # free, premium, enterprise
    last_login = Column(DateTime, nullable=True)

    # Relationships
    fines = relationship("Fine", back_populates="user")
    defenses = relationship("Defense", back_populates="user")
    stripe_customer = relationship("StripeCustomer", uselist=False, back_populates="user")

class DefenseTemplate(TimestampMixin, SoftDeleteMixin):
    """
    Database model to store templates for generating defenses with soft delete capabilities.
    """
    __tablename__ = "defense_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    template_content = Column(Text)
    document_type = Column(String, index=True) # e.g., 'traffic fine defense', 'appeal letter'
    jurisdiction = Column(String, index=True) # e.g., 'Portugal'
    is_active = Column(Boolean, default=True)

class StripeCustomer(SoftDeleteMixin, AuditMixin):
    """
    Database model for Stripe customers with soft delete and audit capabilities.
    Maps to Stripe's Customer API.
    """
    __tablename__ = "stripe_customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True)
    name = Column(String)
    description = Column(Text)
    metadata = Column(Text)  # JSON string for additional metadata
    
    # Stripe fields
    default_payment_method = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="stripe_customer")
    subscriptions = relationship("StripeSubscription", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")

class StripeSubscription(SoftDeleteMixin, AuditMixin):
    """
    Database model for Stripe subscriptions with soft delete and audit capabilities.
    Maps to Stripe's Subscription API.
    """
    __tablename__ = "stripe_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=False)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.incomplete)
    price_id = Column(String, index=True)  # Stripe price ID
    product_id = Column(String, index=True)  # Stripe product ID
    quantity = Column(Integer, default=1)
    
    # Billing periods
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Billing
    currency = Column(String(3), default="eur")
    amount = Column(Integer)  # Amount in cents
    
    # Cancellation
    cancel_at = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(Text)  # JSON string
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="subscriptions")

class Payment(SoftDeleteMixin, AuditMixin):
    """
    Database model for Stripe payments with soft delete and audit capabilities.
    Maps to Stripe's PaymentIntent API.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=True)
    stripe_payment_intent_id = Column(String, unique=True, index=True, nullable=False)
    
    # Payment details
    amount = Column(Integer)  # Amount in cents
    currency = Column(String(3), default="eur")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    
    # Payment method
    payment_method_id = Column(String, nullable=True)
    payment_method_type = Column(String, nullable=True)
    
    # Billing
    description = Column(Text, nullable=True)
    receipt_email = Column(String, nullable=True)
    
    # Processing
    client_secret = Column(String, nullable=True)
    confirmation_method = Column(String, nullable=True)
    capture_method = Column(String, nullable=True)
    
    # Webhook data
    stripe_webhook_event_id = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(Text)  # JSON string
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="payments")

class PaymentMethod(SoftDeleteMixin, AuditMixin):
    """
    Database model for stored payment methods with soft delete and audit capabilities.
    Maps to Stripe's PaymentMethod API.
    """
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False)
    stripe_payment_method_id = Column(String, unique=True, index=True, nullable=False)
    
    # Payment method details
    type = Column(String, index=True)  # card, bank_account, etc.
    is_default = Column(Boolean, default=False)
    
    # Card details (if applicable)
    card_brand = Column(String, nullable=True)
    card_last4 = Column(String, nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    
    # Billing details
    billing_details = Column(Text, nullable=True)  # JSON string

class WebhookEvent(TimestampMixin):
    """
    Database model for tracking Stripe webhook events.
    """
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, index=True)  # e.g., 'payment_intent.succeeded', 'customer.subscription.created'
    
    # Event data
    api_version = Column(String, nullable=True)
    created = Column(DateTime)
    data = Column(Text)  # JSON string of event data
    livemode = Column(Boolean, default=False)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

# Export all models for imports
__all__ = [
    'Fine', 'Defense', 'LegalDocument', 'CaseOutcome', 'User',
    'DefenseTemplate', 'StripeCustomer', 'StripeSubscription',
    'Payment', 'PaymentMethod', 'WebhookEvent', 'AuditTrail'
]

