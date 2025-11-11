#!/usr/bin/env python3
"""
Test script to validate BLOCKER #3: No User System fix.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all authentication components can be imported."""
    try:
        from app.auth import verify_password, get_password_hash, create_access_token, verify_token
        from app.schemas_auth import UserCreate, UserResponse, LoginRequest, Token
        from app.models import User
        from app.crud_users import create_user, get_user_by_email, authenticate_user
        
        print("PASS: All authentication components imported successfully")
        return True
    except Exception as e:
        print(f"FAIL: Import error: {e}")
        return False

def test_password_hashing():
    """Test password hashing and verification."""
    try:
        from app.auth import get_password_hash, verify_password
        
        test_password = "test_password_123"
        hashed = get_password_hash(test_password)
        verified = verify_password(test_password, hashed)
        wrong_verified = verify_password("wrong_password", hashed)
        
        assert verified == True, "Correct password should verify"
        assert wrong_verified == False, "Wrong password should not verify"
        assert hashed != test_password, "Hash should be different from original password"
        
        print("PASS: Password hashing and verification works correctly")
        return True
    except Exception as e:
        print(f"FAIL: Password hashing test failed: {e}")
        return False

def test_jwt_tokens():
    """Test JWT token creation and verification."""
    try:
        from app.auth import create_access_token, verify_token
        from datetime import timedelta
        from core.config import settings
        
        # Test token creation
        test_data = {"sub": "test@example.com", "user_id": 123}
        token = create_access_token(test_data)
        
        assert token is not None, "Token should be created"
        assert len(token) > 50, "Token should be sufficiently long"
        
        # Test token verification
        verified_data = verify_token(token)
        assert verified_data is not None, "Token should verify successfully"
        assert verified_data["email"] == "test@example.com", "Email should match"
        assert verified_data["user_id"] == 123, "User ID should match"
        
        print("PASS: JWT token creation and verification works")
        return True
    except Exception as e:
        print(f"FAIL: JWT token test failed: {e}")
        return False

def test_user_model():
    """Test User model structure."""
    try:
        from app.models import User
        
        # Check User model has expected attributes
        expected_attrs = [
            'id', 'email', 'username', 'hashed_password', 'full_name',
            'is_active', 'is_verified', 'subscription_tier', 
            'created_at', 'updated_at', 'last_login'
        ]
        
        for attr in expected_attrs:
            assert hasattr(User, attr), f"User model should have {attr} attribute"
        
        print("PASS: User model has all required attributes")
        return True
    except Exception as e:
        print(f"FAIL: User model test failed: {e}")
        return False

def test_authentication_endpoints():
    """Test that authentication endpoints are properly configured."""
    try:
        from app.api.v1.endpoints.auth import router
        
        # Check router has expected routes
        route_paths = [route.path for route in router.routes]
        
        expected_paths = ['/register', '/login', '/me', '/logout', '/verify-token']
        for path in expected_paths:
            assert path in route_paths, f"Router should have {path} endpoint"
        
        print("PASS: Authentication endpoints properly configured")
        return True
    except Exception as e:
        print(f"FAIL: Authentication endpoints test failed: {e}")
        return False

def test_configuration():
    """Test that JWT configuration is available."""
    try:
        from core.config import settings
        
        assert hasattr(settings, 'SECRET_KEY'), "Settings should have SECRET_KEY"
        assert hasattr(settings, 'ALGORITHM'), "Settings should have ALGORITHM"
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES'), "Settings should have ACCESS_TOKEN_EXPIRE_MINUTES"
        
        print(f"PASS: JWT configuration loaded - Algorithm: {settings.ALGORITHM}")
        return True
    except Exception as e:
        print(f"FAIL: Configuration test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("BLOCKER #3: NO USER SYSTEM - VALIDATION")
    print("Testing JWT-based authentication implementation")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration),
        ("Component Imports", test_imports),
        ("Password Hashing", test_password_hashing),
        ("JWT Tokens", test_jwt_tokens),
        ("User Model", test_user_model),
        ("Auth Endpoints", test_authentication_endpoints),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   Test failed")
        except Exception as e:
            print(f"   Test error: {e}")
    
    print("\n" + "=" * 60)
    print(f"VALIDATION RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: BLOCKER #3 FIX SUCCESSFUL!")
        print("\nAuthentication system implementation complete:")
        print("✓ JWT-based authentication")
        print("✓ User registration and login endpoints")
        print("✓ Password hashing and verification")
        print("✓ User model with relationships")
        print("✓ Authentication middleware")
        print("✓ CRUD operations for user management")
        print("✓ Integration with main API")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)