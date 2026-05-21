"""JWT validation dependency for FastAPI routes.

Validates the same HMAC-signed tokens that the Authentication service issues.
The shared secret is Base64-decoded before signing in the Java side (jjwt's
`Decoders.BASE64.decode`) so we mirror that exactly here.
"""

import base64
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

log = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def _decoded_secret() -> bytes:
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET is not configured. Set it in ai-core-service/.env "
            "to the same value used by the Authentication service."
        )
    # jjwt's `Decoders.BASE64.decode` treats the configured value as Base64.
    # Mirror that so the two services produce identical signing keys.
    return base64.b64decode(settings.jwt_secret)


async def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Return the JWT subject (user id) or 401 if missing/invalid."""

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            _decoded_secret(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        log.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no subject",
        )
    return str(subject)
