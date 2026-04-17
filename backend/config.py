"""
Configuration for Jarsh Safety ECIMS
Railway deployment version — reads from environment variables
"""
import os


class Config:
    # ── Database ──────────────────────────────────────────────
    # Railway provides DATABASE_URL automatically when you add MySQL plugin
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # If DATABASE_URL is set (Railway), use it directly
    # Otherwise fall back to individual vars (local dev)
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
        MYSQL_USER = os.getenv("MYSQL_USER", "root")
        MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Jarsh@23895")
        MYSQL_DB = os.getenv("MYSQL_DB", "ecims")
        SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:Jarsh%4023895@localhost:3306/ecims"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jarsh-ecims-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = 28800  # 8 hours

    # ── App ───────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "jarsh-ecims-flask-secret")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
