"""
Configuration for Jarsh Safety ECIMS
Render deployment — PostgreSQL
"""
import os


class Config:
    # ── Database ──────────────────────────────────────────────
    # Render provides DATABASE_URL automatically
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    if DATABASE_URL:
        # Render gives postgres:// but SQLAlchemy needs postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Local development fallback — uses your local MySQL
        SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:Jarsh%4023895@localhost:3306/ecims"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jarsh-ecims-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = 28800  # 8 hours

    # ── App ───────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "jarsh-ecims-flask-secret")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
