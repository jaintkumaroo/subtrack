"""Connection checker. Run it when SQL Server will not connect:

    python -m app.database.diagnose
"""

from sqlalchemy import text

from app.config import settings
from app.database.connection import build_engine


def main() -> None:
    print(f"Mode        : {settings.db_mode}")
    if settings.db_mode == "sqlite":
        print(f"SQLite file : {settings.sqlite_path}")
        print("Nothing else to check. SQLite needs no server.")
        return

    import pyodbc

    print(f"Server      : {settings.mssql_server}")
    print(f"Database    : {settings.mssql_database}")
    print(f"Driver      : {settings.mssql_driver}")
    print(f"Auth        : {'Windows' if settings.mssql_trusted else 'SQL login'}")
    print()

    drivers = pyodbc.drivers()
    print("ODBC drivers installed on this computer:")
    for name in drivers:
        marker = "  <-- in use" if name == settings.mssql_driver else ""
        print(f"  - {name}{marker}")
    if settings.mssql_driver not in drivers:
        print("\nPROBLEM: the driver in .env is not installed.")
        print("Copy one of the names above into MSSQL_DRIVER in the .env file.")
        return

    print("\nConnecting to the server (master database)...")
    try:
        engine = build_engine("master")
        with engine.connect() as conn:
            version = conn.execute(text("SELECT @@VERSION")).scalar()
        print("OK: connected.")
        print(str(version).splitlines()[0])
    except Exception as error:  # noqa: BLE001 - we want to show any failure
        print("\nPROBLEM: could not connect.")
        print(error)
        print("\nCheck MSSQL_SERVER in .env. It must match the 'Server name' you type in SSMS,")
        print("and the SQL Server service must be running (Services > SQL Server).")


if __name__ == "__main__":
    main()
