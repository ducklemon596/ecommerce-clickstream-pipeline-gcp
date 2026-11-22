"""Export one MongoDB collection to Parquet parts: resumable, retry-safe and byte-deterministic.

Output layout, one directory per table inside an export directory::

    <export>/<table>/_export.json                  identity: the inputs of this export
    <export>/<table>/<table>.bq.json               BigQuery schema the parts were written from
    <export>/<table>/chunk=<id>/part-NNNNN.parquet rows of one chunk, sorted by _id
    <export>/<table>/chunk=<id>/_SUCCESS.json      chunk commit marker, written last
    <export>/<table>/_manifest.json                written when every chunk is committed

Rerunning the same command resumes: committed chunks are verified and
skipped, an uncommitted chunk is deleted and redone. Transient MongoDB errors
retry the open chunk with backoff. With ``workers > 1`` chunks run in parallel
processes (export/parallel.py) under the same protocol. Contract violations, count mismatches and
state inconsistencies stop the run. See docs/decisions/export_retry_idempotency.md.
``verify-export`` (export/verify.py) checks a finished export again later.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import random
import time

import pyarrow
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import AutoReconnect, CursorNotFound

from glamira_pipeline.export.chunks import Chunk, plan_chunks
from glamira_pipeline.export.convert import Converter, SchemaViolation, check_rules
from glamira_pipeline.export.parallel import ChunkJob, export_chunks_in_processes
from glamira_pipeline.export.parquet_files import COMPRESSION, FORMAT_VERSION, ROW_GROUP_ROWS, ParquetPartWriter, \
    part_dicts
from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.schema import Table, bigquery_schema, parquet_schema, schema_fingerprint, schema_json
from glamira_pipeline.export.state import (claim_identity, commit_chunk, committed_chunk, exclusive_lock, read_json,
                                           reset_chunk, write_json_atomic)
from glamira_pipeline.provenance import git_sha, mongo_collection_identity

LOGGER = logging.getLogger(__name__)
MANIFEST = "_manifest.json"
# AutoReconnect covers NetworkTimeout and ServerSelectionTimeoutError.
TRANSIENT_ERRORS: tuple[type[Exception], ...] = (AutoReconnect, CursorNotFound)


class ExportError(RuntimeError):
    """The export did not complete; the message says why. Rerun the same command after fixing the cause."""


class ExportInterrupted(ExportError):
    """Stopped by a signal; the open chunk stays uncommitted and is redone on the next run."""


@dataclass(frozen=True)
class ExportOptions:
    """``limit`` exports only the first N documents by ``_id`` (a non-random sample).

    ``workers`` processes export chunks in parallel; the output does not
    depend on it, so it is not part of the export identity.
    """

    rows_per_file: int = 1_000_000
    row_group_rows: int = ROW_GROUP_ROWS
    workers: int = 1
    limit: int | None = None
    batch_size: int = 10_000
    max_attempts: int = 3
    backoff_seconds: float = 5.0


def write_schema_files(table: Table, directory: Path) -> None:
    """Write ``<table>.bq.json``, the BigQuery schema the Parquet schema is derived from, into ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{table.name}.bq.json").write_text(schema_json(bigquery_schema(table)), encoding="utf-8")


def export_table(table: Table, collection: Collection, export_dir: Path, hasher: PiiHasher,
                 options: ExportOptions = ExportOptions(),
                 should_stop: Callable[[], bool] = lambda: False,
                 sleep: Callable[[float], None] = time.sleep,
                 connect: Callable[[], MongoClient] | None = None) -> dict:
    """Export ``collection`` as ``table`` into ``export_dir/<table>``, resuming earlier attempts; return the manifest.

    ``connect`` opens a new client in each worker process. It must be
    picklable (a module-level function or a ``functools.partial``) and is
    required when ``options.workers > 1``.
    """
    check_rules(table)
    if options.workers > 1 and connect is None:
        raise ValueError("connect is required when workers > 1")
    run_started = time.monotonic()
    target = export_dir / table.name
    with exclusive_lock(target):
        source = mongo_collection_identity(collection)
        chunks, expected = plan_chunks(table, collection, options.limit)
        identity = {
            "table": table.name,
            "selection": _selection(options),
            "source": {"namespace": source["namespace"], "uuid": source["uuid"]},
            "chunks": [{**chunk.describe(), "documents": expected[chunk.id]} for chunk in chunks],
            "schema_sha256": schema_fingerprint(table),
            "pii_key_fingerprint": hasher.fingerprint(),
            "format": f"parquet {FORMAT_VERSION}, {COMPRESSION}",
            "rows_per_file": options.rows_per_file,
            "row_group_rows": options.row_group_rows,
            "pyarrow": pyarrow.__version__,
        }
        stored = claim_identity(target, identity, {"created_at": _now(), "git_sha": git_sha(),
                                                   "endpoint": source["endpoint"]})
        manifest = read_json(target / MANIFEST)
        if manifest is not None:
            LOGGER.info("%s: already complete (%s rows); nothing to do", table.name, f"{manifest['rows']:,}")
            return manifest
        write_schema_files(table, target)
        workers = min(options.workers, len(chunks)) or 1
        LOGGER.info("exporting %s -> %s: %d chunks, %s documents (%s), %d worker(s)", collection.full_name, target,
                    len(chunks), f"{sum(expected.values()):,}", identity["selection"], workers)
        if workers > 1:
            job = ChunkJob(table, collection.database.name, collection.name, target, hasher, options)
            markers = export_chunks_in_processes(job, chunks, expected, workers, connect, should_stop)
        else:
            exporter = ChunkExporter(table, collection, target, hasher, options, should_stop=should_stop, sleep=sleep)
            markers = [exporter.run(chunk, expected[chunk.id]) for chunk in chunks]
        manifest = _manifest(table, export_dir.name, stored, markers, hasher)
        manifest["workers"] = workers
        manifest["wall_seconds"] = round(time.monotonic() - run_started, 1)
        if manifest["rows"] != sum(expected.values()):
            raise ExportError(f"{table.name}: chunks hold {manifest['rows']:,} rows, "
                              f"the plan expected {sum(expected.values()):,}")
        write_json_atomic(target / MANIFEST, manifest)
        LOGGER.info("%s: complete, %s rows in %d parts", table.name, f"{manifest['rows']:,}", len(manifest["files"]))
        return manifest


class ChunkExporter:
    """Export and commit one chunk at a time; retry transient MongoDB errors with backoff."""

    def __init__(self, table: Table, collection: Collection, target: Path, hasher: PiiHasher,
                 options: ExportOptions, *, should_stop: Callable[[], bool] = lambda: False,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.table, self.collection, self.target, self.hasher = table, collection, target, hasher
        self.options, self.should_stop, self.sleep = options, should_stop, sleep
        self.schema = parquet_schema(bigquery_schema(table))

    def run(self, chunk: Chunk, expected: int) -> dict:
        directory = self.target / chunk.directory
        marker = committed_chunk(directory)
        if marker is not None:
            LOGGER.info("%s %s: committed, verified, skipped", self.table.name, chunk.directory)
            return marker
        for attempt in range(1, self.options.max_attempts + 1):
            removed = reset_chunk(directory)
            if removed:
                LOGGER.info("%s %s: removed %d uncommitted files", self.table.name, chunk.directory, removed)
            try:
                return self._write(chunk, expected, directory, attempt)
            except TRANSIENT_ERRORS as exc:
                if attempt == self.options.max_attempts:
                    raise ExportError(f"{self.table.name} {chunk.directory}: {type(exc).__name__} after "
                                      f"{attempt} attempts: {exc}") from exc
                delay = self.options.backoff_seconds * (2 ** (attempt - 1) + random.random())
                LOGGER.warning("%s %s: attempt %d failed (%s: %s); retrying in %.1f s", self.table.name,
                               chunk.directory, attempt, type(exc).__name__, exc, delay)
                if self.should_stop():
                    raise ExportInterrupted(f"interrupted while retrying {chunk.directory}") from exc
                self.sleep(delay)
        raise AssertionError("unreachable")

    def _count(self, chunk: Chunk) -> int:
        if chunk.lower is not None:
            return self.collection.count_documents(chunk.query)
        count = self.collection.estimated_document_count()
        return count if chunk.limit is None else min(count, chunk.limit)

    def _write(self, chunk: Chunk, expected: int, directory: Path, attempt: int) -> dict:
        count_before = self._count(chunk)
        if count_before != expected:
            raise ExportError(f"{self.table.name} {chunk.directory}: {count_before:,} documents now, "
                              f"{expected:,} when the export was planned; the source changed")
        converter = Converter(self.table, self.hasher)
        writer = ParquetPartWriter(directory, self.schema, rows_per_file=self.options.rows_per_file,
                                   row_group_rows=self.options.row_group_rows)
        cursor = self.collection.find(chunk.query, sort=[("_id", 1)], batch_size=self.options.batch_size,
                                      limit=chunk.limit or 0)
        seconds = {"read": 0.0, "convert": 0.0, "write": 0.0}
        rows, first_id, last_id = 0, None, None
        clock = time.perf_counter
        try:
            while True:
                t0 = clock()
                document = next(cursor, None)
                t1 = clock()
                seconds["read"] += t1 - t0
                if document is None:
                    break
                if self.should_stop():
                    raise ExportInterrupted(f"interrupted in {self.table.name} {chunk.directory} after {rows:,} rows")
                rows += 1
                try:
                    row = converter.convert(document)
                except SchemaViolation as exc:
                    key = "" if self.table.sensitive_key else f" (_id {document.get('_id')})"
                    raise ExportError(f"{self.table.name} {chunk.directory} document #{rows:,}{key}: {exc}") from None
                t2 = clock()
                writer.write(row)
                seconds["convert"] += t2 - t1
                seconds["write"] += clock() - t2
                if first_id is None:
                    first_id = document["_id"]
                last_id = document["_id"]
            parts = writer.close()
        except pyarrow.ArrowException as exc:  # the converter checks types first, so this is a contract/code mismatch
            writer.abort()
            raise ExportError(f"{self.table.name} {chunk.directory}: Parquet rejected a row group: {exc}") from exc
        except BaseException:
            writer.abort()
            raise
        finally:
            cursor.close()
        count_after = self._count(chunk)
        if not rows == count_before == count_after:
            raise ExportError(f"{self.table.name} {chunk.directory}: wrote {rows:,} rows but the range held "
                              f"{count_before:,} before and {count_after:,} after the read")
        marker = {
            "chunk": chunk.id,
            "rows": rows,
            "first_id": None if self.table.sensitive_key else first_id,
            "last_id": None if self.table.sensitive_key else last_id,
            "files": part_dicts(parts),
            "conversions": dict(sorted(converter.stats.items())),
            "seconds": {k: round(v, 2) for k, v in seconds.items()},
            "attempt": attempt,
            "committed_at": _now(),
        }
        commit_chunk(directory, marker)
        LOGGER.info("%s %s: committed %s rows in %d parts (%.1f s)", self.table.name, chunk.directory,
                    f"{rows:,}", len(parts), sum(seconds.values()))
        return marker


def _manifest(table: Table, export_id: str, stored: dict, markers: list[dict], hasher: PiiHasher) -> dict:
    identity, recorded = stored["identity"], stored["recorded"]
    files = [{**part, "name": f"chunk={marker['chunk']}/{part['name']}"}
             for marker in markers for part in marker["files"]]
    conversions: Counter = Counter()
    seconds: Counter = Counter()
    for marker in markers:
        conversions.update(marker["conversions"])
        seconds.update(marker["seconds"])
    rows = sum(marker["rows"] for marker in markers)
    work = sum(seconds.values())
    return {
        "table": table.name,
        "export_id": export_id,
        "status": "complete",
        "selection": identity["selection"],
        "source": {**identity["source"], "documents": sum(c["documents"] for c in identity["chunks"])},
        "rows": rows,
        "chunks": [{"id": m["chunk"], "rows": m["rows"], "files": len(m["files"]), "attempt": m["attempt"]}
                   for m in markers],
        "files": files,
        "bytes": sum(part["bytes"] for part in files),
        "content_sha256": content_sha256(files),
        "conversions": dict(sorted(conversions.items())),
        "schema_sha256": identity["schema_sha256"],
        "pii_key_fingerprint": hasher.fingerprint(),
        "format": identity["format"],
        "rows_per_file": identity["rows_per_file"],
        "row_group_rows": identity["row_group_rows"],
        "git_sha": git_sha(),
        "started_at": recorded["created_at"],
        "finished_at": _now(),
        "seconds": {**{k: round(v, 1) for k, v in sorted(seconds.items())}, "total": round(work, 1)},
        "rows_per_second": round(rows / work) if work else None,
    }


def content_sha256(files: list[dict]) -> str:
    """Identity of an export's content: SHA-256 over the sorted part names and their SHA-256.

    Unlike the manifest's own hash it ignores timestamps, so two exports with
    the same bytes share it (used for the deterministic BigQuery job ID).
    """
    lines = sorted(f"{part['name']} {part['sha256']}" for part in files)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _selection(options: ExportOptions) -> str:
    if options.limit:
        return f"first {options.limit:,} documents by _id (non-random sample)"
    return "full collection"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
