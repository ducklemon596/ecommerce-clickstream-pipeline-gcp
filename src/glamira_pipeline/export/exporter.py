"""Export one MongoDB collection to Avro parts plus a manifest.

Output layout, one directory per table::

    <output>/<table>/part-00000.avro ...   rows, deflate-compressed
    <output>/<table>/<table>.avsc          Avro schema the parts were written with
    <output>/<table>/<table>.bq.json       BigQuery schema of the target table
    <output>/<table>/_manifest.json        written last: its presence means "complete"

The export is a read-only cursor over the collection in natural order. It stops
at the first ``SchemaViolation``. A run never reuses an existing table
directory, so a failed or interrupted run is retried into a new one.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import time

from fastavro import reader as avro_reader
from pymongo.collection import Collection

from glamira_pipeline.export.avro_files import CODEC, AvroPartWriter, PartFile, part_dicts
from glamira_pipeline.export.convert import Converter, SchemaViolation, check_rules
from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.schema import Table, avro_schema, bigquery_schema, schema_fingerprint, schema_json
from glamira_pipeline.provenance import git_sha, mongo_collection_identity

LOGGER = logging.getLogger(__name__)
MANIFEST = "_manifest.json"
PROGRESS_EVERY = 1_000_000


class ExportError(RuntimeError):
    """The export did not complete; the message says why. Partial parts are left for inspection."""


class ExportInterrupted(ExportError):
    """Stopped by a signal; the open part was discarded and no manifest was written."""


@dataclass(frozen=True)
class ExportOptions:
    """``limit`` exports only the first N documents in natural order (a non-random sample)."""

    rows_per_file: int = 1_000_000
    limit: int | None = None
    batch_size: int = 10_000


def write_schema_files(table: Table, directory: Path) -> None:
    """Write ``<table>.avsc`` and ``<table>.bq.json`` into ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{table.name}.avsc").write_text(schema_json(avro_schema(table)), encoding="utf-8")
    (directory / f"{table.name}.bq.json").write_text(schema_json(bigquery_schema(table)), encoding="utf-8")


def export_table(table: Table, collection: Collection, output_root: Path, hasher: PiiHasher,
                 options: ExportOptions = ExportOptions(),
                 should_stop: Callable[[], bool] = lambda: False) -> dict:
    """Export ``collection`` as ``table`` under ``output_root``; return the manifest.

    A full export (no ``limit``) must write exactly as many rows as the
    collection holds before and after the scan, otherwise ExportError.
    """
    check_rules(table)
    target = output_root / table.name
    target.mkdir(parents=True, exist_ok=False)  # never mix two runs in one directory
    write_schema_files(table, target)

    source = mongo_collection_identity(collection)
    count_before = collection.estimated_document_count()
    converter = Converter(table, hasher)
    writer = AvroPartWriter(target, avro_schema(table), rows_per_file=options.rows_per_file)
    started_at, started = datetime.now(timezone.utc), time.monotonic()
    seconds = {"read": 0.0, "convert": 0.0, "write": 0.0}
    LOGGER.info("exporting %s -> %s (%s)", collection.full_name, target,
                f"first {options.limit:,} documents" if options.limit else "full collection")

    cursor = collection.find({}, batch_size=options.batch_size, limit=options.limit or 0)
    documents = 0
    clock = time.perf_counter
    try:
        while True:
            t0 = clock()
            document = next(cursor, None)
            t1 = clock()
            if document is None:
                seconds["read"] += t1 - t0
                break
            if should_stop():
                raise ExportInterrupted(f"interrupted after {documents:,} documents of {table.name}")
            documents += 1
            try:
                row = converter.convert(document)
            except SchemaViolation as exc:
                key = "" if table.sensitive_key else f" (_id {document.get('_id')})"
                raise ExportError(f"{table.name} document #{documents:,}{key}: {exc}") from None
            t2 = clock()
            writer.write(row)
            t3 = clock()
            seconds["read"] += t1 - t0
            seconds["convert"] += t2 - t1
            seconds["write"] += t3 - t2
            if documents % PROGRESS_EVERY == 0:
                LOGGER.info("%s: %s rows, %.0f rows/s", table.name, f"{documents:,}",
                            documents / (time.monotonic() - started))
        parts = writer.close()
    except BaseException:
        writer.abort()
        raise
    finally:
        cursor.close()

    count_after = collection.estimated_document_count()
    if options.limit is None and not documents == count_before == count_after:
        raise ExportError(f"{table.name}: wrote {documents:,} rows but the collection held "
                          f"{count_before:,} before and {count_after:,} after the scan")
    elapsed = time.monotonic() - started
    manifest = {
        "table": table.name,
        "status": "complete",
        "selection": (f"first {options.limit:,} documents in natural order (non-random)"
                      if options.limit else "full collection"),
        "source": {**source, "documents_before": count_before, "documents_after": count_after},
        "rows": documents,
        "files": part_dicts(parts),
        "bytes": sum(p.bytes for p in parts),
        "conversions": dict(sorted(converter.stats.items())),
        "avro_schema_sha256": schema_fingerprint(table),
        "pii_key_fingerprint": hasher.fingerprint(),
        "codec": CODEC,
        "rows_per_file": options.rows_per_file,
        "git_sha": git_sha(),
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "seconds": {**{k: round(v, 1) for k, v in seconds.items()}, "total": round(elapsed, 1)},
        "rows_per_second": round(documents / elapsed) if elapsed else None,
    }
    _write_json_atomic(target / MANIFEST, manifest)
    LOGGER.info("%s: %s rows in %d parts, %.0f s", table.name, f"{documents:,}", len(parts), elapsed)
    return manifest


def verify_export(directory: Path) -> dict:
    """Re-read every part of a finished export; check checksums, row counts and the writer schema."""
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    expected = json.loads((directory / f"{manifest['table']}.avsc").read_text(encoding="utf-8"))
    names = {expected["name"], f"{expected['namespace']}.{expected['name']}"}
    rows = 0
    for part in (PartFile(**p) for p in manifest["files"]):
        path = directory / part.name
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != part.sha256:
            raise ExportError(f"{part.name}: checksum differs from the manifest")
        with path.open("rb") as stream:
            part_reader = avro_reader(stream)
            if part_reader.writer_schema.get("name") not in names:
                raise ExportError(f"{part.name}: unexpected writer schema")
            count = sum(1 for _ in part_reader)
        if count != part.rows:
            raise ExportError(f"{part.name}: {count} rows, manifest says {part.rows}")
        rows += count
    if rows != manifest["rows"]:
        raise ExportError(f"{rows} rows in parts, manifest says {manifest['rows']}")
    return {"table": manifest["table"], "files": len(manifest["files"]), "rows": rows, "ok": True}


def _write_json_atomic(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, default=str)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
