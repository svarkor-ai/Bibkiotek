"""Configuration — reads from env, never inlines secrets."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bibliotek.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h
