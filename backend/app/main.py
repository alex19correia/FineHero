from fastapi import FastAPI
from datetime import datetime, timezone
import logging
from ..core.config import settings
from .api.v1.endpoints import fines, defenses, rag, quality, analytics, knowledge_base, auth, payments
from .middleware.error_handler import add_error_middleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("finehero")

app = FastAPI(title=settings.APP_NAME)

# Add centralized error handling middleware
add_error_middleware(app, logger)

# Register authentication endpoints
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])

# Register existing endpoints
app.include_router(fines.router, prefix="/api/v1", tags=["fines"])
app.include_router(defenses.router, prefix="/api/v1", tags=["defenses"])

# Register new advanced feature endpoints
app.include_router(rag.router, prefix="/api/v1", tags=["rag"])
app.include_router(quality.router, prefix="/api/v1", tags=["quality"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(knowledge_base.router, prefix="/api/v1", tags=["knowledge-base"])

# Register payment endpoints
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": f"Welcome to {settings.APP_NAME}"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/features")
async def get_available_features():
    """
    List all available API features and endpoints.
    """
    return {
        "core_features": {
            "user_authentication": {
                "endpoints": [
                    "/api/v1/auth/register",
                    "/api/v1/auth/login",
                    "/api/v1/auth/me",
                    "/api/v1/auth/logout",
                    "/api/v1/auth/verify-token"
                ],
                "description": "JWT-based user authentication and management"
            },
            "fine_management": {
                "endpoints": ["/api/v1/fines", "/api/v1/fines/{id}"],
                "description": "Create, read, and manage traffic fine records"
            },
            "defense_generation": {
                "endpoints": [
                    "/api/v1/fines/{fine_id}/defenses",
                    "/api/v1/defenses/generate",
                    "/api/v1/defenses/templates",
                    "/api/v1/defenses/validate"
                ],
                "description": "AI-powered defense generation with quality validation"
            }
        },
        "advanced_features": {
            "rag_search": {
                "endpoints": ["/api/v1/rag/search", "/api/v1/rag/knowledge-base/stats"],
                "description": "Advanced RAG system for legal document retrieval"
            },
            "quality_scoring": {
                "endpoints": [
                    "/api/v1/documents/{id}/quality",
                    "/api/v1/documents/quality/batch",
                    "/api/v1/documents/quality/statistics",
                    "/api/v1/quality/continuous-learning"
                ],
                "description": "Automated quality assessment and continuous learning"
            },
            "analytics_dashboard": {
                "endpoints": [
                    "/api/v1/analytics/user/{user_id}/dashboard",
                    "/api/v1/analytics/system/overview",
                    "/api/v1/analytics/events",
                    "/api/v1/analytics/metrics/summary"
                ],
                "description": "Comprehensive analytics and user behavior tracking"
            },
            "knowledge_base_management": {
                "endpoints": [
                    "/api/v1/knowledge-base/status",
                    "/api/v1/knowledge-base/documents",
                    "/api/v1/knowledge-base/maintenance/manual",
                    "/api/v1/knowledge-base/coverage"
                ],
                "description": "Knowledge base administration and maintenance"
            },
            "payment_system": {
                "endpoints": [
                    "/api/v1/customers",
                    "/api/v1/customers/me",
                    "/api/v1/payments/intents",
                    "/api/v1/payments",
                    "/api/v1/subscriptions",
                    "/api/v1/subscriptions/{id}",
                    "/api/v1/portal-session",
                    "/api/v1/billing-overview",
                    "/api/v1/stats",
                    "/api/v1/products",
                    "/api/v1/prices",
                    "/api/v1/webhooks/stripe"
                ],
                "description": "Complete Stripe payment and subscription management"
            }
        },
        "api_version": "v1",
        "total_endpoints": 42,
        "documentation": "/docs"
    }
