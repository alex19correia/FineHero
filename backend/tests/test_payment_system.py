"""
Test suite for Stripe Payment System
Comprehensive testing for payment functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variables for testing
os.environ["STRIPE_SECRET_KEY"] = "sk_test_1234567890"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_1234567890"

from backend.app.models import Base, User, StripeCustomer, StripeSubscription, Payment
from backend.app.schemas_payment import (
    StripeCustomerCreate, PaymentIntentCreate, SubscriptionCreate,
    CustomerPortalRequest
)
from backend.services.stripe_service import StripeService


class TestPaymentSystem:
    """Test suite for payment system functionality."""
    
    @pytest.fixture
    def setup_database(self):
        """Setup in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        yield db
        db.close()
    
    @pytest.fixture
    def setup_stripe_service(self):
        """Setup Stripe service with mocked Stripe client."""
        with patch('backend.services.stripe_service.stripe') as mock_stripe:
            # Mock Stripe objects
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_customer.email = "test@example.com"
            mock_customer.name = "Test User"
            
            mock_payment_intent = MagicMock()
            mock_payment_intent.id = "pi_test123"
            mock_payment_intent.client_secret = "pi_test123_secret"
            mock_payment_intent.amount = 2000
            mock_payment_intent.currency = "eur"
            
            mock_subscription = MagicMock()
            mock_subscription.id = "sub_test123"
            mock_subscription.status = "active"
            mock_subscription.currency = "eur"
            mock_subscription.current_period_start = 1678886400
            mock_subscription.current_period_end = 1681564800
            
            # Configure mock returns
            mock_stripe.Customer.create.return_value = mock_customer
            mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
            mock_stripe.Subscription.create.return_value = mock_subscription
            mock_stripe.Subscription.cancel.return_value = mock_subscription
            mock_stripe.Subscription.modify.return_value = mock_subscription
            mock_stripe.Price.retrieve.return_value = MagicMock(
                product="prod_test123",
                unit_amount=2000
            )
            mock_stripe.Webhook.construct_event.return_value = MagicMock(
                id="evt_test123",
                type="payment_intent.succeeded",
                data=MagicMock(object=MagicMock(to_dict=lambda: {})),
                api_version="2023-10-16",
                created=1678886400,
                livemode=False
            )
            
            yield StripeService()
    
    @pytest.fixture
    def setup_user(self, setup_database):
        """Create a test user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User"
        )
        setup_database.add(user)
        setup_database.commit()
        setup_database.refresh(user)
        return user
    
    def test_create_customer(self, setup_database, setup_stripe_service, setup_user):
        """Test creating a Stripe customer."""
        customer_data = StripeCustomerCreate(
            email="test@example.com",
            name="Test User",
            description="Test customer"
        )
        
        customer = setup_stripe_service.create_customer(
            db=setup_database,
            user_id=setup_user.id,
            email=customer_data.email,
            name=customer_data.name,
            description=customer_data.description
        )
        
        assert customer is not None
        assert customer.user_id == setup_user.id
        assert customer.stripe_customer_id == "cus_test123"
        assert customer.email == "test@example.com"
    
    def test_get_or_create_customer(self, setup_database, setup_stripe_service, setup_user):
        """Test getting or creating a customer."""
        customer = setup_stripe_service.get_or_create_customer(
            db=setup_database,
            user_id=setup_user.id
        )
        
        assert customer is not None
        assert customer.user_id == setup_user.id
        
        # Test getting existing customer
        existing_customer = setup_stripe_service.get_or_create_customer(
            db=setup_database,
            user_id=setup_user.id
        )
        
        assert existing_customer.id == customer.id
    
    def test_create_payment_intent(self, setup_database, setup_stripe_service, setup_user):
        """Test creating a payment intent."""
        # First create a customer
        setup_stripe_service.get_or_create_customer(
            db=setup_database,
            user_id=setup_user.id
        )
        
        payment_data = PaymentIntentCreate(
            amount=2000,
            currency="eur",
            description="Test payment"
        )
        
        payment = setup_stripe_service.create_payment_intent(
            db=setup_database,
            customer_id=setup_user.id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description
        )
        
        assert payment is not None
        assert payment.amount == 2000
        assert payment.currency == "eur"
        assert payment.description == "Test payment"
        assert payment.stripe_payment_intent_id == "pi_test123"
    
    def test_create_subscription(self, setup_database, setup_stripe_service, setup_user):
        """Test creating a subscription."""
        # First create a customer
        setup_stripe_service.get_or_create_customer(
            db=setup_database,
            user_id=setup_user.id
        )
        
        subscription_data = SubscriptionCreate(
            price_id="price_test123",
            trial_days=14
        )
        
        subscription = setup_stripe_service.create_subscription(
            db=setup_database,
            user_id=setup_user.id,
            price_id=subscription_data.price_id,
            trial_days=subscription_data.trial_days
        )
        
        assert subscription is not None
        assert subscription.status.value == "active"
        assert subscription.price_id == "price_test123"
        assert subscription.stripe_subscription_id == "sub_test123"
    
    def test_cancel_subscription(self, setup_database, setup_stripe_service, setup_user):
        """Test canceling a subscription."""
        # Create subscription first
        subscription = setup_stripe_service.create_subscription(
            db=setup_database,
            user_id=setup_user.id,
            price_id="price_test123"
        )
        
        # Cancel the subscription
        canceled_subscription = setup_stripe_service.cancel_subscription(
            db=setup_database,
            subscription_id=subscription.stripe_subscription_id
        )
        
        assert canceled_subscription.status.value == "canceled"
    
    def test_construct_webhook_event(self, setup_stripe_service):
        """Test webhook event construction."""
        payload = b'{"test": "payload"}'
        signature = "v1=test_signature"
        
        event = setup_stripe_service.construct_webhook_event(payload, signature)
        
        assert event is not None
        assert event.id == "evt_test123"
    
    def test_handle_webhook_event(self, setup_database, setup_stripe_service):
        """Test webhook event handling."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.id = "evt_test123"
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object = MagicMock()
        mock_event.data.object.to_dict.return_value = {"test": "data"}
        mock_event.api_version = "2023-10-16"
        mock_event.created = 1678886400
        mock_event.livemode = False
        
        # Test webhook handling
        result = setup_stripe_service.handle_webhook_event(setup_database, mock_event)
        
        assert result is True
        
        # Check that webhook event was recorded
        webhook_event = setup_database.query(backend.app.models.WebhookEvent).filter(
            backend.app.models.WebhookEvent.stripe_event_id == "evt_test123"
        ).first()
        
        assert webhook_event is not None
        assert webhook_event.processed is True
        assert webhook_event.event_type == "payment_intent.succeeded"
    
    def test_get_user_subscriptions(self, setup_database, setup_stripe_service, setup_user):
        """Test getting user subscriptions."""
        # Create subscription
        subscription = setup_stripe_service.create_subscription(
            db=setup_database,
            user_id=setup_user.id,
            price_id="price_test123"
        )
        
        # Get user subscriptions
        subscriptions = setup_stripe_service.get_user_subscriptions(
            db=setup_database,
            user_id=setup_user.id
        )
        
        assert len(subscriptions) == 1
        assert subscriptions[0].id == subscription.id
    
    def test_get_user_payments(self, setup_database, setup_stripe_service, setup_user):
        """Test getting user payments."""
        # Create customer and payment
        setup_stripe_service.get_or_create_customer(
            db=setup_database,
            user_id=setup_user.id
        )
        
        payment = setup_stripe_service.create_payment_intent(
            db=setup_database,
            customer_id=setup_user.id,
            amount=2000
        )
        
        # Get user payments
        payments = setup_stripe_service.get_user_payments(
            db=setup_database,
            user_id=setup_user.id
        )
        
        assert len(payments) == 1
        assert payments[0].id == payment.id
    
    def test_api_health_check(self, client):
        """Test payment health check endpoint."""
        response = client.get("/api/v1/payments/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "stripe" in data
    
    def test_api_features_endpoint(self, client):
        """Test updated API features endpoint includes payments."""
        response = client.get("/api/v1/features")
        assert response.status_code == 200
        
        data = response.json()
        assert "payment_system" in data["advanced_features"]
        
        payment_endpoints = data["advanced_features"]["payment_system"]["endpoints"]
        assert len(payment_endpoints) > 0
        assert "/api/v1/customers" in payment_endpoints
        assert "/api/v1/payments/intents" in payment_endpoints
        assert "/api/v1/subscriptions" in payment_endpoints
        
        # Check total endpoints count increased
        assert data["total_endpoints"] == 42


class TestPaymentSchemas:
    """Test payment API schemas."""
    
    def test_payment_intent_create_schema(self):
        """Test PaymentIntentCreate schema validation."""
        # Valid data
        valid_data = {
            "amount": 2000,
            "currency": "eur",
            "description": "Test payment"
        }
        
        schema = PaymentIntentCreate(**valid_data)
        assert schema.amount == 2000
        assert schema.currency == "eur"
        assert schema.description == "Test payment"
        
        # Invalid currency
        with pytest.raises(ValueError):
            PaymentIntentCreate(amount=2000, currency="INVALID")
    
    def test_subscription_create_schema(self):
        """Test SubscriptionCreate schema validation."""
        valid_data = {
            "price_id": "price_test123",
            "trial_days": 14
        }
        
        schema = SubscriptionCreate(**valid_data)
        assert schema.price_id == "price_test123"
        assert schema.trial_days == 14
        
        # Invalid trial_days
        with pytest.raises(ValueError):
            SubscriptionCreate(price_id="price_test123", trial_days=400)
    
    def test_customer_portal_request_schema(self):
        """Test CustomerPortalRequest schema validation."""
        valid_data = {
            "return_url": "https://example.com/dashboard"
        }
        
        schema = CustomerPortalRequest(**valid_data)
        assert schema.return_url == "https://example.com/dashboard"
        
        # Empty data (should work with defaults)
        schema_empty = CustomerPortalRequest()
        assert schema_empty.return_url is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])