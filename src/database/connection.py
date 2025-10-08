"""
Database connection manager with pooling and session management.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .base import Base

load_dotenv()


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, databaseUrl: str | None = None):
        """
        Initialize database manager.

        Args:
            databaseUrl: PostgreSQL connection string (defaults to env var)
        """
        self.databaseUrl = databaseUrl or os.getenv(
            "DATABASE_URL", "postgresql://localhost:5432/motoprice"
        )
        self.poolSize = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.maxOverflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

        self.engine = create_engine(
            self.databaseUrl,
            poolclass=QueuePool,
            pool_size=self.poolSize,
            max_overflow=self.maxOverflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,
        )

        self.SessionFactory = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def createTables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)

    def dropTables(self):
        """Drop all tables from the database."""
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def getSession(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Yields:
            Database session

        Example:
            with dbManager.getSession() as session:
                session.add(motorcycle)
                session.commit()
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self):
        """Dispose of the engine connection pool."""
        self.engine.dispose()


# Global database manager instance
_dbManager: DatabaseManager | None = None


def getDatabaseManager() -> DatabaseManager:
    """
    Get global database manager instance.

    Returns:
        DatabaseManager instance
    """
    global _dbManager
    if _dbManager is None:
        _dbManager = DatabaseManager()
    return _dbManager


def getSession() -> Generator[Session, None, None]:
    """
    Shorthand for getting a database session.

    Yields:
        Database session
    """
    dbManager = getDatabaseManager()
    with dbManager.getSession() as session:
        yield session
