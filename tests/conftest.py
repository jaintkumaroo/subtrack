"""Test setup: use a throwaway SQLite file and never touch the internet or SQL Server."""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_tmp = tempfile.mkdtemp(prefix="subtrack-tests-")
os.environ["DB_MODE"] = "sqlite"
os.environ["SQLITE_PATH"] = str(Path(_tmp) / "test.db")
os.environ["LIVE_RATES"] = "false"
os.environ["BASE_CURRENCY"] = "PKR"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        test_client.delete("/demo/clear")
        yield test_client
