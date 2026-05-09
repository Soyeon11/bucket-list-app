"""
Supabase client initialization and JWT authentication middleware.

The service-role client is used for backend operations that bypass RLS.
The auth middleware validates the Bearer token from incoming requests and
injects the authenticated user ID into the request state.

Supabase projects use ES256 (asymmetric) JWT signing. Tokens are verified
against the public JWKS fetched from the Supabase auth well-known endpoint.
Falls back to HS256 with the configured JWT secret for legacy compatibility.
"""

from __future__ import annotations

import base64
import json as _json
import logging
import urllib.request
from functools import lru_cache
from typing import Annotated, Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from supabase import Client, create_client

from config import Settings, get_settings

logger = logging.getLogger(__name__)

# ── Security scheme ────────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


# ── JWKS helpers ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _fetch_jwks(supabase_url: str) -> Dict[str, Any]:
    """Fetch JWKS from Supabase and return a {kid: jwk_dict} mapping. Cached."""
    url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
        keys = {k["kid"]: k for k in data.get("keys", [])}
        logger.info("Loaded %d JWKS key(s) from %s", len(keys), url)
        return keys
    except Exception as exc:
        logger.warning("Failed to fetch JWKS from %s: %s", url, exc)
        return {}


def _decode_token_header(token: str) -> Dict[str, Any]:
    """Decode the JWT header segment without verification."""
    header_segment = token.split(".")[0]
    padding = (4 - len(header_segment) % 4) % 4
    decoded = base64.b64decode(header_segment + "=" * padding)
    return _json.loads(decoded)


# ── Supabase client factory ────────────────────────────────────────────────────

def get_supabase_client(settings: Annotated[Settings, Depends(get_settings)]) -> Client:
    """
    Dependency: returns a Supabase service-role client.
    The service-role key bypasses RLS — use only for trusted backend operations.
    """
    return create_client(settings.supabase_url, settings.supabase_service_key)


# ── JWT authentication dependency ──────────────────────────────────────────────

async def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UUID:
    """
    Dependency: validates the Supabase JWT and returns the authenticated user UUID.

    Supports ES256 (via JWKS) and HS256 (via jwt_secret) automatically,
    determined by the alg/kid fields in the token header.

    Raises:
        401 UNAUTHORIZED — token missing, expired, or invalid signature.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authorization header is missing or malformed.",
                    "details": None,
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        header = _decode_token_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")

        if alg != "HS256" and kid:
            # Asymmetric token — verify with JWKS public key
            jwks = _fetch_jwks(settings.supabase_url)
            if kid not in jwks:
                raise JWTError(f"Unknown kid '{kid}' — not in JWKS")
            key = jwks[kid]
        else:
            # Legacy symmetric token — verify with JWT secret
            key = settings.supabase_jwt_secret
            alg = "HS256"

        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            options={"verify_aud": False},
        )
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise JWTError("Missing 'sub' claim")

        return UUID(user_id_str)

    except (JWTError, ValueError) as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Token is invalid or has expired.",
                    "details": None,
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Type aliases for dependency injection ──────────────────────────────────────
CurrentUserID = Annotated[UUID, Depends(get_current_user_id)]
SupabaseClient = Annotated[Client, Depends(get_supabase_client)]
