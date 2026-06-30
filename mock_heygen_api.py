"""
Mock HeyGen internal API — stands in for the real ops API endpoints.
In production these would call the actual HeyGen backend.

Returns realistic-shaped state objects so the prototype flow is meaningful.
"""
from __future__ import annotations

import copy
import json
from typing import Any

# In-memory mock state — keyed by email
_MOCK_USERS: dict[str, dict[str, Any]] = {
    "teodora@heygen.com": {
        "email": "teodora@heygen.com",
        "user_id": "usr_abc123",
        "space_id": "spc_def456",
        "tier": "free",
        "credits": 0,
        "api_quota": 0,
        "subscription_days_remaining": 0,
        "last_active": "2026-06-28",
        "videos_created_7d": 3,
    },
    "mtoth109@gmail.com": {
        "email": "mtoth109@gmail.com",
        "user_id": "usr_bbb222",
        "space_id": "spc_ccc333",
        "tier": "pro",
        "credits": 150,
        "api_quota": 0,
        "subscription_days_remaining": 12,
        "last_active": "2026-06-30",
        "videos_created_7d": 11,
    },
}


def get_user_state(email: str) -> dict[str, Any]:
    """Fetch current user state. Returns a snapshot dict."""
    if email in _MOCK_USERS:
        return copy.deepcopy(_MOCK_USERS[email])
    # Unknown user — return minimal shape
    return {
        "email": email,
        "user_id": None,
        "tier": "unknown",
        "credits": 0,
        "api_quota": 0,
        "note": "user not found in mock db",
    }


def execute_quota_grant(email: str, tier: str | None, credits: int | None,
                         duration_days: int | None, product: str = "credits") -> dict[str, Any]:
    """Mock execute a quota grant. Mutates mock state, returns after-state."""
    if email not in _MOCK_USERS:
        _MOCK_USERS[email] = {
            "email": email, "user_id": None, "space_id": None,
            "tier": "free", "credits": 0, "api_quota": 0,
            "subscription_days_remaining": 0,
        }

    user = _MOCK_USERS[email]

    if tier:
        user["tier"] = tier
    if tier and duration_days:
        user["subscription_days_remaining"] = duration_days
    if credits:
        if product == "api":
            user["api_quota"] = user.get("api_quota", 0) + credits
        else:
            user["credits"] = user.get("credits", 0) + credits

    return copy.deepcopy(user)


def execute_create_account(email: str, tier: str, duration_days: int) -> dict[str, Any]:
    """Mock create account."""
    import uuid
    user = {
        "email": email,
        "user_id": f"usr_{uuid.uuid4().hex[:8]}",
        "space_id": f"spc_{uuid.uuid4().hex[:8]}",
        "tier": tier,
        "credits": 0,
        "api_quota": 0,
        "subscription_days_remaining": duration_days,
        "created": True,
    }
    _MOCK_USERS[email] = user
    return copy.deepcopy(user)


def lookup_user(email: str) -> dict[str, Any]:
    """Lookup user — read only."""
    return get_user_state(email)
