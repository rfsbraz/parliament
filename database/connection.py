"""
Central database connection module for Portuguese Parliament data processing.
Supports both PostgreSQL (production) and SQLite (development) with Lambda-compatible configuration.
"""

import os
import json
import boto3
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load .env file if it exists
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgresql')

# PostgreSQL configuration for RDS
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_USER = os.getenv('PG_USER', 'parluser')
PG_PASSWORD = os.getenv('PG_PASSWORD', '')
PG_DATABASE = os.getenv('PG_DATABASE', 'parliament')

# AWS Secrets Manager for production
DATABASE_SECRET_ARN = os.getenv('DATABASE_SECRET_ARN', '')


def get_database_credentials():
    """Get database credentials from AWS Secrets Manager if running in Lambda."""
    if DATABASE_SECRET_ARN:
        try:
            # Use very short timeout for startup to prevent container blocking
            client = boto3.client('secretsmanager', config=boto3.session.Config(
                connect_timeout=2,  # 2 second connection timeout
                read_timeout=2,     # 2 second read timeout
                retries={'max_attempts': 1}  # Only 1 retry attempt during startup
            ))
            logger.info(f"Fetching database credentials from Secrets Manager: {DATABASE_SECRET_ARN}")
            response = client.get_secret_value(SecretId=DATABASE_SECRET_ARN)
            secret = json.loads(response['SecretString'])
            logger.info(f"Retrieved secret - host: {secret.get('host')}, port: {secret.get('port')}")
            
            host = secret.get('host')
            port = secret.get('port', 5432)
            
            # Ensure port is an integer and handle duplicated ports
            logger.info(f"Original port value: {port} (type: {type(port)})")
            
            if isinstance(port, str):
                # Handle cases like "5432:5432" - take the first valid port
                if ':' in port:
                    port_parts = port.split(':')
                    logger.warning(f"Found colon in port string '{port}', parts: {port_parts}")
                    # Use the first valid port number
                    for part in port_parts:
                        part = part.strip()  # Remove any whitespace
                        try:
                            port = int(part)
                            logger.info(f"Successfully parsed port: {port}")
                            break
                        except ValueError:
                            logger.warning(f"Could not parse part '{part}' as integer")
                            continue
                    else:
                        logger.error(f"Could not parse any port from '{port}', using default 5432")
                        port = 5432
                else:
                    try:
                        port = int(port.strip())
                        logger.info(f"Converted string port to integer: {port}")
                    except ValueError as e:
                        logger.error(f"Error converting port '{port}' to int: {e}")
                        port = 5432
            elif not isinstance(port, int):
                logger.error(f"Port is neither string nor int (type: {type(port)}, value: {port}), using default 5432")
                port = 5432
            
            logger.info(f"Final port value: {port} (type: {type(port)})")
            
            logger.info(f"Processed credentials - host: {host}, port: {port} (type: {type(port)})")
            return {
                'host': host,
                'port': port,
                'username': secret.get('username'),
                'password': secret.get('password'),
                'database': secret.get('database', 'parliament')
            }
        except Exception as e:
            logger.error(f"Error getting credentials from Secrets Manager (will fallback): {e}")
            # Don't raise the exception, return None to allow fallback
    
    return None


def get_database_url() -> str:
    """Get the database URL for PostgreSQL or SQLite fallback."""
    if DATABASE_URL:
        return DATABASE_URL
    
    # Try AWS Secrets Manager first (for Lambda)
    credentials = get_database_credentials()
    if credentials:
        encoded_password = quote_plus(credentials['password'])
        host = credentials['host']
        port = credentials['port']
        
        logger.info(f"Before processing - host: {host}, port: {port}")
        
        # Handle case where host already includes port (e.g., "host.rds.amazonaws.com:5432")
        if host and ':' in str(host):
            host_parts = str(host).split(':')
            host = host_parts[0]  # Use only the hostname part
            # Use the port from the host if no explicit port is provided or if port is duplicated
            if len(host_parts) > 1:
                try:
                    port_from_host = int(host_parts[1])
                    if not port or port == port_from_host:
                        port = port_from_host
                    logger.info(f"Extracted port from host: {port_from_host}, using port: {port}")
                except ValueError as e:
                    logger.error(f"Error parsing port from host '{host_parts[1]}': {e}")
                    # Keep the original port if parsing fails
        
        logger.info(f"After processing - host: {host}, port: {port}")
        
        # Final validation: ensure we don't have duplicate ports in the URL
        try:
            if ':' in str(host) and str(port) in str(host):
                logger.warning(f"Host '{host}' already contains port, using host as-is")
                db_url = f"postgresql://{credentials['username']}:{encoded_password}@{host}/{credentials['database']}?sslmode=require"
            else:
                db_url = f"postgresql://{credentials['username']}:{encoded_password}@{host}:{port}/{credentials['database']}?sslmode=require"
            
            logger.info(f"Generated database URL: postgresql://[username]:[password]@{host}:{port}/{credentials['database']}?sslmode=require")
            logger.info(f"DB URL construction successful")
            return db_url
        except Exception as e:
            logger.error(f"ERROR in URL construction: {e}")
            logger.error(f"Host: {host} (type: {type(host)})")
            logger.error(f"Port: {port} (type: {type(port)})")
            logger.error(f"Credentials: {credentials}")
            raise
    
    # Use environment variables (for local development with PostgreSQL)
    if DATABASE_TYPE == 'postgresql' and PG_PASSWORD:
        encoded_password = quote_plus(PG_PASSWORD)
        return f"postgresql://{PG_USER}:{encoded_password}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}?sslmode=require"
    
    # Fallback to SQLite for local development
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'database', 'parliament_data.db')
    return f"sqlite:///{db_path}"


def create_database_engine(echo: bool = False):
    """Create and return a database engine with connection pooling."""
    url = get_database_url()
    
    # PostgreSQL-specific configuration
    if url.startswith('postgresql://'):
        engine_kwargs = {
            'echo': echo,
            'pool_pre_ping': True,  # Verify connections before use
            'pool_size': 2,  # Much smaller pool for micro instance
            'max_overflow': 3,  # Reduced overflow
            'pool_timeout': 10,  # Shorter timeout
            'pool_recycle': 300,  # Recycle connections every 5 minutes
            'pool_reset_on_return': 'commit',  # Reset connections more aggressively
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'parliament-fiscaliza',
                'sslmode': 'require'  # Required for RDS PostgreSQL
            }
        }
    else:  # SQLite
        engine_kwargs = {
            'echo': echo,
            'pool_pre_ping': True,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 20
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
    credentials = get_database_credentials()
    if credentials:
        return {
            'type': 'postgresql',
            'url': get_database_url(),
            'host': credentials['host'],
            'database': credentials['database'],
            'user': credentials['username'],
            'port': credentials['port'],
        }
    else:
        return {
            'type': DATABASE_TYPE,
            'url': get_database_url(),
            'host': PG_HOST,
            'database': PG_DATABASE,
            'user': PG_USER,
            'port': PG_PORT,
        }