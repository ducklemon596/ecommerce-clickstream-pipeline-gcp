"""Upload a verified table export to GCS, finishing with the ``_load.json`` that triggers the load.

Object layout: ``<prefix>/<table>/export_id=<export-id>/`` holding the parts
under ``chunk=<id>/``, the two schema files, ``_manifest.json`` and, last,
``_load.json``. Only files the manifest lists are uploaded; local state files
(``_export.json``, ``.lock``, ``_SUCCESS.json``) stay local.

Every object is created with ``if_generation_match=0``, so nothing is ever
overwritten. If an object already exists, its CRC32C must equal the local
file's: a rerun skips what is already there, and a different object under the
same name stops the publish. GCS verifies each upload's CRC32C on arrival.
"""
from __future__ import annotations

import base64
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import time

from google.api_core.exceptions import PreconditionFailed
import google_crc32c

from glamira_pipeline.export.exporter import MANIFEST
from glamira_pipeline.export.schema import bigquery_schema
from glamira_pipeline.export.tables import TABLES
from glamira_pipeline.export.verify import verify_table
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LoadSpec, Source

LOGGER = logging.getLogger(__name__)


class PublishError(RuntimeError):
    """The export cannot be published: it failed verification or conflicts with objects in GCS."""


@dataclass(frozen=True)
class PublishResult:
    table: str
    load_spec: str
    uploaded: int
    skipped: int
    bytes_uploaded: int
    seconds: float


def object_prefix(prefix: str, table: str, export_id: str) -> str:
    return f"{prefix.strip('/')}/{table}/export_id={export_id}"


def build_load_spec(manifest: dict, bucket_name: str, base: str, dataset: str) -> LoadSpec:
    """The load spec of an exported table, from its manifest and the table contract."""
    table = TABLES[manifest["table"]]
    return LoadSpec(
        export_id=manifest["export_id"],
        table=table.name,
        dataset=dataset,
        rows=manifest["rows"],
        content_sha256=manifest["content_sha256"],
        sources=tuple(Source(f"gs://{bucket_name}/{base}/{part['name']}", part["bytes"])
                      for part in manifest["files"]),
        schema=tuple(bigquery_schema(table)),
        partition_by=table.partition_by,
        cluster_by=table.cluster_by,
    )


def publish_table(table_dir: Path, bucket, *, prefix: str, dataset: str, schema_dir: Path,
                  workers: int = 4, verify: Callable = verify_table) -> PublishResult:
    """Verify ``table_dir`` and upload it into ``bucket`` (a ``google.cloud.storage.Bucket``)."""
    started = time.monotonic()
    verify(table_dir, schema_dir)
    manifest = json.loads((table_dir / MANIFEST).read_text(encoding="utf-8"))
    table = manifest["table"]
    exported_bq = json.loads((table_dir / f"{table}.bq.json").read_text(encoding="utf-8"))
    if exported_bq != bigquery_schema(TABLES[table]):
        raise PublishError(f"{table}: the exported BigQuery schema differs from the contract in this checkout")
    base = object_prefix(prefix, table, manifest["export_id"])
    spec = build_load_spec(manifest, bucket.name, base, dataset)

    parts = [part["name"] for part in manifest["files"]]
    with ThreadPoolExecutor(max(1, workers)) as pool:
        outcomes = list(pool.map(lambda name: _upload_file(bucket, table_dir / name, f"{base}/{name}"), parts))
    for name in (f"{table}.avsc", f"{table}.bq.json", MANIFEST):
        outcomes.append(_upload_file(bucket, table_dir / name, f"{base}/{name}"))
    outcomes.append(_upload_text(bucket, spec.to_json(), f"{base}/{LOAD_SPEC}"))  # last: the commit and the trigger

    uploaded = [size for created, size in outcomes if created]
    result = PublishResult(table, f"gs://{bucket.name}/{base}/{LOAD_SPEC}", len(uploaded),
                           len(outcomes) - len(uploaded), sum(uploaded), round(time.monotonic() - started, 1))
    LOGGER.info("%s: %d objects uploaded (%s bytes), %d already present -> %s", table, result.uploaded,
                f"{result.bytes_uploaded:,}", result.skipped, result.load_spec)
    return result


def file_crc32c(path: Path) -> str:
    """Base64 big-endian CRC32C, the form GCS reports in ``Blob.crc32c``."""
    checksum = google_crc32c.Checksum()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            checksum.update(block)
    return base64.b64encode(checksum.digest()).decode("ascii")


def _upload_file(bucket, path: Path, name: str) -> tuple[bool, int]:
    blob = bucket.blob(name)
    try:
        blob.upload_from_filename(str(path), if_generation_match=0, checksum="crc32c")
        return True, path.stat().st_size
    except PreconditionFailed:
        blob.reload()
        if blob.crc32c != file_crc32c(path):
            raise PublishError(f"gs://{bucket.name}/{name} exists with other content; "
                               "use a new --export-id or remove the object deliberately") from None
        return False, 0


def _upload_text(bucket, text: str, name: str) -> tuple[bool, int]:
    blob = bucket.blob(name)
    data = text.encode("utf-8")
    try:
        blob.upload_from_string(data, content_type="application/json", if_generation_match=0, checksum="crc32c")
        return True, len(data)
    except PreconditionFailed:
        if blob.download_as_bytes() != data:
            raise PublishError(f"gs://{bucket.name}/{name} exists with another load spec") from None
        return False, 0
