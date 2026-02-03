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
        if db_url is None:
             # DEBUG: Force In-Memory DB to bypass FS issues
             db_url = "sqlite://"
             print(f"⚠️ DEBUG MODE: Using In-Memory Database (RAM only)")

             # Check for Docker/Env override
             if os.path.exists("/app/data"):
                 db_url = "sqlite:///data/orbis_ethica.db"
        
        print(f"📂 DatabaseManager initializing with: {db_url}")
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
def init_db(db_url: str = None):
    # DEBUG: Force In-Memory DB to bypass FS issues
    final_url = "sqlite://" 
    print(f"⚠️ DEBUG MODE: Using In-Memory Database (RAM only) due to FS permission issues.")

    # Check for Docket/Env override
    if os.path.exists("/app/data"):
         final_url = "sqlite:///data/orbis_ethica.db"
    
    if db_url and db_url.startswith("sqlite"):
         final_url = db_url

    print(f"📂 initializing DB at: {final_url}")
    DatabaseManager(final_url)

def SessionLocal():
    return DatabaseManager().get_session()
