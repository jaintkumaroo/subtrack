"""Currency conversion using a free live exchange-rate API, with an offline fallback."""

import threading
import time

import requests

from app.config import settings

RATES_URL = "https://open.er-api.com/v6/latest/USD"
CACHE_SECONDS = 6 * 60 * 60  # refresh live rates every 6 hours
RETRY_SECONDS = 5 * 60  # after a failed request, wait before trying again

CURRENCIES = {
    "USD": "US Dollar",
    "PKR": "Pakistani Rupee",
    "EUR": "Euro",
    "GBP": "British Pound",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "INR": "Indian Rupee",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "CNY": "Chinese Yuan",
    "JPY": "Japanese Yen",
    "TRY": "Turkish Lira",
    "BDT": "Bangladeshi Taka",
    "MYR": "Malaysian Ringgit",
    "SGD": "Singapore Dollar",
    "CHF": "Swiss Franc",
    "QAR": "Qatari Riyal",
    "KWD": "Kuwaiti Dinar",
    "EGP": "Egyptian Pound",
    "ZAR": "South African Rand",
}

# Approximate units of each currency per 1 USD. Only used when the live API is unreachable.
FALLBACK_RATES = {
    "USD": 1.0,
    "PKR": 280.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "AED": 3.6725,
    "SAR": 3.75,
    "INR": 84.0,
    "CAD": 1.37,
    "AUD": 1.52,
    "CNY": 7.2,
    "JPY": 150.0,
    "TRY": 34.0,
    "BDT": 120.0,
    "MYR": 4.4,
    "SGD": 1.33,
    "CHF": 0.88,
    "QAR": 3.64,
    "KWD": 0.307,
    "EGP": 49.0,
    "ZAR": 18.0,
}

_lock = threading.Lock()
_state = {
    "rates": dict(FALLBACK_RATES),
    "source": "offline",
    "updated": None,
    "fetched": 0.0,
    "retry_at": 0.0,
}


def _fetch_live() -> dict | None:
    try:
        response = requests.get(RATES_URL, timeout=4)
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            return None
        live = data["rates"]
        return {code: float(live[code]) for code in CURRENCIES if code in live}
    except (requests.RequestException, ValueError, KeyError):
        return None


def get_rates() -> dict:
    """Returns {"rates": {...}, "source": "live"|"offline", "updated": iso-string|None}."""
    with _lock:
        now = time.time()
        fresh = _state["source"] == "live" and now - _state["fetched"] < CACHE_SECONDS
        if settings.live_rates and not fresh and now >= _state["retry_at"]:
            live = _fetch_live()
            if live:
                merged = dict(FALLBACK_RATES)
                merged.update(live)
                _state.update(
                    rates=merged,
                    source="live",
                    updated=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
                    fetched=now,
                    retry_at=0.0,
                )
            else:
                _state["retry_at"] = now + RETRY_SECONDS
        return {
            "rates": dict(_state["rates"]),
            "source": _state["source"],
            "updated": _state["updated"],
        }


def convert(amount: float, source: str, target: str, rates: dict) -> float:
    """Convert via USD: amount / rate[source] * rate[target]."""
    if source == target:
        return amount
    return amount / rates[source] * rates[target]
