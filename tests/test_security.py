"""Tests for credential redaction and safe serialization helpers."""

from __future__ import annotations

import json

from liq.core.security import (
    REDACTED_SECRET_VALUE,
    hash_fingerprint,
    is_sensitive_key,
    mask_sensitive_context,
    redact_sensitive_payload,
    serialize_sensitive_payload,
)


def test_is_sensitive_key_detects_common_variants() -> None:
    assert is_sensitive_key("api_key")
    assert is_sensitive_key("api_secret")
    assert is_sensitive_key("access_token")
    assert is_sensitive_key("private_key")
    assert not is_sensitive_key("payload")


def test_mask_sensitive_context_masks_nested_secret_keys() -> None:
    source = {
        "api_key": "abc",
        "model": "xgboost",
        "nested": {
            "run_token": "secret-run",
            "password": "pass",
            "ok": 1,
        },
        "items": [
            {"refresh_token": "rot"},
            ("access_token", "value"),
            {"value": "safe"},
        ],
        "plain": [1, 2, 3],
    }

    redacted = mask_sensitive_context(source)
    assert redacted is not None
    assert redacted["api_key"] == REDACTED_SECRET_VALUE
    assert redacted["model"] == "xgboost"
    assert redacted["nested"]["run_token"] == REDACTED_SECRET_VALUE
    assert redacted["nested"]["password"] == REDACTED_SECRET_VALUE
    assert redacted["nested"]["ok"] == 1
    assert redacted["items"][0]["refresh_token"] == REDACTED_SECRET_VALUE
    assert redacted["items"][1] == ("access_token", "value")


def test_redact_sensitive_payload_handles_sets_and_bytes() -> None:
    payload = {
        "api_token": "top-secret",
        "weights": {1, 2, 3},
        "blob": memoryview(b"abc"),
        "nested": {
            "token": b"hidden",
            "metric": "ok",
        },
    }
    redacted = redact_sensitive_payload(payload)

    assert redacted["api_token"] == REDACTED_SECRET_VALUE
    assert redacted["nested"]["token"] == REDACTED_SECRET_VALUE
    assert redacted["weights"] == [1, 2, 3]
    assert isinstance(redacted["blob"], memoryview)


def test_serialize_sensitive_payload_redacts_and_preserves_structure() -> None:
    payload = {
        "api_key": "secret-key",
        "config": {"secret_sauce": "dont-print", "model": "abc"},
        "set": {1, 3, 2},
    }
    serialized = serialize_sensitive_payload(payload)
    assert isinstance(serialized, bytes)

    loaded = json.loads(serialized.decode("utf-8"))
    assert loaded["api_key"] == REDACTED_SECRET_VALUE
    assert loaded["config"]["secret_sauce"] == REDACTED_SECRET_VALUE
    assert loaded["set"] == [1, 2, 3]
    assert loaded["config"]["model"] == "abc"


def test_serialize_sensitive_payload_handles_empty_and_none() -> None:
    assert json.loads(serialize_sensitive_payload({}).decode("utf-8")) == {}
    assert json.loads(serialize_sensitive_payload(None).decode("utf-8")) is None


def test_hash_fingerprint_is_stable_and_sensitive_to_change() -> None:
    first = hash_fingerprint({"a": 1, "b": [1, 2], "secret": "x"})
    second = hash_fingerprint({"b": [1, 2], "a": 1, "secret": "x"})
    third = hash_fingerprint({"a": 1, "b": [1, 3], "secret": "x"})

    assert first == second
    assert first != third
