#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Middleware.

This module handles all the auth stuff - JWT verification, user extraction,
and the special "dev mode" for running without Supabase.

How it works:
    1. For production: We verify Supabase JWTs using either ES256 (JWKS) or HS256
    2. For local dev: If AUTH_DISABLED=true, we skip all that and return a mock user

The key dependencies you'll use in your routes:
    - get_current_user: REQUIRES authentication (401 if not logged in)
    - get_optional_user: Works for both logged-in and anonymous users
    - require_role("admin"): Requires a specific role

Contributor: Vedant Singh Rajput <teleported0722@gmail.com>
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from typing import Optional
from dataclasses import dataclass

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
# auto_error=False means we handle missing tokens ourselves (for optional auth routes)
security = HTTPBearer(auto_error=False)

# Cache JWKS for 15 minutes to avoid hitting Supabase on every request.
# This is important because JWKS fetching involves a network call, and we don't
# want to do that on every single API request!
_jwks_cache: TTLCache = TTLCache(maxsize=1, ttl=900)


def _get_jwks_cached(supabase_url: str) -> dict:
    """Fetch JWKS from Supabase with caching."""
    import requests
    
    cache_key = "jwks"
    if cache_key in _jwks_cache:
        return _jwks_cache[cache_key]
    
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        jwks = resp.json()
        _jwks_cache[cache_key] = jwks
        logger.info("JWKS fetched and cached")
        return jwks
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signing keys")


@dataclass
class AuthenticatedUser:
    """
    Represents a logged-in user from Supabase.
    
    You'll get this from get_current_user() when the user provides a valid JWT.
    The id is the Supabase user UUID, email is from their profile.
    """
    id: str
    email: Optional[str]
    role: str
    
    @property
    def is_authenticated(self) -> bool:
        return True


@dataclass  
class AnonymousUser:
    """
    Represents someone who isn't logged in.
    
    You'll get this from get_optional_user() when no token is provided.
    Useful for routes that work for both logged-in and anonymous users.
    """
    id: None = None
    email: None = None
    role: str = "anon"
    
    @property
    def is_authenticated(self) -> bool:
        return False


@dataclass
class LocalDevUser:
    """
    A mock user for local development when auth is disabled.
    
    When you set AUTH_DISABLED=true, all auth dependencies return this user
    instead of requiring a real Supabase JWT. This lets you run the app
    locally without any cloud setup!
    
    The id "local-dev-user" is never a real Supabase UUID, so it's easy
    to spot in logs if something weird is happening.
    """
    id: str = "local-dev-user"
    email: str = "dev@localhost"
    role: str = "authenticated"
    
    @property
    def is_authenticated(self) -> bool:
        return True


def verify_jwt(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.
    
    Supabase uses ES256 (ECDSA) for JWT signing. We fetch the public keys
    from their JWKS endpoint to verify tokens (with caching).
    
    Args:
        token: JWT access token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    from jose import jwk
    
    try:
        # Get the unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg", "unknown")
        kid = unverified_header.get("kid")
        
        logger.debug(f"Token algorithm: {token_alg}, kid: {kid}")
        
        # For ES256 tokens, fetch JWKS from Supabase (cached)
        if token_alg == "ES256":
            from app.supabase import get_supabase_url
            jwks = _get_jwks_cached(get_supabase_url())
            
            # Find the key matching the kid
            ec_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    ec_key = key
                    break
            
            if not ec_key:
                logger.warning(f"No matching key found for kid: {kid}")
                raise HTTPException(status_code=401, detail="Invalid token signing key")
            
            # Convert JWK to PEM format for jose
            public_key = jwk.construct(ec_key)
            
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                options={"verify_aud": False}
            )
            return payload
        
        # Fallback to HS256 for older tokens
        else:
            from app.supabase import get_jwt_secret
            payload = jwt.decode(
                token,
                get_jwt_secret(),
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            return payload
            
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser | LocalDevUser:
    """
    Dependency to extract and verify the current user.
    
    Use this for routes that REQUIRE authentication (like /jobs endpoints).
    
    How it works:
        1. If AUTH_DISABLED=true -> returns a LocalDevUser (no verification!)
        2. Otherwise -> verifies the JWT token and returns an AuthenticatedUser
        3. If no token or invalid token -> raises 401 Unauthorized
    
    Example usage:
        @router.get("/protected")
        async def my_route(user: AuthenticatedUser = Depends(get_current_user)):
            print(f"Hello, {user.email}!")
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        AuthenticatedUser with user details, or LocalDevUser in dev mode
        
    Raises:
        HTTPException: If no token or invalid token (only when auth is enabled)
    """
    # Check if we're in local dev mode - if so, skip all the JWT stuff!
    from app.config import settings
    if settings.auth_disabled:
        logger.debug("Auth disabled - returning LocalDevUser")
        return LocalDevUser()
    
    # Normal auth flow: require a valid token
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = verify_jwt(credentials.credentials)
    
    return AuthenticatedUser(
        id=payload["sub"],
        email=payload.get("email"),
        role=payload.get("role", "authenticated")
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser | AnonymousUser | LocalDevUser:
    """
    Dependency to optionally extract the current user.
    
    Use this for routes that work for BOTH authenticated and anonymous users.
    For example, the upload endpoint works anonymously but tracks ownership
    if you're logged in.
    
    How it works:
        1. If AUTH_DISABLED=true -> returns a LocalDevUser
        2. If no token provided -> returns AnonymousUser
        3. If valid token -> returns AuthenticatedUser
        4. If invalid token -> returns AnonymousUser (graceful fallback)
    
    Example usage:
        @router.post("/upload")
        async def upload(user = Depends(get_optional_user)):
            if user.is_authenticated:
                print(f"Upload by {user.email}")
            else:
                print("Anonymous upload")
    
    Args:
        credentials: Optional Bearer token
        
    Returns:
        AuthenticatedUser if valid token, AnonymousUser otherwise, LocalDevUser in dev mode
    """
    # Check if we're in local dev mode
    from app.config import settings
    if settings.auth_disabled:
        logger.debug("Auth disabled - returning LocalDevUser")
        return LocalDevUser()
    
    # No token? That's fine for optional auth routes
    if credentials is None:
        return AnonymousUser()
    
    # Try to verify the token - if it fails, treat as anonymous
    try:
        payload = verify_jwt(credentials.credentials)
        return AuthenticatedUser(
            id=payload["sub"],
            email=payload.get("email"),
            role=payload.get("role", "authenticated")
        )
    except HTTPException:
        # Token was provided but invalid - treat as anonymous rather than erroring
        return AnonymousUser()


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Usage:
        @router.get("/admin")
        async def admin_only(user: AuthenticatedUser = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)):
        if user.role != required_role and user.role != "service_role":
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required"
            )
        return user
    return role_checker
