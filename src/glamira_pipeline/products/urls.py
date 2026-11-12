"""Disk-backed URL inventory and product-page evidence across event types."""
from __future__ import annotations

from html import unescape
import json
import os
import re
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

def product_path(path: str) -> bool:
    """Recognize observed .html paths and Magento catalog/product/view routes."""
    return (path.rstrip("/").lower().endswith(".html")
            or re.search(r"/catalog/product/view/id/[^/]+(?:/|$)", path) is not None)


def create_url_tables(connection: sqlite3.Connection) -> None:
    """Create inventory/evidence tables inside the extraction checkpoint."""
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS urls(
            url TEXT PRIMARY KEY, hostname TEXT, path TEXT, occurrences INTEGER);
        CREATE TABLE IF NOT EXISTS product_pages(
            hostname TEXT, path TEXT, id_field TEXT, product_id TEXT, store_id TEXT,
            PRIMARY KEY(hostname,path,id_field,product_id,store_id));
    """)


def collect_urls(connection: sqlite3.Connection, event: dict) -> dict[str, int]:
    """Count current_url for every event and record direct product evidence.

    Return aggregate URL counters. A product-shaped URL and an explicit
    product_id/viewing_product_id establish evidence regardless of event type;
    identifiers are never inferred from the URL or event name.
    """
    counts: dict[str, int] = {}
    raw = event.get("current_url")
    if raw is None or raw == "":
        return counts
    counts["current_url_references_seen"] = 1
    try:
        if not isinstance(raw, str) or any(ord(char) < 32 for char in raw):
            raise ValueError()
        url = unescape(raw)
        parsed = urlsplit(url)
        host = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            raise ValueError()
        parsed.port
    except ValueError:
        counts["invalid_current_urls"] = 1
        return counts
    connection.execute("""INSERT INTO urls VALUES(?,?,?,1)
            ON CONFLICT(url) DO UPDATE SET occurrences=occurrences+1""",
        (url, host.lower(), parsed.path))
    store = event.get("store_id")
    if product_path(parsed.path) and isinstance(store, str) and store.strip():
        for id_field in ("product_id", "viewing_product_id"):
            product = event.get(id_field)
            if isinstance(product, str) and product.strip():
                connection.execute("INSERT OR IGNORE INTO product_pages VALUES(?,?,?,?,?)",
                    (host.lower(), parsed.path, id_field, product, store))
    return counts


def export_urls(connection: sqlite3.Connection, directory: Path) -> dict[str, int]:
    """Stream evidence-backed product URLs and unverified product paths separately.

    Matching uses exact hostname/path, preserving URL query variants. Each
    appearance in current_url counts once; mappings include direct ID field.
    """
    totals: dict[str, int] = {}
    connection.create_function("product_path", 1, lambda path: int(product_path(path)), deterministic=True)
    for confirmed, filename in ((True, "product_urls.jsonl"), (False, "unverified_product_urls.jsonl")):
        path = directory / filename
        temporary = path.with_suffix(".jsonl.tmp")
        comparison = "EXISTS" if confirmed else "NOT EXISTS"
        query = f"""SELECT url,hostname,path,occurrences FROM urls u
            WHERE {comparison}(SELECT 1 FROM product_pages p
                WHERE p.hostname=u.hostname AND p.path=u.path)
            {' ' if confirmed else "AND product_path(u.path)=1"}
            ORDER BY url"""
        unique = occurrences = 0
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                os.chmod(temporary, 0o600)
                for url, host, page, count in connection.execute(query):
                    mappings = [{"id_field": id_field, "product_id": product, "store_id": store}
                        for id_field, product, store in connection.execute(
                        "SELECT id_field,product_id,store_id FROM product_pages WHERE hostname=? AND path=? ORDER BY id_field,product_id,store_id",
                        (host, page))]
                    row = {"source_url": url, "hostname": host, "occurrence_count": count,
                           "product_store_mappings": mappings,
                           "classification": "observed_product_page" if confirmed else "unverified_product_candidate"}
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    unique += 1
                    occurrences += count
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        prefix = "product_urls" if confirmed else "unverified_product_urls"
        totals[prefix + "_unique"] = unique
        totals[prefix + "_occurrences"] = occurrences
    totals["all_valid_urls_unique"] = connection.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
    return totals
