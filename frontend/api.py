"""Thin client for the SubTrack backend. Every call the UI makes to the API lives here."""

import os
from typing import Any, Optional

import requests

BASE_URL = os.getenv("SUBTRACK_API_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(Exception):
    """Raised for any failed call. `offline` is True when the backend cannot be reached at all."""

    def __init__(self, message: str, offline: bool = False):
        super().__init__(message)
        self.offline = offline


_FRIENDLY = {
    "String should have at least 1 character": "please fill this in",
    "Name cannot be empty": "please enter a name",
    "greater than 0": "must be greater than zero",
    "Field required": "this field is required",
}


def _error_message(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        return f"Server error ({response.status_code})"
    if isinstance(detail, list):  # validation errors from FastAPI
        parts = []
        for item in detail:
            field = " > ".join(str(p) for p in item.get("loc", []) if p != "body").replace("_", " ")
            message = str(item.get("msg", "Invalid value")).removeprefix("Value error, ")
            for technical, friendly in _FRIENDLY.items():
                if technical in message:
                    message = friendly
                    break
            label = field.capitalize() if field else ""
            parts.append(f"{label}: {message}" if label else message)
        return "; ".join(parts)
    return str(detail or f"Server error ({response.status_code})")


def _call(method: str, path: str, **kwargs: Any) -> requests.Response:
    try:
        response = requests.request(method, f"{BASE_URL}{path}", timeout=20, **kwargs)
    except requests.ConnectionError:
        raise ApiError(f"Cannot reach the SubTrack backend at {BASE_URL}.", offline=True)
    except requests.Timeout:
        raise ApiError("The backend took too long to answer.", offline=True)
    if response.status_code >= 400:
        raise ApiError(_error_message(response))
    return response


# --------------------------------------------------------------------- system
def health() -> dict:
    return _call("GET", "/health").json()


def meta() -> dict:
    return _call("GET", "/meta").json()


def rates() -> dict:
    return _call("GET", "/rates").json()


def seed_demo() -> int:
    return _call("POST", "/demo/seed").json()["added"]


def clear_all() -> int:
    return _call("DELETE", "/demo/clear").json()["deleted"]


# ----------------------------------------------------------------- categories
def categories() -> list[dict]:
    return _call("GET", "/categories").json()


def create_category(name: str, color: str) -> dict:
    return _call("POST", "/categories", json={"name": name, "color": color}).json()


# -------------------------------------------------------------- subscriptions
def subscriptions(
    base: str,
    status: str = "all",
    category_id: Optional[int] = None,
    search: str = "",
    sort: str = "renewal",
) -> list[dict]:
    params: dict[str, Any] = {"base": base, "status": status, "sort": sort}
    if category_id is not None:
        params["category_id"] = category_id
    if search:
        params["search"] = search
    return _call("GET", "/subscriptions", params=params).json()


def create_subscription(payload: dict, base: str) -> dict:
    return _call("POST", "/subscriptions", json=payload, params={"base": base}).json()


def update_subscription(sub_id: int, payload: dict, base: str) -> dict:
    return _call("PUT", f"/subscriptions/{sub_id}", json=payload, params={"base": base}).json()


def toggle_subscription(sub_id: int, base: str) -> dict:
    return _call("PATCH", f"/subscriptions/{sub_id}/toggle", params={"base": base}).json()


def delete_subscription(sub_id: int) -> None:
    _call("DELETE", f"/subscriptions/{sub_id}")


# ---------------------------------------------------------- dashboard/reports
def dashboard(base: str) -> dict:
    return _call("GET", "/dashboard", params={"base": base}).json()


def export_csv(base: str) -> bytes:
    return _call("GET", "/reports/export.csv", params={"base": base}).content
