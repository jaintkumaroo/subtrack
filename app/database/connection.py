"""Builds the SQLAlchemy engine for SQL Server (default) or SQLite (fallback)."""

from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import settings


def odbc_connection_string(database: str) -> str:
    """Raw ODBC connection string for the configured SQL Server."""
    parts = [
        f"DRIVER={{{settings.mssql_driver}}}",
        f"SERVER={settings.mssql_server}",
        f"DATABASE={database}",
    ]
    if settings.mssql_trusted:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={settings.mssql_user}")
        parts.append(f"PWD={settings.mssql_password}")
    # ODBC Driver 18 encrypts by default and rejects local self-signed certificates.
    parts.append("TrustServerCertificate=yes")
    return ";".join(parts) + ";"


def build_engine(database: str | None = None, **kwargs) -> Engine:
    """Create an engine. `database` lets us connect to `master` for CREATE DATABASE."""
    if settings.db_mode == "sqlite":
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            f"sqlite:///{settings.sqlite_path}",
            connect_args={"check_same_thread": False},
            **kwargs,
        )

    odbc = odbc_connection_string(database or settings.mssql_database)
    url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"
    try:
        return create_engine(url, pool_pre_ping=True, **kwargs)
    except ImportError as error:
        raise RuntimeError(
            "The 'pyodbc' package could not be loaded. Run:  pip install pyodbc\n"
            "(or set DB_MODE=sqlite in the .env file to use the built-in file database)."
        ) from error


engine = build_engine()
