import os

from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Base for models
Base = declarative_base()

# Import models to ensure they are registered with Base.metadata
# Note: We import them inside init_db or ensure they use the same Base
# Ideally, sql_models.py should import Base from here.

# Database Manager 

class DatabaseManager:
    """Singleton database manager."""
    
    _instance = None
    
    def __new__(cls, db_url: str = "sqlite:///data/orbis_ethica.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db(db_url)
        return cls._instance
    
    def _init_db(self, db_url: str):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = SessionLocal
        
        # Import models here to ensure they are registered
        
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
# Use /app/data for Docker persistence, fallback to local backend/ for local dev without docker
def init_db(db_url: str = "sqlite:///data/orbis_ethica.db"):
    # Check if /app/data exists (Docker), otherwise use local path
    if not os.path.exists("/app/data") and not db_url.startswith("sqlite:///data"):
         # Fallback for local python run
         db_url = "sqlite:///backend/orbis_ethica.db"
         
    DatabaseManager(db_url)

def SessionLocal():
    return DatabaseManager().get_session()
