#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Middleware.

JWT verification and user extraction for protected routes.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from typing import Optional
from dataclasses import dataclass

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.supabase import get_jwt_secret

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Authenticated user context."""
    id: str
    email: Optional[str]
    role: str
    
    @property
    def is_authenticated(self) -> bool:
        return True


@dataclass  
class AnonymousUser:
    """Anonymous/unauthenticated user."""
    id: None = None
    email: None = None
    role: str = "anon"
    
    @property
    def is_authenticated(self) -> bool:
        return False


def verify_jwt(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.
    
    Supabase uses ES256 (ECDSA) for JWT signing. We fetch the public keys
    from their JWKS endpoint to verify tokens.
    
    Args:
        token: JWT access token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    import requests
    from jose import jwk
    from jose.utils import base64url_decode
    
    try:
        # Get the unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg", "unknown")
        kid = unverified_header.get("kid")
        
        logger.info(f"Token algorithm: {token_alg}, kid: {kid}")
        
        # For ES256 tokens, fetch JWKS from Supabase
        if token_alg == "ES256":
            from app.supabase import get_supabase_url
            jwks_url = f"{get_supabase_url()}/auth/v1/.well-known/jwks.json"
            
            try:
                resp = requests.get(jwks_url, timeout=5)
                resp.raise_for_status()
                jwks = resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch signing keys")
            
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
) -> AuthenticatedUser:
    """
    Dependency to extract and verify the current user.
    
    Use this for routes that REQUIRE authentication.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        AuthenticatedUser with user details
        
    Raises:
        HTTPException: If no token or invalid token
    """
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
) -> AuthenticatedUser | AnonymousUser:
    """
    Dependency to optionally extract the current user.
    
    Use this for routes that work for both authenticated and anonymous users.
    
    Args:
        credentials: Optional Bearer token
        
    Returns:
        AuthenticatedUser if valid token, AnonymousUser otherwise
    """
    if credentials is None:
        return AnonymousUser()
    
    try:
        payload = verify_jwt(credentials.credentials)
        return AuthenticatedUser(
            id=payload["sub"],
            email=payload.get("email"),
            role=payload.get("role", "authenticated")
        )
    except HTTPException:
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
