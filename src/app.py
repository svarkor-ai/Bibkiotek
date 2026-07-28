"""Bibliotek — FastAPI application entry point.

Wires together all feature routers, sets up Jinja2 templates,
mounts static files, and runs startup initialisation (DB creation
+ admin seed user).
"""

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.auth import create_access_token
from src.database import init_db
from src.models import User
from src.users import register_user

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(title="Bibliotek", version="0.1.0")

# ---------------------------------------------------------------------------
# Templates & static files
# ---------------------------------------------------------------------------

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------------------------------------
# Startup — create tables and seed admin user
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    """Initialise the database and ensure an admin account exists."""
    init_db()

    from src.database import get_session_cm

    with get_session_cm() as db:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None:
            register_user(
                db,
                username="admin",
                password="admin",
                role="admin",
            )


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

@app.get("/")
async def home(request: Request) -> dict:
    """Render the home page (index.html)."""
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "year": datetime.now(timezone.utc).year,
        },
    )


# ---------------------------------------------------------------------------
# Wire routers
# ---------------------------------------------------------------------------

from src.auth import router as auth_router
from src.books import create_router as books_router
from src.circulation import create_router as loans_router
from src.users import create_router as users_router

app.include_router(auth_router)
app.include_router(books_router())
app.include_router(loans_router())
app.include_router(users_router())
