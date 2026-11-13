"""Single-request HTTP access to the public product ``react_data`` endpoint.

Requests identify themselves with a plain, honest User-Agent and are never
disguised as a browser. A block or challenge is reported as ``blocked`` so the
caller can stop; this module never retries.
"""
from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER_AGENT = "glamira-pipeline/0.1"
BLOCK_STATUSES = frozenset({401, 403, 429})


@dataclass(frozen=True)
class FetchResult:
    """Outcome of one request; ``payload`` is set only for ``ok``."""

    status: str  # ok | not_found | blocked | error
    url: str
    http_status: int | None
    elapsed_s: float
    response_bytes: int
    payload: dict | None = None
    raw: bytes | None = None
    error: str | None = None


def react_data_url(host: str, product_id: str, currency: str) -> str:
    """Build the endpoint URL; robots.txt allows ``/productcustomizer/reactdata/``."""
    if not product_id.isdigit():
        raise ValueError("product_id must be numeric")
    return f"https://{host}/productcustomizer/reactdata/index/id/{product_id}/?currency={quote(currency)}"


def classify(http_status: int | None, content_type: str, body: bytes) -> tuple[str, dict | None]:
    """Map an HTTP response to a crawl status and parsed JSON payload.

    ``404`` with the site's JSON error means the product does not exist on that
    store. Any non-JSON 200 (for example an HTML challenge page) is ``blocked``.
    """
    if http_status in BLOCK_STATUSES:
        return "blocked", None
    is_json = "json" in content_type.lower()
    if http_status == 404:
        return ("not_found", None) if is_json else ("error", None)
    if http_status != 200:
        return "error", None
    if not is_json:
        return "blocked", None
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "error", None
    if not isinstance(payload, dict) or "product_id" not in payload:
        return "error", None
    return "ok", payload


def fetch(url: str, *, timeout_s: float = 30.0) -> FetchResult:
    """GET one URL with gzip transfer encoding and classify the response."""
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                    "Accept-Encoding": "gzip"})
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout_s) as response:
            http_status, headers, wire = response.status, response.headers, response.read()
    except HTTPError as exc:
        http_status, headers, wire = exc.code, exc.headers, exc.read()
    except (URLError, TimeoutError, ConnectionError) as exc:
        return FetchResult("error", url, None, round(time.monotonic() - started, 3), 0,
                           error=type(exc).__name__ + ": " + str(getattr(exc, "reason", exc)))
    elapsed = round(time.monotonic() - started, 3)
    try:
        body = gzip.decompress(wire) if headers.get("Content-Encoding") == "gzip" else wire
    except (OSError, EOFError):
        return FetchResult("error", url, http_status, elapsed, len(wire), error="bad gzip body")
    status, payload = classify(http_status, headers.get("Content-Type", ""), body)
    return FetchResult(status, url, http_status, elapsed, len(wire), payload=payload,
                       raw=body if status == "ok" else None)
