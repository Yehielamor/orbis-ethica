import os
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import create_engine, Column, String, Float, Integer, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship

# Base for models
Base = declarative_base()

# Import models to ensure they are registered with Base.metadata
# Note: We import them inside init_db or ensure they use the same Base
# Ideally, sql_models.py should import Base from here.

# --- Database Manager ---

class DatabaseManager:
    """Singleton database manager."""
    
    _instance = None
    
    def __new__(cls, db_url: str = "sqlite:///orbis_ethica.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db(db_url)
        return cls._instance
    
    def _init_db(self, db_url: str):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = SessionLocal
        
        # Import models here to ensure they are registered
        from .models import sql_models
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        print(f"💾 Database initialized at {db_url}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

# Global instance accessor
def get_db():
    db = DatabaseManager().get_session()
    try:
        yield db
    finally:
        db.close()

# Helpers for compatibility with existing code
def init_db(db_url: str = "sqlite:///orbis_ethica.db"):
    DatabaseManager(db_url)

def SessionLocal():
    return DatabaseManager().get_session()
