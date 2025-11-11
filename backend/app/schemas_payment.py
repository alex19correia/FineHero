"""
Pydantic schemas for Stripe payment operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PaymentStatusEnum(str, Enum):
    """Payment status enumeration."""
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class SubscriptionStatusEnum(str, Enum):
    """Subscription status enumeration."""
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"


# Customer Schemas
class StripeCustomerBase(BaseModel):
    """Base Stripe customer schema."""
    email: str = Field(..., description="Customer email address")
    name: Optional[str] = Field(None, description="Customer full name")
    description: Optional[str] = Field(None, description="Customer description")


class StripeCustomerCreate(StripeCustomerBase):
    """Schema for creating a Stripe customer."""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class StripeCustomerUpdate(BaseModel):
    """Schema for updating a Stripe customer."""
    email: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StripeCustomerResponse(StripeCustomerBase):
    """Schema for Stripe customer response."""
    id: int
    user_id: int
    stripe_customer_id: str
    metadata: Optional[str] = None
    default_payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payment Intent Schemas
class PaymentIntentBase(BaseModel):
    """Base payment intent schema."""
    amount: int = Field(..., ge=1, description="Amount in cents")
    currency: str = Field(default="eur", description="Three-letter currency code")
    description: Optional[str] = Field(None, description="Payment description")
    receipt_email: Optional[str] = Field(None, description="Email for receipt")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class PaymentIntentCreate(PaymentIntentBase):
    """Schema for creating a payment intent."""
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        if len(v) != 3 or not v.islower():
            raise ValueError('Currency must be 3 lowercase letters (e.g., "eur", "usd")')
        return v


class PaymentIntentResponse(PaymentIntentBase):
    """Schema for payment intent response."""
    id: int
    customer_id: Optional[int] = None
    stripe_payment_intent_id: str
    status: PaymentStatusEnum
    payment_method_id: Optional[str] = None
    payment_method_type: Optional[str] = None
    client_secret: Optional[str] = None
    confirmation_method: Optional[str] = None
    stripe_webhook_event_id: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Subscription Schemas
class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    price_id: str = Field(..., description="Stripe price ID")
    trial_days: Optional[int] = Field(None, ge=0, le=365, description="Trial period in days")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    price_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""
    id: int
    customer_id: int
    stripe_subscription_id: str
    status: SubscriptionStatusEnum
    product_id: Optional[str] = None
    quantity: int
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    """Base payment method schema."""
    type: str = Field(..., description="Payment method type (card, bank_account, etc.)")
    is_default: bool = Field(default=False, description="Whether this is the default payment method")


class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating a payment method."""
    stripe_payment_method_id: str = Field(..., description="Stripe payment method ID")


class PaymentMethodResponse(PaymentMethodBase):
    """Schema for payment method response."""
    id: int
    customer_id: int
    stripe_payment_method_id: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    billing_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Webhook Event Schemas
class WebhookEventBase(BaseModel):
    """Base webhook event schema."""
    event_type: str = Field(..., description="Stripe event type")
    data: Dict[str, Any] = Field(..., description="Event data")


class WebhookEventCreate(WebhookEventBase):
    """Schema for creating webhook event."""
    stripe_event_id: str = Field(..., description="Stripe event ID")
    api_version: Optional[str] = None
    created: datetime
    data: str = Field(..., description="Event data as JSON string")
    livemode: bool = False


class WebhookEventResponse(WebhookEventBase):
    """Schema for webhook event response."""
    id: int
    stripe_event_id: str
    api_version: Optional[str] = None
    created: datetime
    data: str
    livemode: bool
    processed: bool
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Customer Portal Schemas
class CustomerPortalRequest(BaseModel):
    """Schema for customer portal request."""
    return_url: Optional[str] = Field(None, description="URL to redirect after portal session")


class CustomerPortalResponse(BaseModel):
    """Schema for customer portal response."""
    url: str = Field(..., description="Customer portal URL")


# Billing Overview Schemas
class BillingOverview(BaseModel):
    """Schema for billing overview."""
    customer: StripeCustomerResponse
    subscriptions: List[SubscriptionResponse] = Field(default_factory=list)
    payments: List[PaymentIntentResponse] = Field(default_factory=list)
    total_monthly_amount: int = Field(..., description="Total monthly subscription amount in cents")
    active_subscription_count: int = Field(..., description="Number of active subscriptions")


# Payment Methods List Schemas
class PaymentMethodsList(BaseModel):
    """Schema for list of payment methods."""
    payment_methods: List[PaymentMethodResponse] = Field(default_factory=list)


# Subscriptions List Schemas
class SubscriptionsList(BaseModel):
    """Schema for list of subscriptions."""
    subscriptions: List[SubscriptionResponse] = Field(default_factory=list)


# Payments List Schemas
class PaymentsList(BaseModel):
    """Schema for list of payments."""
    payments: List[PaymentIntentResponse] = Field(default_factory=list)


# Customer Stats Schemas
class CustomerStats(BaseModel):
    """Schema for customer statistics."""
    total_spent: int = Field(..., description="Total amount spent in cents")
    total_payments: int = Field(..., description="Total number of payments")
    successful_payments: int = Field(..., description="Number of successful payments")
    failed_payments: int = Field(..., description="Number of failed payments")
    active_subscriptions: int = Field(..., description="Number of active subscriptions")
    last_payment_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None


# Price Information Schemas
class PriceInfo(BaseModel):
    """Schema for price information."""
    id: str
    product: str
    nickname: Optional[str] = None
    unit_amount: int
    currency: str
    recurring: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class PricesList(BaseModel):
    """Schema for list of prices."""
    prices: List[PriceInfo] = Field(default_factory=list)


# Product Information Schemas
class ProductInfo(BaseModel):
    """Schema for product information."""
    id: str
    name: str
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ProductsList(BaseModel):
    """Schema for list of products."""
    products: List[ProductInfo] = Field(default_factory=list)


# API Response Schemas
class ApiResponse(BaseModel):
    """Base API response schema."""
    success: bool
    message: str
    data: Optional[Any] = None


class ApiError(BaseModel):
    """Schema for API error responses."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None