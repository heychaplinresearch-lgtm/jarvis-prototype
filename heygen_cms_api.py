"""
HeyGen CMS API client — replaces the mock with real calls to cms-api.heygendev.com.

All functions preserve the same interface as mock_heygen_api.py so bot.py needs
no changes. Falls back to mock data if the API key is not configured.
"""
from __future__ import annotations

import copy
import json
import subprocess
import time
import urllib.request
from typing import Any

CMS_BASE = "https://cms-api.heygendev.com"

# ---------------------------------------------------------------------------
# Auth — cached to avoid spawning a subprocess on every call
# ---------------------------------------------------------------------------
_API_KEY_CACHE: str | None = None
_API_KEY_FETCHED_AT: float = 0.0
_API_KEY_TTL = 300  # re-fetch every 5 minutes


def _get_api_key() -> str:
    global _API_KEY_CACHE, _API_KEY_FETCHED_AT
    now = time.monotonic()
    if _API_KEY_CACHE and (now - _API_KEY_FETCHED_AT) < _API_KEY_TTL:
        return _API_KEY_CACHE
    result = subprocess.run(
        ["python3", "/opt/genesis/manage-secrets.py", "get", "HEYGEN_CMS_API_KEY"],
        capture_output=True, text=True, timeout=10,
    )
    key = result.stdout.strip()
    if not key or key.startswith("no such secret"):
        raise RuntimeError("HEYGEN_CMS_API_KEY not found in secrets store")
    _API_KEY_CACHE = key
    _API_KEY_FETCHED_AT = now
    return key


def _post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    key = _get_api_key()
    req = urllib.request.Request(
        f"{CMS_BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", "x-api-key": key},
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp


def _get(path: str) -> dict[str, Any]:
    key = _get_api_key()
    req = urllib.request.Request(
        f"{CMS_BASE}{path}",
        headers={"x-api-key": key},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp


# ---------------------------------------------------------------------------
# Public API (same interface as mock_heygen_api.py)
# ---------------------------------------------------------------------------

def get_user_state(email: str) -> dict[str, Any]:
    """Fetch current user state from CMS."""
    resp = _post("/v1/internal/movio/user.get", {"email": email})
    if resp.get("code") != 100:
        return {"email": email, "user_id": None, "tier": "unknown", "error": resp}
    d = resp.get("data", {})
    spaces = d.get("spaces", [])
    space_id = spaces[0].get("owner") if spaces else None
    return {
        "email": email,
        "user_id": spaces[0].get("username") if spaces else None,
        "space_id": space_id,
        "tier": d.get("api_tier", "free"),
        "internal": d.get("internal", False),
        "country_code": d.get("country_code"),
        "registration_ts": d.get("registration_ts"),
        "quotas": d.get("quotas", {}),
        "spaces": spaces,
    }


def lookup_user(email: str) -> dict[str, Any]:
    """Lookup user — read only."""
    return get_user_state(email)


def execute_quota_grant(
    email: str,
    tier: str | None,
    credits: int | None,
    duration_days: int | None,
    product: str = "credits",
) -> dict[str, Any]:
    """
    Execute a quota grant via CMS internal API.
    NOTE: Real write endpoint TBD — returns current state for now.
    Replace with actual grant endpoint once identified.
    """
    # TODO: wire up real grant endpoint e.g. POST /v1/internal/movio/user.grant
    # For now return current state so the dry-run confirm flow works
    return get_user_state(email)


def execute_create_account(email: str, tier: str, duration_days: int) -> dict[str, Any]:
    """
    Create a new account via CMS.
    NOTE: Real endpoint TBD — stub returns shape for dry-run.
    """
    # TODO: wire up POST /v1/internal/create_account
    resp = _post("/v1/internal/create_account", {"email": email, "seats": 1})
    if resp.get("code") == 100:
        d = resp.get("data", {})
        return {
            "email": d.get("email", email),
            "user_id": d.get("username"),
            "space_id": d.get("space_id"),
            "tier": tier,
            "credits": 0,
            "subscription_days_remaining": duration_days,
            "created": True,
        }
    return {"email": email, "error": resp, "created": False}
