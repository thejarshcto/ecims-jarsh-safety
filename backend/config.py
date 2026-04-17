import os

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if not DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = "sqlite:///ecims.db"
    else:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jarsh-ecims-secret")
    JWT_ACCESS_TOKEN_EXPIRES = 28800
    SECRET_KEY = os.getenv("SECRET_KEY", "jarsh-ecims-flask-secret")
    DEBUG = False