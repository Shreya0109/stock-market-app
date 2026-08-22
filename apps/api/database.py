"""
Database configuration and session management.

SQLite-based setup for local MVP development.
"""

import os
from sqlalchemy import create_engine, inspect, text
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
    # Import ORM models before create_all so SQLAlchemy metadata is populated.
    from apps.api.app import models as _models  # noqa: F401

    logger.info(f"Creating database tables (Database: {DATABASE_URL})...")
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_schema_compatibility()
    logger.info("Database initialization complete")


def _ensure_sqlite_schema_compatibility():
    """Apply narrow SQLite compatibility upgrades for local MVP databases."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "symbols" not in table_names:
        return

    existing_symbol_columns = {column["name"] for column in inspector.get_columns("symbols")}
    symbol_migrations = {
        "last_close": "ALTER TABLE symbols ADD COLUMN last_close FLOAT",
        "metadata_updated_at": "ALTER TABLE symbols ADD COLUMN metadata_updated_at DATETIME",
    }
    with engine.begin() as connection:
        for column_name, statement in symbol_migrations.items():
            if column_name not in existing_symbol_columns:
                logger.info("Adding missing SQLite column symbols.%s", column_name)
                connection.execute(text(statement))

    if "indicator_values" not in table_names:
        return

    existing_indicator_columns = {column["name"] for column in inspector.get_columns("indicator_values")}
    indicator_migrations = {
        "breakout_high_20": "ALTER TABLE indicator_values ADD COLUMN breakout_high_20 FLOAT",
        "breakout_low_20": "ALTER TABLE indicator_values ADD COLUMN breakout_low_20 FLOAT",
        "ineligible_reason": "ALTER TABLE indicator_values ADD COLUMN ineligible_reason TEXT",
        "updated_at": "ALTER TABLE indicator_values ADD COLUMN updated_at DATETIME",
    }
    with engine.begin() as connection:
        for column_name, statement in indicator_migrations.items():
            if column_name not in existing_indicator_columns:
                logger.info("Adding missing SQLite column indicator_values.%s", column_name)
                connection.execute(text(statement))


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
