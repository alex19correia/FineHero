# API Documentation Template - FineHero/Multas AI

## Overview
This document provides comprehensive API documentation for the FineHero/Multas AI REST API, including endpoint specifications, request/response formats, authentication requirements, and integration examples.

## Document Information
- **Last Updated**: 2025-11-11
- **API Version**: v1.0
- **Base URL**: `https://api.finehero.ai/v1`
- **Maintained By**: Development Team
- **Review Cycle**: Monthly

## Table of Contents
1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
5. [Integration Examples](#integration-examples)
6. [SDKs and Libraries](#sdks-and-libraries)

## Authentication

### API Key Authentication
All API requests require authentication using an API key in the request header.

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

> **Note**: API keys should be kept secure and never exposed in client-side code.

### Getting API Keys
1. Register an account at [finehero.ai](https://finehero.ai)
2. Navigate to Dashboard → API Keys
3. Generate a new API key with required permissions
4. Store the key securely (environment variables recommended)

## Rate Limiting

### Rate Limits
- **Default Tier**: 100 requests per minute
- **Premium Tier**: 1000 requests per minute
- **Enterprise Tier**: Custom limits available

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699712000
```

## Error Handling

### HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Rate Limit Exceeded
- **500**: Internal Server Error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "request_id": "req_123456789"
  }
}
```

## Endpoints

### 1. Fines Management

#### POST /fines
Process and analyze a traffic fine PDF.

**Request:**
```json
{
  "pdf_content": "base64_encoded_pdf",
  "user_id": "user_123456",
  "options": {
    "extract_all_fields": true,
    "confidence_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "fine_id": "fine_789012",
  "extracted_data": {
    "date": "2025-10-15",
    "location": "Lisbon, Portugal",
    "amount": 120.00,
    "infraction_code": "A123",
    "description": "Speeding in urban area"
  },
  "confidence_scores": {
    "date": 0.95,
    "location": 0.87,
    "amount": 0.99
  },
  "processing_time": 2.3
}
```

**Status Codes:**
- 201: Fine processed successfully
- 400: Invalid PDF format or missing data
- 422: Validation errors in extracted data
- 429: Rate limit exceeded

#### GET /fines/{fine_id}
Retrieve fine details and processing results.

**Response:**
```json
{
  "fine_id": "fine_789012",
  "status": "processed",
  "extracted_data": { /* same as above */ },
  "defenses": [
    {
      "defense_id": "def_456789",
      "type": "administrative",
      "status": "generated",
      "created_at": "2025-11-11T15:00:00Z"
    }
  ],
  "created_at": "2025-11-11T14:58:00Z",
  "updated_at": "2025-11-11T15:00:00Z"
}
```

### 2. Defense Generation

#### POST /defenses
Generate administrative defense for a processed fine.

**Request:**
```json
{
  "fine_id": "fine_789012",
  "defense_type": "administrative",
  "options": {
    "template": "standard",
    "include_precedents": true,
    "jurisdiction": "portugal"
  },
  "user_context": {
    "previous_offenses": false,
    "circumstances": "emergency_medical"
  }
}
```

**Response:**
```json
{
  "defense_id": "def_456789",
  "status": "generated",
  "defense_content": {
    "formatted_letter": "base64_encoded_pdf",
    "text_content": "Defense letter text...",
    "word_count": 423
  },
  "legal_citations": [
    {
      "law": "Road Traffic Code",
      "article": "Article 135",
      "relevance_score": 0.92
    }
  ],
  "success_probability": 0.75,
  "processing_time": 4.2
}
```

### 3. Knowledge Base

#### GET /knowledge/cases
Search for relevant legal precedents and cases.

**Query Parameters:**
- `query`: Search query string
- `jurisdiction`: Country/region filter
- `case_type`: Type of legal case
- `limit`: Number of results (max 50)

**Response:**
```json
{
  "results": [
    {
      "case_id": "case_123456",
      "title": "Administrative Defense - Speeding",
      "summary": "Successful defense based on emergency circumstances",
      "jurisdiction": "Portugal",
      "outcome": "defense_granted",
      "relevance_score": 0.89,
      "legal_citations": ["Article 135", "Constitution Article 27"]
    }
  ],
  "total_results": 1,
  "search_time": 0.15
}
```

### 4. User Management

#### GET /users/{user_id}/history
Retrieve user's fine and defense history.

**Response:**
```json
{
  "user_id": "user_123456",
  "fines": [
    {
      "fine_id": "fine_789012",
      "status": "processed",
      "processed_at": "2025-11-11T15:00:00Z",
      "defense_status": "generated"
    }
  ],
  "defenses": [
    {
      "defense_id": "def_456789",
      "fine_id": "fine_789012",
      "type": "administrative",
      "created_at": "2025-11-11T15:00:00Z",
      "outcome": "pending_submission"
    }
  ],
  "statistics": {
    "total_fines": 1,
    "successful_defenses": 0,
    "total_saved": 0.0
  }
}
```

## Integration Examples

### Python Integration
```python
import requests
import base64

class FineHeroAPI:
    def __init__(self, api_key):
        self.base_url = "https://api.finehero.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def process_fine(self, pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_content = base64.b64encode(f.read()).decode()
        
        payload = {
            "pdf_content": pdf_content,
            "options": {"extract_all_fields": True}
        }
        
        response = requests.post(
            f"{self.base_url}/fines",
            json=payload,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"API Error: {response.json()}")

# Usage
api = FineHeroAPI("your_api_key_here")
result = api.process_fine("fine_document.pdf")
print(f"Fine ID: {result['fine_id']}")
```

### JavaScript Integration
```javascript
class FineHeroAPI {
    constructor(apiKey) {
        this.baseUrl = 'https://api.finehero.ai/v1';
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async processFine(pdfFile) {
        const formData = new FormData();
        formData.append('pdf', pdfFile);
        
        const response = await fetch(`${this.baseUrl}/fines/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error.message);
        }
        
        return await response.json();
    }
}

// Usage
const api = new FineHeroAPI('your_api_key_here');
const result = await api.processFine(pdfFile);
console.log(`Fine ID: ${result.fine_id}`);
```

## SDKs and Libraries

### Official SDKs
- **Python**: `pip install finehero-api`
- **JavaScript**: `npm install finehero-api`
- **PHP**: `composer require finehero/api-client`

### Community Libraries
- [Ruby Gem](https://github.com/finehero/ruby-client) (Community-maintained)
- [Go Package](https://github.com/finehero/go-client) (Community-maintained)

## Webhooks

### Setting Up Webhooks
To receive real-time updates about fine processing status:

1. Register webhook endpoint in your account dashboard
2. Verify webhook signatures using your webhook secret
3. Handle events: `fine.processed`, `defense.generated`, `user.activity`

### Webhook Payload Example
```json
{
  "event": "fine.processed",
  "timestamp": "2025-11-11T15:00:00Z",
  "data": {
    "fine_id": "fine_789012",
    "user_id": "user_123456",
    "status": "processed",
    "processing_time": 2.3
  }
}
```

## Support and Resources

- **Documentation**: [https://docs.finehero.ai](https://docs.finehero.ai)
- **API Status**: [https://status.finehero.ai](https://status.finehero.ai)
- **Support**: [support@finehero.ai](mailto:support@finehero.ai)
- **Community Forum**: [https://community.finehero.ai](https://community.finehero.ai)

## Revision History
| Date | Version | Changes |
|------|---------|---------|
| 2025-11-11 | 1.0 | Initial API documentation |