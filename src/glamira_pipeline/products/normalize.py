"""Pure validation and URL configuration normalization."""
from __future__ import annotations

from html import unescape
import re
from urllib.parse import parse_qsl, urlsplit

TRACKING = frozenset({
    "gclid", "fbclid", "dclid", "msclkid", "gbraid", "wbraid", "ttclid",
    "keyword", "matchtype", "campaignid",
})
CONTROLS = frozenset({"no_cache"})
KNOWN_OPTIONS = frozenset({"alloy", "diamond", "stone", "stone2", "stone3",
                           "stone4", "pearl", "synthetic", "accent", "leather"})


class InvalidConfiguration(ValueError):
    """A rejected event with a safe aggregate reason, never raw URL contents."""


def is_tracking(key: str) -> bool:
    """Return whether a decoded query key belongs to the explicit exclusion policy."""
    key = key.lower()
    return key in TRACKING or key.startswith(("utm_", "itm_"))


def normalize_event(event: dict) -> tuple[dict, list[str]]:
    """Validate one detail event and return its configuration and warning codes.

    Uses URL values only, preserving case and decoded value text. Empty values
    are unspecified. Raises InvalidConfiguration for missing/invalid fields,
    malformed HTTP(S) URLs or distinct repeated nonempty values for one option.
    Use after filtering collection == view_product_detail.
    """
    for key in ("product_id", "store_id"):
        value = event.get(key)
        if value is None or value == "":
            raise InvalidConfiguration("missing_" + key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidConfiguration("invalid_" + key)
    raw_url = event.get("current_url")
    if raw_url is None or raw_url == "":
        raise InvalidConfiguration("missing_current_url")
    if not isinstance(raw_url, str):
        raise InvalidConfiguration("invalid_current_url")
    url = unescape(raw_url)
    if re.search(r"[\x00-\x20\x7f]", url) or re.search(r"%(?![0-9a-fA-F]{2})", url):
        raise InvalidConfiguration("malformed_url")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme not in {"http", "https"} or not host or "." not in host
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in {None, 80, 443}):
            raise ValueError("unsupported URL")
        pairs = parse_qsl(parsed.query, keep_blank_values=True, errors="strict", max_num_fields=256)
    except (ValueError, UnicodeError):
        raise InvalidConfiguration("malformed_url") from None
    options: dict[str, str] = {}
    warnings = []
    for key, value in pairs:
        if is_tracking(key):
            if "tracking_parameters_removed" not in warnings:
                warnings.append("tracking_parameters_removed")
            continue
        if key.lower() in CONTROLS or value == "":
            continue
        # Ambiguous separators are not repaired: doing so could invent an option.
        if not key or key[0] in ";?" or "/" in key:
            raise InvalidConfiguration("malformed_parameter")
        if key in options and options[key] != value:
            raise InvalidConfiguration("conflicting_option_values")
        options[key] = value
    if set(options) - KNOWN_OPTIONS:
        warnings.append("unknown_parameters_retained")
    option = event.get("option")
    if not isinstance(option, list) or any(not isinstance(item, dict) for item in option):
        warnings.append("option_validation_unavailable")
    else:
        labels = {item.get("option_label") for item in option if isinstance(item.get("option_label"), str)}
        if set(options) - labels:
            warnings.append("url_keys_not_in_option")
        # IDs are not URL labels; no mapping or website defaults are inferred.
        warnings.append("option_values_not_comparable")
    return {"product_id": event["product_id"], "store": event["store_id"],
            "store_id": event["store_id"], "hostname": host.lower(),
            "normalized_options": dict(sorted(options.items())), "source_url": url}, warnings
