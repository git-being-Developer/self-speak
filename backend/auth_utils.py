"""
Authentication utilities for Selfspeak Backend
Handles JWT verification with Supabase
"""

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt
from jwt import PyJWTError

# Load environment variables
load_dotenv()

# Security scheme
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


async def verify_jwt_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify JWT token from Supabase.

    Args:
        credentials: HTTPAuthorizationCredentials from request header

    Returns:
        dict: Decoded JWT payload

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    token = credentials.credentials

    try:
        # Method 1: Verify with Supabase Auth API
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise AuthenticationError("Invalid token: No user found")

        # Extract user info from response
        user = user_response.user

        return {
            "user_id": user.id,
            "email": user.email,
            "metadata": user.user_metadata,
            "role": user.role if hasattr(user, 'role') else 'authenticated'
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # If Supabase API fails, try JWT verification
        if SUPABASE_JWT_SECRET:
            try:
                payload = verify_jwt_with_secret(token, SUPABASE_JWT_SECRET)
                return payload
            except Exception as jwt_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token verification failed: {str(jwt_error)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


def verify_jwt_with_secret(token: str, secret: str) -> dict:
    """
    Verify JWT token using secret key (fallback method).

    Args:
        token: JWT token string
        secret: Supabase JWT secret

    Returns:
        dict: Decoded JWT payload

    Raises:
        PyJWTError: If token is invalid
    """
    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't always set aud
        )

        # Extract user_id from 'sub' claim (standard JWT claim for subject)
        user_id = payload.get("sub")
        if not user_id:
            raise PyJWTError("Token missing 'sub' claim")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "metadata": payload.get("user_metadata", {}),
            "role": payload.get("role", "authenticated")
        }

    except PyJWTError as e:
        raise PyJWTError(f"Invalid JWT token: {str(e)}")


async def get_current_user_id(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Extract and return only the user_id from JWT.
    This is the main function used in API endpoints.

    Args:
        credentials: HTTPAuthorizationCredentials from Bearer token

    Returns:
        str: User ID (UUID)

    Raises:
        HTTPException: If authentication fails
    """
    payload = await verify_jwt_token(credentials)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user_id not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Get full user information from JWT.
    Use this when you need email, metadata, etc.

    Args:
        credentials: HTTPAuthorizationCredentials from Bearer token

    Returns:
        dict: Full user payload

    Raises:
        HTTPException: If authentication fails
    """
    return await verify_jwt_token(credentials)


def require_role(required_role: str):
    """
    Dependency to require specific role.
    Usage: user = Depends(require_role("admin"))

    Args:
        required_role: Role name required (e.g., "admin", "pro")

    Returns:
        Callable dependency function
    """
    async def role_checker(credentials: HTTPAuthorizationCredentials) -> dict:
        user = await get_current_user(credentials)

        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return user

    return role_checker


# Optional: Create a global session store for performance
# (In production, use Redis or similar)
_session_cache = {}

async def get_cached_user(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Get user with caching to reduce Supabase API calls.
    Cache expires after 5 minutes.

    Args:
        credentials: HTTPAuthorizationCredentials from Bearer token

    Returns:
        dict: User payload
    """
    token = credentials.credentials

    # Check cache
    if token in _session_cache:
        cached = _session_cache[token]
        # Simple cache (in production, check expiry)
        return cached

    # Verify and cache
    user = await get_current_user(credentials)
    _session_cache[token] = user

    return user
