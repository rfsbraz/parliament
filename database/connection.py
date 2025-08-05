"""
Central database connection module for Portuguese Parliament data processing.
Uses MySQL database with connection pooling and proper configuration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# MySQL configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'parliament_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'parliament_pass')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'parliament')


def get_database_url() -> str:
    """Get the MySQL database URL."""
    if DATABASE_URL:
        return DATABASE_URL
    
    return f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"


def create_database_engine(echo: bool = False):
    """Create and return a MySQL database engine with connection pooling."""
    url = get_database_url()
    
    engine_kwargs = {
        'echo': echo,
        'pool_pre_ping': True,  # Verify connections before use
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,  # Recycle connections every hour
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 60,
            'read_timeout': 30,
            'write_timeout': 30,
        }
    }
    
    return create_engine(url, **engine_kwargs)


# Global engine and session factory
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine():
    """Get the global database engine, creating it if necessary."""
    global _engine
    if _engine is None:
        _engine = create_database_engine()
    return _engine


def get_session_factory():
    """Get the global session factory, creating it if necessary."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal


def get_session():
    """Get a new database session with context manager support."""
    SessionLocal = get_session_factory()
    return SessionLocal()


class DatabaseSession:
    """Context manager for database sessions."""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        SessionLocal = get_session_factory()
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Exception in DatabaseSession, rolling back: {exc_type.__name__}: {exc_val}")
                self.session.rollback()
                logger.debug("Session rolled back due to exception")
            self.session.close()


def get_database_info() -> dict:
    """Get information about the current database configuration."""
    return {
        'type': 'mysql',
        'url': get_database_url(),
        'host': MYSQL_HOST,
        'database': MYSQL_DATABASE,
        'user': MYSQL_USER,
        'port': MYSQL_PORT,
    }