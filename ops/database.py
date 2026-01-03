"""
Database management commands for Parliament Operations CLI.

Handles database clearing, resetting, and maintenance operations.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

import click

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .config import get_config


def get_terraform_output(terraform_dir: Path, output_name: str) -> str:
    """Get a specific terraform output value."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", output_name],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def get_production_db_url(config) -> tuple[str, dict]:
    """Get database URL from AWS Secrets Manager for production."""
    import boto3

    # Get secret ARN from terraform
    secret_arn = get_terraform_output(config.terraform_dir, "database_secret_arn")
    if not secret_arn:
        raise click.ClickException("Could not get database_secret_arn from terraform outputs")

    # Get credentials from Secrets Manager
    session = boto3.Session(profile_name=config.aws.profile, region_name=config.aws.region)
    client = session.client('secretsmanager')

    response = client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response['SecretString'])

    host = secret.get('host')
    port = secret.get('port', 5432)
    username = secret.get('username')
    password = secret.get('password')
    database = secret.get('database', 'parliament')

    # Handle host that already includes port (e.g., "host.rds.amazonaws.com:5432")
    if host and ':' in str(host):
        host_parts = str(host).split(':')
        host = host_parts[0]
        if len(host_parts) > 1:
            try:
                port = int(host_parts[1])
            except ValueError:
                port = 5432

    # Handle port if it's a string with duplicates (e.g., "5432:5432")
    if isinstance(port, str):
        port_str = port.split(':')[0] if ':' in port else port
        try:
            port = int(port_str.strip())
        except ValueError:
            port = 5432
    elif not isinstance(port, int):
        port = 5432

    encoded_password = quote_plus(password)
    db_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}?sslmode=require"

    info = {
        'source': 'AWS Secrets Manager (production)',
        'host': host,
        'port': port,
        'database': database,
        'username': username
    }

    return db_url, info


def create_production_engine(config, echo: bool = False):
    """Create database engine for production RDS."""
    from sqlalchemy import create_engine

    db_url, _ = get_production_db_url(config)

    return create_engine(
        db_url,
        echo=echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={
            'connect_timeout': 30,
            'sslmode': 'require'
        }
    )


def get_db_connection_info(production: bool = False):
    """Get database connection information for display."""
    if production:
        try:
            config = get_config()
            _, info = get_production_db_url(config)
            return info
        except Exception as e:
            return {
                'source': 'Production (error)',
                'host': 'Unknown',
                'database': 'Unknown',
                'error': str(e)
            }

    try:
        from database.connection import DATABASE_SECRET_ARN, PG_HOST, PG_DATABASE

        if DATABASE_SECRET_ARN:
            return {
                'source': 'AWS Secrets Manager',
                'host': 'RDS (from secrets)',
                'database': 'parliament'
            }
        else:
            return {
                'source': 'Local (environment variables)',
                'host': PG_HOST,
                'database': PG_DATABASE
            }
    except Exception as e:
        return {
            'source': 'Unknown',
            'host': 'Unknown',
            'database': 'Unknown',
            'error': str(e)
        }


def clear_all_tables(engine, echo: bool = False):
    """Clear all data from tables without dropping them."""
    from sqlalchemy import text, MetaData

    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Get tables in reverse dependency order (to handle foreign keys)
    tables = list(reversed(metadata.sorted_tables))

    cleared_count = 0
    with engine.begin() as conn:
        # Disable foreign key checks temporarily for PostgreSQL
        conn.execute(text("SET session_replication_role = 'replica';"))

        for table in tables:
            if echo:
                click.echo(f"    Clearing table: {table.name}")
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
            cleared_count += 1

        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = 'origin';"))

    return cleared_count


def drop_and_recreate_tables(engine, echo: bool = False):
    """Drop all tables and recreate them from models."""
    from database.models import Base

    if echo:
        click.echo("    Dropping all tables...")

    Base.metadata.drop_all(bind=engine)

    if echo:
        click.echo("    Creating tables from models...")

    Base.metadata.create_all(bind=engine)

    return len(Base.metadata.tables)


def reset_import_status(engine, echo: bool = False):
    """Reset all import status records to 'discovered' state."""
    from sqlalchemy import text

    with engine.begin() as conn:
        # Check if import_status table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'import_status'
            )
        """))
        if not result.scalar():
            if echo:
                click.echo("    import_status table does not exist, skipping...")
            return 0

        # Get count before reset
        count_result = conn.execute(text("SELECT COUNT(*) FROM import_status WHERE status != 'discovered'"))
        count = count_result.scalar()

        if count == 0:
            if echo:
                click.echo("    No import status records to reset")
            return 0

        # Reset all records
        conn.execute(text("""
            UPDATE import_status
            SET
                status = 'discovered',
                processing_started_at = NULL,
                processing_completed_at = NULL,
                error_message = NULL,
                records_imported = 0,
                error_count = 0,
                retry_at = NULL,
                updated_at = NOW()
            WHERE status != 'discovered'
        """))

        if echo:
            click.echo(f"    Reset {count} import status records to 'discovered'")

        return count


def get_engine(production: bool, verbose: bool):
    """Get database engine based on production flag."""
    if production:
        config = get_config()
        return create_production_engine(config, echo=verbose)
    else:
        from database.connection import create_database_engine
        return create_database_engine(echo=verbose)


@click.group()
def database():
    """Database management commands."""
    pass


@database.command()
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--preserve-schema', is_flag=True, help='Keep tables, only clear data')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.option('--production', '-p', is_flag=True, help='Connect to production RDS database')
def clear(yes: bool, preserve_schema: bool, verbose: bool, production: bool):
    """
    Clear all data from the database.

    By default, drops and recreates all tables from models.
    Use --preserve-schema to only truncate data while keeping table structure.
    Use --production to connect to the production RDS database.
    """
    click.echo(click.style("\n[Database] Clear Database", fg="blue", bold=True))

    # Show connection info
    info = get_db_connection_info(production=production)
    click.echo(f"  Source: {info['source']}")
    click.echo(f"  Host: {info['host']}")
    click.echo(f"  Database: {info['database']}")

    if 'error' in info:
        raise click.ClickException(f"Could not get database info: {info['error']}")

    # Extra warning for production
    if production:
        click.echo(click.style("\n  ⚠️  WARNING: You are about to modify PRODUCTION database!", fg="red", bold=True))

    # Confirmation
    if not yes:
        action = "truncate all tables" if preserve_schema else "drop and recreate all tables"
        if not click.confirm(click.style(f"\n  WARNING: This will {action}. Continue?", fg="yellow")):
            click.echo("  Aborted.")
            return

    try:
        engine = get_engine(production, verbose)

        if preserve_schema:
            click.echo("\n  Truncating all tables...")
            count = clear_all_tables(engine, echo=verbose)
            click.echo(click.style(f"\n  Cleared {count} tables successfully!", fg="green"))
        else:
            click.echo("\n  Dropping and recreating tables...")
            count = drop_and_recreate_tables(engine, echo=verbose)
            click.echo(click.style(f"\n  Recreated {count} tables successfully!", fg="green"))

    except Exception as e:
        raise click.ClickException(f"Database operation failed: {e}")


@database.command()
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed progress')
@click.option('--production', '-p', is_flag=True, help='Connect to production RDS database')
def reset_imports(yes: bool, verbose: bool, production: bool):
    """
    Reset all import status records to 'discovered' state.

    This allows all files to be re-imported by the pipeline.
    Use --production to connect to the production RDS database.
    """
    click.echo(click.style("\n[Database] Reset Import Status", fg="blue", bold=True))

    # Show connection info
    info = get_db_connection_info(production=production)
    click.echo(f"  Source: {info['source']}")
    click.echo(f"  Host: {info['host']}")
    click.echo(f"  Database: {info['database']}")

    # Extra warning for production
    if production:
        click.echo(click.style("\n  ⚠️  WARNING: You are about to modify PRODUCTION database!", fg="red", bold=True))

    # Confirmation
    if not yes:
        if not click.confirm(click.style("\n  This will reset all import status records. Continue?", fg="yellow")):
            click.echo("  Aborted.")
            return

    try:
        engine = get_engine(production, verbose)
        count = reset_import_status(engine, echo=verbose)

        if count > 0:
            click.echo(click.style(f"\n  Reset {count} import status records!", fg="green"))
        else:
            click.echo(click.style("\n  No records needed to be reset.", fg="cyan"))

    except Exception as e:
        raise click.ClickException(f"Reset failed: {e}")


@database.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed table information')
@click.option('--production', '-p', is_flag=True, help='Connect to production RDS database')
def status(verbose: bool, production: bool):
    """Show database status and table statistics."""
    from sqlalchemy import text, MetaData

    click.echo(click.style("\n[Database] Status", fg="blue", bold=True))

    # Show connection info
    info = get_db_connection_info(production=production)
    click.echo(f"\n  Connection: {info['source']}")
    click.echo(f"  Host: {info['host']}")
    click.echo(f"  Database: {info['database']}")

    if 'error' in info:
        raise click.ClickException(f"Could not get database info: {info['error']}")

    try:
        engine = get_engine(production, verbose=False)
        metadata = MetaData()
        metadata.reflect(bind=engine)

        click.echo(f"\n  Tables: {len(metadata.tables)}")

        if verbose:
            click.echo("\n  Table row counts:")
            with engine.connect() as conn:
                for table in sorted(metadata.tables.keys()):
                    try:
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                        count = result.scalar()
                        if count > 0:
                            click.echo(f"    {table}: {count:,} rows")
                    except Exception:
                        click.echo(f"    {table}: (error reading)")

        # Check import status if table exists
        if 'import_status' in metadata.tables:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT status, COUNT(*) as count
                    FROM import_status
                    GROUP BY status
                    ORDER BY count DESC
                """))
                rows = result.fetchall()

                if rows:
                    click.echo("\n  Import status:")
                    for row in rows:
                        click.echo(f"    {row[0]}: {row[1]:,}")

        click.echo(click.style("\n  Database connection OK", fg="green"))

    except Exception as e:
        raise click.ClickException(f"Could not connect to database: {e}")
