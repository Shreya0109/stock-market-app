"""
Database configuration and session management.

SQLite-based setup for local MVP development.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alphamomentum.db")

# SQLAlchemy setup
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model for ORM
Base = declarative_base()


def init_db():
    """Initialize database tables."""
    logger.info(f"Creating database tables (Database: {DATABASE_URL})...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete")


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
