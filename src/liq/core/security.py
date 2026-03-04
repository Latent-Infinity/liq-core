"""Credential-safe redaction and serialization helpers.

These utilities are shared across LIQ packages for deterministic, secret-aware
logging and persistence boundaries.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

REDACTED_SECRET_VALUE = "***REDACTED***"

SENSITIVE_CONTEXT_KEYS = (
    "api_key",
    "api_secret",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "private_key",
    "api_token",
)


def is_sensitive_key(key: str) -> bool:
    """Return ``True`` when a key name indicates credential-like content."""
    lowered = key.lower()
    return any(token in lowered for token in SENSITIVE_CONTEXT_KEYS)


def mask_sensitive_context(context: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Return a redacted mapping copy for diagnostics."""
    if context is None:
        return None
    return _redact_value(context)


def redact_sensitive_payload(payload: Any) -> Any:
    """Recursively replace sensitive values with ``REDACTED_SECRET_VALUE``."""
    return _redact_value(payload)


def serialize_sensitive_payload(payload: Any) -> bytes:
    """Serialize a payload to JSON while redacting sensitive values."""
    redacted = redact_sensitive_payload(payload)
    sanitized = _coerce_json_value(redacted)
    return json.dumps(
        sanitized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def hash_fingerprint(payload: Any) -> str:
    """Return a stable fingerprint for arbitrary payload diagnostics."""
    normalized = json.dumps(
        _coerce_json_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, raw in value.items():
            redacted_key = str(key)
            if is_sensitive_key(redacted_key):
                redacted[redacted_key] = REDACTED_SECRET_VALUE
            else:
                redacted[redacted_key] = _redact_value(raw)
        return redacted

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)

    if isinstance(value, (set, frozenset)):
        return [_redact_value(item) for item in sorted(value, key=repr)]

    return value


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _coerce_json_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_coerce_json_value(item) for item in value]

    if isinstance(value, tuple):
        return [_coerce_json_value(item) for item in value]

    if isinstance(value, (set, frozenset)):
        return [_coerce_json_value(item) for item in sorted(value, key=repr)]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", errors="replace")

    return str(value)
