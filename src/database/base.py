"""
SQLAlchemy base configuration and declarative base.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()


def createEngine(databaseUrl: str, poolSize: int = 5, maxOverflow: int = 10):
    """
    Create SQLAlchemy engine with connection pooling.

    Args:
        databaseUrl: PostgreSQL connection string
        poolSize: Number of connections to maintain
        maxOverflow: Maximum overflow connections

    Returns:
        SQLAlchemy engine instance
    """
    return create_engine(
        databaseUrl,
        poolclass=QueuePool,
        pool_size=poolSize,
        max_overflow=maxOverflow,
        pool_pre_ping=True,  # Verify connections before using
        echo=False,
    )


def createSessionFactory(engine):
    """
    Create session factory bound to engine.

    Args:
        engine: SQLAlchemy engine

    Returns:
        Session factory
    """
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)
