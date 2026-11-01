"""Count duplicate identifiers and IP/timestamp pairs without retaining raw IPs."""
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import ipaddress
import re
from typing import Any

from bson import BSON

EVENT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,80}$")


def _digest(value: dict[str, Any]) -> bytes:
    """Return a type-aware SHA-256 digest for a BSON-encodable mapping.

    Args:
        value: Identifier or IP/timestamp mapping to encode as BSON.

    Returns:
        Digest bytes for in-memory duplicate keys; raw values are not retained.

    Raises:
        bson.errors.InvalidDocument: If a value cannot be encoded as BSON.
    """
    return hashlib.sha256(BSON.encode(value)).digest()


def ip_value(document: dict[str, Any]) -> tuple[str, Any]:
    """Return the IP field name and value from one event, preferring `ip`.

    Args:
        document: One decoded event document.

    Returns:
        The chosen field name and value, or `("missing", None)` if absent.
        Use this shared selection rule for both IP and duplicate checks.
    """
    if "ip" in document:
        return "ip", document["ip"]
    if "user_ip" in document:
        return "user_ip", document["user_ip"]
    return "missing", None


def classify_ip(value: str) -> str:
    """Return `ipv4`, `ipv6`, or `invalid` for an IP string after trimming spaces.

    Args:
        value: An IP address string, optionally surrounded by whitespace.

    Returns:
        `ipv4`, `ipv6`, or `invalid`. Use only for format classification.

    The original string remains the duplicate
    key, so equivalent spellings are not silently merged. IPv4-mapped IPv6
    addresses are classified as IPv6 by Python's `ipaddress` library.
    """
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return "invalid"
    return "ipv4" if address.version == 4 else "ipv6"


def duplicate_summary(values: Counter[bytes]) -> tuple[int, int]:
    """Return `(groups, excess_rows)` from a counter keyed by digests.

    Args:
        values: Occurrence counts keyed by identifier or pair digest.

    Returns:
        Duplicate group count and excess row count, excluding first occurrences.
    """
    return sum(count > 1 for count in values.values()), sum(count - 1 for count in values.values() if count > 1)


def _event_name(document: dict[str, Any]) -> str:
    """Return a safe `collection` label or invalid-label marker for one event document."""
    value = document.get("collection")
    return value if isinstance(value, str) and EVENT_NAME.fullmatch(value) else "<missing or invalid event type>"


@dataclass
class DuplicateCounts:
    """Maintain type-aware digest counts and aggregate repeated-pair classifications."""

    mongo_ids: Counter[bytes] = field(default_factory=Counter)
    pairs: Counter[bytes] = field(default_factory=Counter)
    mongo_id_usable: int = 0
    pair_usable: int = 0
    first_events: dict[bytes, str] = field(default_factory=dict)
    duplicate_first_events: dict[bytes, str] = field(default_factory=dict)
    mixed_event_groups: set[bytes] = field(default_factory=set)
    pair_versions: dict[bytes, str] = field(default_factory=dict)

    def observe(self, document: dict[str, Any]) -> None:
        """Update counters from one decoded event document; return no value.

        Args:
            document: One decoded BSON-compatible event document.

        Returns:
            None. Only usable `_id` and `(ip, time_stamp)` values are counted.
            Raw IPs are hashed immediately; classifications are retained only
            for repeated pairs. BSON encoding errors propagate to the caller.
        """
        value = document.get("_id")
        if value is not None and not (isinstance(value, str) and not value.strip()):
            self.mongo_ids[_digest({"value": value})] += 1
            self.mongo_id_usable += 1
        _, ip = ip_value(document)
        timestamp = document.get("time_stamp")
        if not isinstance(ip, str) or not ip.strip() or timestamp is None:
            return
        # Hash the original IP spelling and BSON timestamp before classification.
        key = _digest({"ip": ip, "timestamp": timestamp})
        self.pairs[key] += 1
        self.pair_usable += 1
        count = self.pairs[key]
        event = _event_name(document)
        if count == 1:
            self.first_events[key] = event
            return
        if count == 2:
            first = self.first_events.pop(key)
            self.duplicate_first_events[key] = first
            self.pair_versions[key] = classify_ip(ip)
        else:
            first = self.duplicate_first_events[key]
        if first != event:
            self.mixed_event_groups.add(key)
