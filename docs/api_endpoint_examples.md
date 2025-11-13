# FineHero API Endpoint Documentation Examples

This document provides detailed examples of how to document FineHero API endpoints using the [API Documentation Template](api_documentation_template.md).

## Authentication Endpoints

### POST /auth/login

```python
@router.post("/auth/login", response_model=schemas.Token)
async def login_for_access_token(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and get an access token.
    
    This endpoint validates the user's credentials and returns a JWT access token that can be used to authenticate subsequent requests.
    The token has an expiration time of 30 minutes.
    
    ### Parameters
    - **email** (request body, string, required): The user's email address
    - **password** (request body, string, required): The user's password
    
    ### Request Body
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePassword123!"
    }
    ```
    - **email** (string, required): User's email address
    - **password** (string, required): User's password (minimum 8 characters)
    
    ### Response
    Returns a JSON object containing:
    - **access_token** (string): JWT access token for authenticated requests
    - **token_type** (string): Type of token (always "bearer")
    
    ### Status Codes
    - **200 OK**: Successful authentication
    - **400 Bad Request**: Invalid login request format
    - **401 Unauthorized**: Invalid credentials
    - **422 Unprocessable Entity**: Missing required fields
    
    ### Example Request
    ```python
    import requests
    
    response = requests.post(
        "https://api.finehero.pt/api/v1/auth/login",
        headers={
            "Content-Type": "application/json"
        },
        json={
            "email": "user@example.com",
            "password": "SecurePassword123!"
        }
    )
    ```
    
    ### Example Response
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    
    ### Error Responses
    - **401 Unauthorized**
      ```json
      {
        "error": {
          "type": "auth_error",
          "code": "FINEHERO_401",
          "detail": "Invalid credentials",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/auth/login"
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
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/auth/login",
          "data": {
            "field_errors": {
              "password": "Password must be at least 8 characters long"
            }
          }
        }
      }
      ```
    
    ### Notes
    - The returned token should be included in the Authorization header for all subsequent authenticated requests
    - Token format: JWT signed with HS256 algorithm
    - Token expires after 30 minutes
    - If the account has been locked due to too many failed attempts, a 429 Too Many Requests will be returned
    """
    return authenticate_user(login_data.email, login_data.password, db)
```

## Fines Management Endpoints

### POST /fines

```python
@router.post("/fines/", response_model=schemas.Fine)
def create_fine(fine: schemas.FineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new traffic fine record.
    
    This endpoint allows authenticated users to create a new traffic fine record in the system. The fine will be associated with the current user.
    
    ### Parameters
    - **date** (request body, date, optional): Date the fine was issued (format: YYYY-MM-DD)
    - **location** (request body, string, optional): Location where the fine was issued
    - **infractor** (request body, string, optional): Name of the person who received the fine
    - **fine_amount** (request body, number, optional): Amount of the fine in euros
    - **infraction_code** (request body, string, optional): Legal code of the infraction
    - **pdf_reference** (request body, string, optional): Reference number from the fine document
    
    ### Request Body
    ```json
    {
      "date": "2025-10-15",
      "location": "Avenida da Liberdade, Lisboa",
      "infractor": "João Silva",
      "fine_amount": 120.50,
      "infraction_code": "CE-ART-048-01",
      "pdf_reference": "REF-12345"
    }
    ```
    - **date** (string, optional): Date in ISO format (YYYY-MM-DD)
    - **location** (string, optional): Full address or location description
    - **infractor** (string, optional): Name of the person who received the fine
    - **fine_amount** (number, optional): Fine amount in euros (must be positive)
    - **infraction_code** (string, optional): Legal code from the fine document
    - **pdf_reference** (string, optional): Reference or document number
    
    ### Response
    Returns a JSON object containing:
    - **id** (integer): Unique identifier of the created fine
    - **date** (date): Date the fine was issued
    - **location** (string): Location where the fine was issued
    - **infractor** (string): Name of the person who received the fine
    - **fine_amount** (number): Amount of the fine in euros
    - **infraction_code** (string): Legal code of the infraction
    - **pdf_reference** (string): Reference number from the fine document
    - **user_id** (integer): ID of the user who created the fine
    
    ### Status Codes
    - **201 Created**: Fine successfully created
    - **400 Bad Request**: Invalid input data
    - **401 Unauthorized**: Invalid or missing token
    - **422 Unprocessable Entity**: Validation error
    
    ### Example Request
    ```python
    import requests
    
    response = requests.post(
        "https://api.finehero.pt/api/v1/fines",
        headers={
            "Authorization": "Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "date": "2025-10-15",
            "location": "Avenida da Liberdade, Lisboa",
            "infractor": "João Silva",
            "fine_amount": 120.50,
            "infraction_code": "CE-ART-048-01",
            "pdf_reference": "REF-12345"
        }
    )
    ```
    
    ### Example Response
    ```json
    {
      "id": 1,
      "date": "2025-10-15",
      "location": "Avenida da Liberdade, Lisboa",
      "infractor": "João Silva",
      "fine_amount": 120.50,
      "infraction_code": "CE-ART-048-01",
      "pdf_reference": "REF-12345",
      "user_id": 1
    }
    ```
    
    ### Error Responses
    - **401 Unauthorized**
      ```json
      {
        "error": {
          "type": "auth_error",
          "code": "FINEHERO_401",
          "detail": "Authentication credentials are invalid or missing",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/fines"
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
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/fines",
          "data": {
            "field_errors": {
              "fine_amount": "Must be a positive number"
            }
          }
        }
      }
      ```
    
    ### Notes
    - Requires valid authentication token in the Authorization header
    - The created fine will be associated with the authenticated user
    - At least one of the optional fields should be provided
    - This endpoint does not generate a defense; use the defense endpoints for that
    """
    return crud.create_fine(db=db, fine=fine, user_id=current_user.id)
```

## Defense Generation Endpoints

### POST /fines/{fine_id}/defenses

```python
@router.post("/fines/{fine_id}/defenses/", response_model=schemas.DefenseWithMetadata)
def create_defense_for_fine(
    fine_id: int, 
    defense_request: schemas.DefenseRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a defense for a specific traffic fine using AI.
    
    This endpoint creates an AI-powered defense letter for a traffic fine based on the fine's details. The system uses advanced legal knowledge and templates to create personalized defense letters.
    The defense generation uses the Gemini API when available, with automatic fallback to templates if the API is unavailable.
    
    ### Parameters
    - **fine_id** (path parameter, integer, required): The ID of the fine to generate a defense for
    - **generation_style** (query parameter, string, optional): Style of defense to generate (formal, casual, legal_technical). Default: formal
    - **include_precedent** (query parameter, boolean, optional): Whether to include relevant case precedents. Default: true
    - **custom_notes** (body parameter, string, optional): Additional notes or circumstances to include in the defense
    
    ### Request Body
    ```json
    {
      "generation_style": "formal",
      "include_precedent": true,
      "custom_notes": "Vehicle was parked in loading zone for less than 5 minutes while picking up a passenger with mobility issues."
    }
    ```
    - **generation_style** (string, optional): Style of defense to generate (formal, casual, legal_technical)
    - **include_precedent** (boolean, optional): Whether to include relevant case precedents
    - **custom_notes** (string, optional): Additional context or notes about the circumstances
    
    ### Response
    Returns a JSON object containing:
    - **id** (integer): Unique identifier of the generated defense
    - **fine_id** (integer): ID of the associated fine
    - **content** (string): The generated defense text
    - **generation_time** (float): Time taken to generate in seconds
    - **ai_used** (boolean): Whether AI was used in generation
    - **template_fallback** (boolean): Whether template fallback was used
    - **quality_score** (float): Quality score of the generated defense (0-1)
    
    ### Status Codes
    - **200 OK**: Defense successfully generated
    - **401 Unauthorized**: Invalid or missing token
    - **403 Forbidden**: Fine does not belong to the current user
    - **404 Not Found**: Fine not found
    - **422 Unprocessable Entity**: Invalid fine data or parameters
    - **429 Too Many Requests**: Rate limit exceeded
    - **500 Internal Server Error**: Server error during generation
    
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
            "include_precedent": True,
            "custom_notes": "Vehicle was parked in loading zone for less than 5 minutes while picking up a passenger with mobility issues."
        }
    )
    ```
    
    ### Example Response
    ```json
    {
      "id": 1,
      "fine_id": 123,
      "content": "Exmo. Senhor Presidente da Autoridade Nacional de Segurança Rodoviária,\n\nEu, João Silva, venho por este meio...",
      "generation_time": 2.34,
      "ai_used": true,
      "template_fallback": false,
      "quality_score": 0.87
    }
    ```
    
    ### Error Responses
    - **403 Forbidden**
      ```json
      {
        "error": {
          "type": "permission_error",
          "code": "FINEHERO_403",
          "detail": "You do not have permission to generate a defense for this fine",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/fines/123/defenses"
        }
      }
      ```
    - **404 Not Found**
      ```json
      {
        "error": {
          "type": "not_found_error",
          "code": "FINEHERO_404",
          "detail": "Fine with ID 123 not found",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/fines/123/defenses",
          "data": {
            "resource_type": "fine",
            "resource_id": "123"
          }
        }
      }
      ```
    - **429 Too Many Requests**
      ```json
      {
        "error": {
          "type": "rate_limit_error",
          "code": "FINEHERO_429",
          "detail": "Too many defense generation requests. Please try again later.",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/fines/123/defenses",
          "data": {
            "retry_after": 60
          }
        }
      }
      ```
    
    ### Notes
    - Requires valid authentication token in the Authorization header
    - Rate limit: 10 requests per minute per user
    - This endpoint may take 1-5 seconds to complete depending on the complexity of the defense
    - The response includes quality scoring to assess the generated defense's strength
    - Defenses are generated based on the fine's location, date, infraction code, and other details
    - Custom notes provide additional context that can strengthen the defense
    """
    try:
        # Get the fine data
        fine = crud.get_fine(db, fine_id=fine_id)
        if not fine:
            raise HTTPException(status_code=404, detail="Fine not found")
        
        # Check if fine belongs to current user
        if fine.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to generate a defense for this fine")
        
        # Create Fine object for defense generator
        fine_data = schemas.Fine(
            id=fine.id,
            date=fine.date,
            location=fine.location,
            infraction_code=fine.infraction_code,
            fine_amount=fine.fine_amount,
            infractor=fine.infractor
        )
        
        # Generate defense using AI
        generator = DefenseGenerator(fine_data)
        
        # Measure generation time
        start_time = time.time()
        
        # Generate the defense
        defense_content = generator.generate()
        
        generation_time = time.time() - start_time
        
        # Create defense record
        defense_create = schemas.DefenseCreate(
            defense_text=defense_content,
            success_probability=0.75  # Default, could be enhanced with ML model
        )
        
        defense = crud.create_fine_defense(db=db, defense=defense_create, fine_id=fine_id)
        
        # Return enhanced response with metadata
        return {
            **defense.__dict__,
            "generation_time": round(generation_time, 2),
            "ai_used": generator.gemini_available,
            "template_fallback": not generator.gemini_available
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}") from e
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Service configuration error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Defense generation failed: {str(e)}") from e
```

## RAG Search Endpoints

### POST /rag/search

```python
@router.post("/rag/search", response_model=List[Dict[str, Any]])
def search_legal_documents(
    query: str,
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    jurisdictions: Optional[List[str]] = Query(None, description="Filter by jurisdictions"),
    case_outcomes: Optional[List[str]] = Query(None, description="Filter by case outcomes"),
    min_quality_score: float = Query(0.0, description="Minimum quality score (0-1)"),
    max_results: int = Query(5, description="Maximum number of results", ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search legal documents using advanced RAG system with semantic and keyword search.
    
    This endpoint provides advanced search capabilities for the legal knowledge base, combining semantic similarity search with keyword-based filtering and metadata-based relevance scoring.
    
    ### Parameters
    - **query** (query parameter, string, required): Search query string
    - **document_types** (query parameter, array of strings, optional): Filter by document types (law, precedent, regulation, commentary)
    - **jurisdictions** (query parameter, array of strings, optional): Filter by jurisdictions (Portugal, Lisbon, Porto)
    - **case_outcomes** (query parameter, array of strings, optional): Filter by case outcomes (successful, partially_successful, unsuccessful)
    - **min_quality_score** (query parameter, number, optional): Minimum quality score (0-1). Default: 0.0
    - **max_results** (query parameter, integer, optional): Maximum number of results. Default: 5, Range: 1-20
    
    ### Request Body
    ```json
    {
      "query": "estacionamento proibido zona carga descarga",
      "document_types": ["law", "precedent"],
      "jurisdictions": ["Portugal", "Lisbon"],
      "min_quality_score": 0.7,
      "max_results": 10
    }
    ```
    - **query** (string, required): Search query string
    - **document_types** (array of strings, optional): Filter by document types
    - **jurisdictions** (array of strings, optional): Filter by jurisdictions
    - **case_outcomes** (array of strings, optional): Filter by case outcomes
    - **min_quality_score** (number, optional): Minimum quality score (0-1)
    - **max_results** (integer, optional): Maximum number of results
    
    ### Response
    Returns a list of JSON objects, each containing:
    - **content** (string): Excerpt of the legal document
    - **document_id** (integer): ID of the document in the knowledge base
    - **title** (string): Title of the document
    - **source** (string): Source URL of the document
    - **document_type** (string): Type of document (law, precedent, etc.)
    - **jurisdiction** (string): Jurisdiction of the document
    - **publication_date** (string): Publication date in ISO format
    - **relevance_score** (float): Overall relevance score (0-1)
    - **semantic_score** (float): Semantic similarity score (0-1)
    - **keyword_score** (float): Keyword match score (0-1)
    - **metadata_bonus** (float): Metadata relevance bonus (0-1)
    - **quality_score** (float): Document quality score (0-1)
    
    ### Status Codes
    - **200 OK**: Search successful
    - **400 Bad Request**: Invalid search parameters
    - **401 Unauthorized**: Invalid or missing token
    - **422 Unprocessable Entity**: Invalid query parameters
    - **500 Internal Server Error**: Server error during search
    
    ### Example Request
    ```python
    import requests
    
    response = requests.post(
        "https://api.finehero.pt/api/v1/rag/search",
        headers={
            "Authorization": "Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": "estacionamento proibido zona carga descarga",
            "document_types": ["law", "precedent"],
            "jurisdictions": ["Portugal", "Lisbon"],
            "min_quality_score": 0.7,
            "max_results": 10
        }
    )
    ```
    
    ### Example Response
    ```json
    [
      {
        "content": "Art. 48º do Código da Estrada - Estacionamento...",
        "document_id": 1,
        "title": "Código da Estrada - Estacionamento",
        "source": "https://dre.pt/...",
        "document_type": "law",
        "jurisdiction": "Portugal",
        "publication_date": "2023-06-15T00:00:00",
        "relevance_score": 0.95,
        "semantic_score": 0.92,
        "keyword_score": 0.98,
        "metadata_bonus": 0.05,
        "quality_score": 0.91
      },
      {
        "content": "Decreto-Lei nº 44/2006 - Estacionamento...",
        "document_id": 2,
        "title": "Regulamento de Estacionamento de Lisboa",
        "source": "https://cmlisboa.pt/...",
        "document_type": "regulation",
        "jurisdiction": "Lisbon",
        "publication_date": "2023-05-20T00:00:00",
        "relevance_score": 0.87,
        "semantic_score": 0.85,
        "keyword_score": 0.92,
        "metadata_bonus": 0.03,
        "quality_score": 0.88
      }
    ]
    ```
    
    ### Error Responses
    - **400 Bad Request**
      ```json
      {
        "error": {
          "type": "validation_error",
          "code": "FINEHERO_400",
          "detail": "Invalid search parameters",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/rag/search",
          "data": {
            "field_errors": {
              "min_quality_score": "Must be between 0.0 and 1.0"
            }
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
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/rag/search",
          "data": {
            "field_errors": {
              "query": "Query string cannot be empty"
            }
          }
        }
      }
      ```
    
    ### Notes
    - Requires valid authentication token in the Authorization header
    - Rate limit: 20 requests per minute per user
    - Search uses a combination of semantic and keyword matching
    - Results are ranked by relevance score
    - Filtering parameters are optional and can be combined
    - The knowledge base is regularly updated with new legal documents
    - This endpoint is particularly useful for researching legal precedents and regulations
    """
    try:
        # Initialize RAG retriever
        retriever = AdvancedRAGRetriever()
        
        # Create query context
        context = LegalQueryContext(
            query=query,
            document_types=document_types,
            jurisdictions=jurisdictions,
            case_outcomes=case_outcomes,
            min_quality_score=min_quality_score,
            max_results=max_results
        )
        
        # Perform search
        results = retriever.retrieve_with_context(context)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "document_id": result.document_id,
                "title": result.title,
                "source": result.source,
                "document_type": result.document_type,
                "jurisdiction": result.jurisdiction,
                "publication_date": result.publication_date.isoformat() if result.publication_date else None,
                "relevance_score": result.relevance_score,
                "semantic_score": result.semantic_score,
                "keyword_score": result.keyword_score,
                "metadata_bonus": result.metadata_bonus,
                "quality_score": result.quality_score
            })
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")
```

## Payment Processing Endpoints

### POST /payments/intents

```python
@router.post("/payments/intents", response_model=schemas.PaymentIntentResponse)
def create_payment_intent(
    payment_data: schemas.PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a payment intent for processing payments.
    
    This endpoint creates a Stripe payment intent for processing payments. The payment intent is used to collect payment information from the customer and confirm the payment on the client side.
    
    ### Parameters
    - **amount** (request body, integer, required): Amount in cents
    - **currency** (request body, string, optional): Three-letter currency code (default: "eur")
    - **description** (request body, string, optional): Payment description
    - **receipt_email** (request body, string, optional): Email for receipt
    - **metadata** (request body, object, optional): Additional metadata
    
    ### Request Body
    ```json
    {
      "amount": 2500,
      "currency": "eur",
      "description": "Defense generation payment",
      "metadata": {
        "fine_id": "123",
        "service": "defense_generation"
      }
    }
    ```
    - **amount** (integer, required): Amount in cents (minimum 100)
    - **currency** (string, optional): Three-letter lowercase currency code (e.g., "eur", "usd")
    - **description** (string, optional): Description of the payment
    - **receipt_email** (string, optional): Email address to send receipt to
    - **metadata** (object, optional): Additional key-value pairs to store with the payment
    
    ### Response
    Returns a JSON object containing:
    - **id** (integer): Unique identifier of the payment intent in our system
    - **customer_id** (integer): ID of the customer
    - **stripe_payment_intent_id** (string): Stripe payment intent ID
    - **amount** (integer): Amount in cents
    - **currency** (string): Currency code
    - **description** (string): Payment description
    - **receipt_email** (string): Email for receipt
    - **status** (string): Payment status (pending, processing, succeeded, failed, canceled)
    - **client_secret** (string): Client secret for confirming payment on frontend
    - **created_at** (datetime): Creation timestamp
    - **updated_at** (datetime): Last update timestamp
    
    ### Status Codes
    - **201 Created**: Payment intent successfully created
    - **400 Bad Request**: Invalid input data
    - **401 Unauthorized**: Invalid or missing token
    - **402 Payment Required**: Payment required (user has no valid payment method)
    - **422 Unprocessable Entity**: Invalid input data
    
    ### Example Request
    ```python
    import requests
    
    response = requests.post(
        "https://api.finehero.pt/api/v1/payments/intents",
        headers={
            "Authorization": "Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "amount": 2500,
            "currency": "eur",
            "description": "Defense generation payment",
            "metadata": {
              "fine_id": "123",
              "service": "defense_generation"
            }
        }
    )
    ```
    
    ### Example Response
    ```json
    {
      "id": 1,
      "customer_id": 1,
      "stripe_payment_intent_id": "pi_1234567890",
      "amount": 2500,
      "currency": "eur",
      "description": "Defense generation payment",
      "receipt_email": "user@example.com",
      "status": "pending",
      "client_secret": "pi_1234567890_secret_abcd",
      "created_at": "2025-11-12T21:27:00.000Z",
      "updated_at": "2025-11-12T21:27:00.000Z"
    }
    ```
    
    ### Error Responses
    - **402 Payment Required**
      ```json
      {
        "error": {
          "type": "payment_error",
          "code": "FINEHERO_402",
          "detail": "Payment method required",
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/payments/intents",
          "data": {
            "message": "User has no valid payment method on file"
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
          "timestamp": "2025-11-12T21:27:00.000Z",
          "path": "/api/v1/payments/intents",
          "data": {
            "field_errors": {
              "amount": "Must be at least 100 cents"
            }
          }
        }
      }
      ```
    
    ### Notes
    - Requires valid authentication token in the Authorization header
    - The client_secret should be used on the frontend to confirm the payment
    - Payment intents expire after 1 hour if not confirmed
    - This endpoint requires the user to have a Stripe customer profile
    - The status will initially be "pending" and will be updated via webhooks when the payment is processed
    - For security reasons, the actual Stripe API key is never exposed to the client
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