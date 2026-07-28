"""User CRUD + FastAPI router for Bibliotek.

Functions
    register_user(db, username, password, role, email) -> User
    get_user(db, user_id) -> User or 404
    list_users(db, role_filter) -> list[User]
    update_user(db, user_id, **kwargs) -> User
    create_router() -> FastAPI router mounted at /api/users

Endpoints
    POST   /api/users/register          → {user}
    GET    /api/users                   → [users]          [admin]
    GET    /api/users/{id}              → {user}           [admin/librarian]
    PUT    /api/users/{id}              → {user}           [admin/librarian]
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth import check_password, hash_password, require_role
from src.database import get_session
from src.models import User, VALID_ROLES


# ---------------------------------------------------------------------------
# CRUD functions — accept explicit DB session
# ---------------------------------------------------------------------------


def register_user(
    db: Session,
    username: str,
    password: str,
    role: str = "user",
    email: str | None = None,
) -> User:
    """Persist a new user with a bcrypt-hashed password.

    Parameters
    ----------
    db:
        SQLAlchemy session.
    username:
        Unique username (max 50 chars).
    password:
        Plain-text password (hashed with bcrypt before storage).
    role:
        One of ``admin``, ``librarian``, or ``user`` (default ``user``).
    email:
        Optional email address.

    Returns
    -------
    User
        The newly created ORM User instance.

    Raises
    ------
    HTTPException(400):
        If *username* already exists or *role* is invalid.
    """
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role {role!r}. Must be one of {VALID_ROLES}",
        )

    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {username!r} already exists",
        )

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        email=email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User:
    """Retrieve a single user by primary key.

    Returns
    -------
    User
        The user if found.

    Raises
    ------
    HTTPException(404):
        When no user with *user_id* exists.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def list_users(db: Session, role_filter: str | None = None) -> list[User]:
    """Return a (optionally role-filtered) list of users.

    Parameters
    ----------
    db:
        SQLAlchemy session.
    role_filter:
        Optional role to filter by (e.g. ``"librarian"``).

    Returns
    -------
    list[User]
    """
    q = db.query(User)
    if role_filter:
        q = q.filter(User.role == role_filter)
    return q.order_by(User.id).all()


def update_user(
    db: Session,
    user_id: int,
    **kwargs,
) -> User:
    """Update fields on an existing user.

    Accepts any keyword arguments that match User columns:
    ``username``, ``password``, ``role``, ``email``.

    ``password`` is automatically hashed with bcrypt before storage.

    Returns
    -------
    User
        The updated ORM User instance.

    Raises
    ------
    HTTPException(404):
        If no user with *user_id* exists.
    HTTPException(400):
        If a validation error occurs (e.g. invalid role).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate role if being updated
    if "role" in kwargs and kwargs["role"] not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role {kwargs['role']!r}. Must be one of {VALID_ROLES}",
        )

    # Hash password if being updated
    if "password" in kwargs:
        kwargs["password_hash"] = hash_password(kwargs.pop("password"))

    for key, value in kwargs.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------


def create_router() -> APIRouter:
    """Build and return a FastAPI ``APIRouter`` mounted at ``/api/users``."""
    router = APIRouter(prefix="/api/users", tags=["users"])

    _dep_admin = require_role(["admin"])
    _dep_admin_librarian = require_role(["admin", "librarian"])

    # ------------------------------------------------------------------
    # POST /api/users/register — public registration
    # ------------------------------------------------------------------
    @router.post("/register")
    async def register_endpoint(
        username: str = Body(..., min_length=2, max_length=50),
        password: str = Body(..., min_length=4),
        role: str = Body("user"),
        email: str | None = Body(None),
        db: Session = Depends(get_session),
    ) -> dict:
        """Public user registration."""
        user = register_user(db, username, password, role, email)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    # ------------------------------------------------------------------
    # GET /api/users — list all users [admin]
    # ------------------------------------------------------------------
    @router.get("", response_model=dict)
    async def list_users_endpoint(
        role_filter: str | None = Query(None),
        db: Session = Depends(get_session),
        current_user: dict = Depends(_dep_admin),
    ) -> dict:
        """List all users (admin only)."""
        users = list_users(db, role_filter=role_filter)
        return {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "email": u.email,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": len(users),
        }

    # ------------------------------------------------------------------
    # GET /api/users/{user_id} — get single user [admin/librarian]
    # ------------------------------------------------------------------
    @router.get("/{user_id}", response_model=dict)
    async def get_user_endpoint(
        user_id: int,
        db: Session = Depends(get_session),
        current_user: dict = Depends(_dep_admin_librarian),
    ) -> dict:
        """Get a single user by ID (admin/librarian only)."""
        user = get_user(db, user_id)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    # ------------------------------------------------------------------
    # PUT /api/users/{user_id} — update user [admin/librarian]
    # ------------------------------------------------------------------
    @router.put("/{user_id}", response_model=dict)
    async def update_user_endpoint(
        user_id: int,
        username: str | None = Query(None),
        password: str | None = Query(None),
        role: str | None = Query(None),
        email: str | None = Query(None),
        db: Session = Depends(get_session),
        current_user: dict = Depends(_dep_admin_librarian),
    ) -> dict:
        """Update a user (admin/librarian only).

        Omitted fields are not changed.  Pass ``password`` to hash & store
        a new password.
        """
        kwargs: dict = {}
        if username is not None:
            kwargs["username"] = username
        if password is not None:
            kwargs["password"] = password
        if role is not None:
            kwargs["role"] = role
        if email is not None:
            kwargs["email"] = email

        if not kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        user = update_user(db, user_id, **kwargs)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    return router
