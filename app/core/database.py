from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.core.config import settings

# 1. Instantiate the SQLAlchemy Database Engine
# pool_pre_ping checks if connection is alive before issuing a query, preventing stale connection errors
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Set to True to log raw SQL statements in logs (useful in debugging)
)

# 2. Define the Session Factory
# Sessions will be spawned from this class per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Define the Declarative Base class
# All database models will inherit from this Base
Base = declarative_base()

# 4. Define the Database Session Dependency
def get_db() -> Generator:
    """
    FastAPI dependency that yields a database session.
    Guarantees that the session is closed at the end of the HTTP request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
