"""Normalize addresses and query an IP2Location BIN without network access."""
from __future__ import annotations

from datetime import date
import ipaddress
from pathlib import Path
import struct

import IP2Location


def bin_metadata(path: Path) -> dict:
    """Read BIN edition, date and IPv6 support from path; reject an invalid header."""
    with path.open("rb") as stream:
        header = stream.read(64)
    if len(header) < 64 or not 1 <= header[0] <= 26 or header[1] < 2:
        raise ValueError("invalid IP2Location BIN header")
    version_date = date(2000 + header[2], header[3], header[4]).isoformat()
    return {"edition": header[0], "date": version_date,
            "ipv6_supported": struct.unpack_from("<I", header, 13)[0] > 0}


def event_address(event: dict) -> tuple[str, str | None, int | None]:
    """Classify an event IP and return (category, normalized address, version).

    Reads only the `ip` field. Invalid and absent values return no address;
    valid addresses are canonicalized for deduplication.
    """
    if "ip" not in event:
        return "missing", None, None
    value = event["ip"]
    if value is None:
        return "null", None, None
    if not isinstance(value, str):
        return "invalid_type", None, None
    if not value.strip():
        return "empty", None, None
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return "invalid_format", None, None
    return "valid", str(address), address.version


def lookup_address(reader: IP2Location.IP2Location, address: str, ipv6_supported: bool) -> dict:
    """Return a status and location for one normalized IP using an open BIN reader.

    Use after normalization. Unavailable fields become None; lookup failures are
    recorded without exposing the input address in an exception or log.
    """
    ip = ipaddress.ip_address(address)
    result = {"status": None, "country_code": None, "country_name": None, "region": None, "city": None}
    if ip.version == 6 and not ipv6_supported:
        result["status"] = "unsupported_ipv6"
    elif not ip.is_global:
        result["status"] = "not_public"
    else:
        try:
            record = reader.get_all(address)
            code = getattr(record, "country_short", None)
            if not isinstance(code, str) or len(code) != 2 or not code.isascii() or not code.isalpha():
                result["status"] = "no_match"
            else:
                result["status"] = "resolved"
                result["country_code"] = code.upper()
                for target, attribute in (("country_name", "country_long"), ("region", "region"), ("city", "city")):
                    value = getattr(record, attribute, None)
                    result[target] = value if isinstance(value, str) and value.strip() not in {"", "-"} else None
        except Exception:
            result["status"] = "lookup_failed"
    return result
