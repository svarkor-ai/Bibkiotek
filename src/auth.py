"""Auth module — JWT helpers, password hashing, FastAPI role dependency.

Functions:
    create_access_token(user_id, role)  → JWT string (expires 24 h)
    verify_token(token)                 → dict(user_id, role) or None
    hash_password(password)             → bcrypt hash string
    check_password(password, hash)      → bool
    require_role(allowed_roles)         → FastAPI dependency callable

Endpoints:
    POST /api/auth/login  (username, password) → {access_token, user}
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# ---------------------------------------------------------------------------
# Password hashing (bcrypt directly — avoids passlib 1.7 / bcrypt 5 compat)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a ``$2b$...`` bcrypt hash of *password*."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Return True if *password* matches *hashed*."""
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed.encode("utf-8")
    )

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(user_id: int, role: str) -> str:
    """Create a signed JWT that expires after 24 hours."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),       # subject = user id
        "role": role,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decode and verify *token*; return payload dict or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "role": payload["role"],
        }
    except JWTError:
        return None

# ---------------------------------------------------------------------------
# FastAPI dependency — role gate
# ---------------------------------------------------------------------------

_scheme = HTTPBearer(auto_error=False)


def require_role(allowed_roles: list[str]):
    """Return a FastAPI dependency that rejects requests lacking one of
    *allowed_roles* in the JWT payload.

    Usage::

        @router.get("/secret")
        def secret_view(current_user = require_role(["admin"])):
            ...
    """

    def _dep(credentials: HTTPAuthorizationCredentials = Depends(_scheme)) -> dict:
        """Inner dep — called by FastAPI for every protected route."""
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = verify_token(credentials.credentials)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dep

# ---------------------------------------------------------------------------
# Login endpoint stub
# ---------------------------------------------------------------------------

from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(username: str, password: str):
    """Authenticate *username*/ *password* and return a JWT.

    This is a *stub* — it currently returns a synthetic token for the
    built-in "admin" account so other modules can import this file
    without models.py being complete.

    TODO: replace with real DB lookup once models.py exists.
    """
    # ---- stub implementation ----
    # In production this queries the User table:
    #
    #   user = db.query(User).filter(User.username == username).first()
    #   if user is None or not check_password(password, user.password_hash):
    #       raise HTTPException(401, "Invalid credentials")
    #   token = create_access_token(user.id, user.role)
    #   return {"access_token": token, "user": {...}}

    if username == "admin" and password == "admin":
        token = create_access_token(user_id=1, role="admin")
        return {
            "access_token": token,
            "user": {"id": 1, "username": "admin", "role": "admin"},
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )
