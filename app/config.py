"""Application settings, loaded from environment variables / the .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _text(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _flag(name: str, default: bool) -> bool:
    value = _text(name, "")
    if value == "":
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


class Settings:
    """Plain settings object. Edit the values in the .env file, not here."""

    def __init__(self) -> None:
        # "mssql" = Microsoft SQL Server, "sqlite" = local file (fallback / tests)
        self.db_mode: str = _text("DB_MODE", "mssql").lower()

        # --- SQL Server ---
        self.mssql_server: str = _text("MSSQL_SERVER", r"localhost\SQLEXPRESS")
        self.mssql_database: str = _text("MSSQL_DATABASE", "SubTrack")
        self.mssql_driver: str = _text("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
        self.mssql_trusted: bool = _flag("MSSQL_TRUSTED_CONNECTION", True)
        self.mssql_user: str = _text("MSSQL_USER")
        self.mssql_password: str = _text("MSSQL_PASSWORD")

        # --- SQLite fallback ---
        sqlite_name = _text("SQLITE_PATH", "subtrack.db")
        sqlite_path = Path(sqlite_name)
        self.sqlite_path: Path = (
            sqlite_path if sqlite_path.is_absolute() else ROOT_DIR / sqlite_path
        )

        # --- Money ---
        self.base_currency: str = _text("BASE_CURRENCY", "PKR").upper()
        self.live_rates: bool = _flag("LIVE_RATES", True)

    @property
    def db_label(self) -> str:
        return "SQL Server" if self.db_mode == "mssql" else "SQLite"


settings = Settings()
