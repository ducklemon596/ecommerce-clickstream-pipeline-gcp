"""Keyed pseudonymization of personal identifiers (email, device ID, IP).

HMAC-SHA256 with a secret key, not a plain hash: emails and IPv4 addresses are
guessable, so a plain hash could be reversed by hashing candidate values. The
same key must be used for every export so hashes stay joinable across tables
and runs; it is read from the environment and never written anywhere.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import hmac
import os

from glamira_pipeline.ip_location.lookup import event_address

KEY_ENV = "GLAMIRA_PII_HASH_KEY"
MIN_KEY_BYTES = 32
_FINGERPRINT_MESSAGE = b"glamira-pii-key-fingerprint/v1"


class PiiHasher:
    """Hash identifiers with one secret key; ``""`` and ``None`` pass through unchanged."""

    def __init__(self, key: bytes) -> None:
        if len(key) < MIN_KEY_BYTES:
            raise ValueError(f"PII hash key must be at least {MIN_KEY_BYTES} bytes")
        self._key = key

    def digest(self, value: str) -> str:
        """Return the 64-char hex HMAC-SHA256 of ``value`` (UTF-8)."""
        return hmac.new(self._key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    def text(self, value: str | None) -> str | None:
        """Hash an opaque identifier exactly as stored."""
        return value if not value else self.digest(value)

    def email(self, value: str | None) -> str | None:
        """Hash an email after trimming and lower-casing, so case variants match."""
        return value if not value else self.digest(value.strip().lower())

    def ip(self, value: str | None) -> tuple[str | None, bool]:
        """Hash an IP in canonical form; return ``(hash, was_valid)``.

        Canonical form (``ipaddress``) is what ``ip_locations`` is keyed on, so
        the two hashes join. An unparseable value is hashed as stored.
        """
        if not value:
            return value, True
        category, normalized, _ = event_address({"ip": value})
        if category == "valid":
            return self.digest(normalized), True
        return self.digest(value), False

    def fingerprint(self) -> str:
        """A short key identifier for manifests: equal fingerprints mean joinable hashes."""
        return hmac.new(self._key, _FINGERPRINT_MESSAGE, hashlib.sha256).hexdigest()[:16]


def hasher_from_env(env: Mapping[str, str] = os.environ) -> PiiHasher:
    """Build a hasher from ``GLAMIRA_PII_HASH_KEY`` (hex); raise ValueError if unset or invalid."""
    raw = env.get(KEY_ENV)
    if not raw:
        raise ValueError(f"set {KEY_ENV} to a hex key of at least {MIN_KEY_BYTES} bytes "
                         "(e.g. python -c 'import secrets; print(secrets.token_hex(32))')")
    try:
        key = bytes.fromhex(raw.strip())
    except ValueError:
        raise ValueError(f"{KEY_ENV} must be hexadecimal") from None
    return PiiHasher(key)
