# FineHero API Documentation Template

This document provides a consistent template for documenting FineHero API endpoints. All endpoints should follow this structure to ensure clarity and consistency across the API.

## Template Structure

### Endpoint Information
```python
@router.{HTTP_METHOD}({ENDPOINT_PATH}, response_model={RESPONSE_SCHEMA})
def {FUNCTION_NAME}(
    {PARAMETERS_WITH_TYPES},
    db: Session = Depends(get_db)
    # Add other dependencies like authentication below
):
    """
    {ENDPOINT_TITLE}
    
    {DETAILED_DESCRIPTION}
    
    ### Parameters
    {PARAMETER_DOCUMENTATION}
    
    ### Request Body (if applicable)
    {REQUEST_BODY_DOCUMENTATION}
    
    ### Response
    {RESPONSE_DOCUMENTATION}
    
    ### Status Codes
    {STATUS_CODE_DOCUMENTATION}
    
    ### Example Request
    ```python
    {EXAMPLE_REQUEST}
    ```
    
    ### Example Response
    ```json
    {EXAMPLE_RESPONSE}
    ```
    
    ### Error Responses
    {ERROR_RESPONSE_DOCUMENTATION}
    
    ### Notes
    {ADDITIONAL_NOTES}
    """
```

## Required Documentation Elements

### 1. Endpoint Title
A concise summary of what the endpoint does (verb + resource).

**Example:**
```
Create a defense for a specific traffic fine
```

### 2. Detailed Description
A more comprehensive explanation of the endpoint's functionality, business context, and any special considerations.

**Example:**
```
This endpoint generates an AI-powered defense letter for a traffic fine based on the fine's details. 
The system uses advanced legal knowledge and templates to create personalized defense letters.
The defense generation uses the Gemini API when available, with automatic fallback to templates.
```

### 3. Parameters Documentation
Document all path parameters, query parameters, and body parameters with their types, descriptions, and validation rules.

**Example:**
```
### Parameters
- **fine_id** (path parameter, integer, required): The ID of the fine to generate a defense for
- **generation_style** (query parameter, string, optional): Style of defense to generate (formal, casual, legal_technical). Default: formal
- **include_precedent** (query parameter, boolean, optional): Whether to include relevant case precedents. Default: true
```

### 4. Request Body Documentation
If the endpoint accepts a request body, document its structure, required fields, and validation rules.

**Example:**
```
### Request Body
```json
{
  "email": "user@example.com",
  "subscription_tier": "premium",
  "trial_days": 14
}
```
- **email** (string, required): Customer's email address
- **subscription_tier** (string, required): Subscription tier (free, basic, premium)
- **trial_days** (integer, optional): Number of days for the trial period (0-30)
```

### 5. Response Documentation
Document the response structure, including both success and error responses.

**Example:**
```
### Response
Returns a JSON object containing:
- **content** (string): The generated defense text
- **fine_id** (integer): ID of the associated fine
- **generation_metadata** (object): Information about the generation process
  - **generation_time** (float): Time taken to generate in seconds
  - **ai_used** (boolean): Whether AI was used in generation
  - **template_used** (string): ID of the template used (if applicable)
  - **quality_score** (float): Quality score of the generated defense (0-1)
```

### 6. Status Code Documentation
Document all possible status codes the endpoint can return.

**Example:**
```
### Status Codes
- **200 OK**: Defense successfully generated
- **404 Not Found**: Fine not found
- **422 Unprocessable Entity**: Invalid fine data or parameters
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error during generation
```

### 7. Example Request
Provide a concrete example of how to call the endpoint.

**Example:**
```
### Example Request
```python
import requests

response = requests.post(
    "https://api.finehero.pt/api/v1/fines/123/defenses",
    headers={
        "Authorization": "Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "generation_style": "formal",
        "include_precedent": True
    }
)
```
```

### 8. Example Response
Provide a concrete example of the endpoint's response.

**Example:**
```
### Example Response
```json
{
  "content": "Exmo. Senhor Presidente da Autoridade Nacional de Segurança Rodoviária,\n\n...",
  "fine_id": 123,
  "generation_metadata": {
    "generation_time": 2.34,
    "ai_used": true,
    "template_used": "defense_template_01",
    "quality_score": 0.87
  }
}
```
```

### 9. Error Response Documentation
Document the possible error responses, including the structure and error codes.

**Example:**
```
### Error Responses
- **404 Not Found**
  ```json
  {
    "error": {
      "type": "not_found_error",
      "code": "FINEHERO_404",
      "detail": "Fine with ID 123 not found",
      "timestamp": "2025-11-12T21:24:00.000Z",
      "path": "/api/v1/fines/123/defenses",
      "data": {
        "resource_type": "fine",
        "resource_id": "123"
      }
    }
  }
  ```
- **422 Unprocessable Entity**
  ```json
  {
    "error": {
      "type": "validation_error",
      "code": "FINEHERO_422",
      "detail": "Request validation failed",
      "timestamp": "2025-11-12T21:24:00.000Z",
      "path": "/api/v1/fines/123/defenses",
      "data": {
        "field_errors": {
          "generation_style": "Invalid value: must be one of formal, casual, legal_technical"
        }
      }
    }
  }
  ```
```

### 10. Additional Notes
Include any additional information, special considerations, rate limits, pagination, authentication requirements, etc.

**Example:**
```
### Notes
- Requires valid authentication token in the Authorization header
- Rate limit: 10 requests per minute per user
- This endpoint may take 1-5 seconds to complete depending on the complexity of the defense
- The response includes quality scoring to assess the generated defense's strength
```

## Endpoint Categories

### Authentication
Endpoints for user authentication and management.

### User Management
Endpoints for managing user information and preferences.

### Fine Management
Endpoints for creating, reading, and managing traffic fines.

### Defense Generation
Endpoints for generating legal defenses for traffic fines.

### Payment Processing
Endpoints for payment processing and subscription management.

### RAG Search
Endpoints for searching the legal knowledge base.

### Analytics
Endpoints for retrieving analytics and metrics.

### Knowledge Base
Endpoints for managing the legal knowledge base.

## Schema Documentation Format

Schemas should be documented with:
1. Schema name and purpose
2. Field descriptions
3. Field types and constraints
4. Required vs. optional fields
5. Default values
6. Example schema instance

### Example Schema Documentation

```python
class StripeCustomerCreate(BaseModel):
    """Schema for creating a Stripe customer."""
    email: str = Field(..., description="Customer email address", examples=["customer@example.com"])
    name: Optional[str] = Field(None, description="Customer full name")
    description: Optional[str] = Field(None, description="Customer description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "email": "customer@example.com",
                "name": "João Silva",
                "description": "Premium customer",
                "metadata": {
                    "tier": "premium",
                    "source": "website"
                }
            }
        }
```

## Error Documentation

Error responses should be documented with:
1. Error type and code
2. HTTP status code
3. Description of the error
4. Example error response
5. Possible causes and solutions

### Example Error Documentation

```
### AuthenticationError (401)
**Description:** The request requires authentication. The response includes details about what went wrong.

**Example Response:**
```json
{
  "error": {
    "type": "auth_error",
    "code": "FINEHERO_401",
    "detail": "Authentication credentials are invalid or missing",
    "timestamp": "2025-11-12T21:24:00.000Z",
    "path": "/api/v1/payments"
  }
}
```

**Possible Causes:**
- Missing or invalid Authorization header
- Expired token
- User account disabled

**Solution:**
Re-authenticate with valid credentials.