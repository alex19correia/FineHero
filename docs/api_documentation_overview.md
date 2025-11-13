# FineHero API Documentation Overview

## Introduction

The FineHero API is a RESTful service built with FastAPI that provides access to traffic fine defense generation services. The API is organized into several functional areas, each with its own set of endpoints.

## Base URL

- **Production**: `https://api.finehero.pt/api/v1`
- **Development**: `http://localhost:8000/api/v1`

## Authentication

The FineHero API uses JWT-based authentication. To use authenticated endpoints:

1. Register or login to get an access token:
   ```http
   POST /api/v1/auth/login
   Content-Type: application/json
   
   {
     "email": "user@example.com",
     "password": "securepassword"
   }
   ```

2. Use the token in the Authorization header:
   ```http
   Authorization: Bearer {token}
   ```

## Response Format

All responses follow a standard format with optional data payload and/or an error object.

### Success Response

```json
{
  "data": {
    // Response data
  }
}
```

### Error Response

```json
{
  "error": {
    "type": "error_type",
    "code": "ERROR_CODE",
    "detail": "Detailed error message",
    "timestamp": "2025-11-12T21:24:00.000Z",
    "path": "/api/v1/endpoint/path",
    "data": {
      // Additional error data
    }
  }
}
```

## Rate Limiting

- Unauthenticated requests: 10 requests per minute
- Authenticated requests: 100 requests per minute
- Rate limit exceeded: 429 Too Many Requests

## Pagination

For endpoints that return lists, use query parameters for pagination:

- `skip` (integer, default: 0): Number of items to skip
- `limit` (integer, default: 100, max: 1000): Number of items to return

## API Endpoints Overview

The FineHero API includes the following main endpoint groups:

### Authentication
Endpoints for user authentication and management.

### Fines Management
Endpoints for creating, reading, and managing traffic fines.

### Defense Generation
Endpoints for generating legal defenses for traffic fines.

### RAG Search
Endpoints for searching the legal knowledge base.

### Payment Processing
Endpoints for payment processing and subscription management.

### Analytics
Endpoints for retrieving analytics and metrics.

## Error Types

The FineHero API uses standardized error types:

- **auth_error**: Authentication failed
- **permission_error**: Not authorized to access resource
- **validation_error**: Request validation failed
- **not_found_error**: Resource not found
- **conflict_error**: Resource conflict (e.g., already exists)
- **rate_limit_error**: Rate limit exceeded
- **payment_error**: Payment processing error
- **service_error**: Service unavailable
- **server_error**: General server error

## API Documentation Standards

The FineHero API follows a consistent documentation structure:

- Each endpoint is documented with a clear summary and detailed description
- Parameters are documented with types, descriptions, and validation rules
- Request bodies include schema definitions with examples
- Responses include detailed examples of successful and error responses
- Status codes are clearly documented with explanations
- Authentication requirements are specified for each endpoint
- Rate limits and special considerations are noted

## SDKs and Client Libraries

Official client libraries are available for:

- **JavaScript/TypeScript**: `@finehero/api-client`
- **Python**: `finehero-api-client`
- **PHP**: `finehero/php-client`

## Support

For API support, contact api-support@finehero.pt or visit our [developer portal](https://developers.finehero.pt).