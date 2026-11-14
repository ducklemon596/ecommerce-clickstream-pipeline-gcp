"""Load a BSON member of a ``.tar.gz`` dump into MongoDB: streamed, parallel, resumable.

Data flow: ``tar``+``pigz`` (or ``tarfile``) → length-prefix batches (main
thread) → ``insert_many`` of raw BSON on N worker threads. Every completed
batch advances a watermark that is checkpointed to ``load_runs``; a rerun with
the same source and batch limits skips batches below it and relies on
duplicate-key errors for the few batches that were in flight.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
import logging
from pathlib import Path
import signal
import threading
import time

from pymongo.collection import Collection
from pymongo.database import Database

from glamira_pipeline.load.bson_stream import Batch, iter_batches, open_member
from glamira_pipeline.load.checkpoint import RunStore, Watermark
from glamira_pipeline.load.metrics import LoadMetrics
from glamira_pipeline.load.writer import insert_batch
from glamira_pipeline.provenance import file_sha256, git_sha

LOGGER = logging.getLogger(__name__)
CHECKPOINT_EVERY_S = 30

# Lenient on purpose: only fields every event type has (measured in the Phase 0
# reports). "warn" logs violations in the mongod log instead of rejecting them.
SUMMARY_VALIDATOR = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "collection", "time_stamp"],
    "properties": {
        "collection": {"bsonType": "string"},
        "time_stamp": {"bsonType": ["int", "long", "double"]},
    },
}}


class LoadError(RuntimeError):
    """The load cannot start or did not finish correctly; the message says why."""


class LoadInterrupted(LoadError):
    """Stopped by a signal after in-flight batches finished and the checkpoint was saved."""


@dataclass(frozen=True)
class LoadOptions:
    """Tuning knobs; ``batch_docs`` and ``max_batch_bytes`` define batch boundaries for resume."""

    workers: int = 4
    batch_docs: int = 1_000
    max_batch_bytes: int = 16 * 1024 * 1024
    pigz: bool | None = None
    validator: str = "warn"  # "warn" or "off"; applied only when the target is created


@dataclass
class Progress:
    """Counters persisted in the run document; ``batches_done`` is the resume watermark."""

    batches_done: int = 0
    offset: int = 0
    docs_seen: int = 0
    docs_skipped: int = 0
    docs_sent: int = 0
    inserted: int = 0
    duplicates: int = 0

    def as_dict(self) -> dict:
        return dict(vars(self))


class _StopFlag:
    """First SIGINT/SIGTERM/SIGHUP requests a graceful stop; a repeat after 2 s aborts.

    Repeats within 2 s are ignored because ``uv run`` and the terminal can both
    deliver one Ctrl+C. SIGHUP arrives when the SSH session on the VM drops.
    """

    SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)

    def __init__(self) -> None:
        self.reason: str | None = None
        self._first = 0.0
        self._previous: dict = {}

    def __enter__(self) -> "_StopFlag":
        if threading.current_thread() is threading.main_thread():
            for signum in self.SIGNALS:
                self._previous[signum] = signal.signal(signum, self._handle)
        return self

    def __exit__(self, *exc) -> None:
        for signum, handler in self._previous.items():
            signal.signal(signum, handler)

    def _handle(self, signum: int, _frame) -> None:
        name = signal.Signals(signum).name
        if self.reason is None:
            self.reason, self._first = f"interrupted ({name})", time.monotonic()
            LOGGER.warning("%s received: finishing in-flight batches; repeat to abort", name)
        elif time.monotonic() - self._first > 2:
            raise KeyboardInterrupt


def _create_target(db: Database, name: str, validator: str) -> None:
    if validator == "warn":
        db.create_collection(name, validator=SUMMARY_VALIDATOR, validationLevel="strict",
                             validationAction="warn")
    else:
        db.create_collection(name)


def _collection_uuid(db: Database, name: str) -> str | None:
    info = next(db.list_collections(filter={"name": name}), None)
    uuid = info and info.get("info", {}).get("uuid")
    return bytes(uuid).hex() if uuid else None


def load_summary(archive: Path, member: str, db: Database, collection: str,
                 options: LoadOptions = LoadOptions()) -> dict:
    """Load ``member`` of ``archive`` into ``db[collection]`` and return the finished run document.

    Refuses a non-empty target unless resuming a run with the same identity
    (archive SHA-256, member, target, batch limits); never drops or replaces
    data. Raises LoadError when it cannot start or the final count does not
    match the source, and LoadInterrupted after a graceful stop.
    """
    metrics = LoadMetrics()
    started = time.perf_counter()
    source_sha = file_sha256(archive)
    metrics.hash_s = time.perf_counter() - started

    store = RunStore(db)
    namespace = f"{db.name}.{collection}"
    identity = {"source_sha256": source_sha, "member": member, "target": namespace,
                "batch_docs": options.batch_docs, "max_batch_bytes": options.max_batch_bytes}
    store.check_lock(namespace)
    previous = store.latest(identity)
    if previous and previous["status"] == "completed":
        LOGGER.info("already loaded by run %s; nothing to do", previous["_id"])
        return previous  # rerunning a finished load is a no-op, not an error

    exists = collection in db.list_collection_names()
    target_uuid = _collection_uuid(db, collection) if exists else None
    if previous:
        if previous["target"].get("uuid") != target_uuid:
            raise LoadError("target was dropped or recreated since the previous run; resume is unsafe")
        progress = Progress(batches_done=previous["progress"]["batches_done"],
                            offset=previous["progress"]["offset"])
        LOGGER.info("resuming run %s from batch %s", previous["_id"], f"{progress.batches_done:,}")
    else:
        if exists and db[collection].estimated_document_count():
            raise LoadError(f"{namespace} already has documents and no resumable run matches this source")
        if not exists:
            _create_target(db, collection, options.validator)
            target_uuid = _collection_uuid(db, collection)
        progress = Progress()

    run_id = store.start(
        identity,
        source={"archive": archive.name, "bytes": archive.stat().st_size, "sha256": source_sha, "member": member},
        target={"namespace": namespace, "uuid": target_uuid},
        params={"workers": options.workers, "batch_docs": options.batch_docs,
                "max_batch_bytes": options.max_batch_bytes, "pigz": options.pigz, "validator": options.validator},
        resumed_from=previous["_id"] if previous else None, progress=progress.as_dict(), git_sha=git_sha())
    LOGGER.info("run %s: loading %s → %s with %d workers", run_id, archive.name, namespace, options.workers)

    target = db[collection]
    try:
        _stream_into(archive, member, target, options, progress, metrics, store, run_id)
    except LoadInterrupted as exc:
        store.finish(run_id, "stopped", progress.as_dict(), metrics.close(progress.docs_seen), str(exc))
        raise
    except BaseException as exc:
        store.finish(run_id, "failed", progress.as_dict(), metrics.close(progress.docs_seen),
                     f"{type(exc).__name__}: {exc}")
        raise

    started = time.perf_counter()
    stored = target.estimated_document_count()
    metrics.finalize_s = time.perf_counter() - started
    error = None
    if progress.docs_seen != progress.docs_skipped + progress.inserted + progress.duplicates:
        error = "every streamed document must be skipped, inserted or a duplicate"
    elif stored != progress.docs_seen:
        error = f"target holds {stored:,} documents but the source has {progress.docs_seen:,}"
    store.finish(run_id, "failed" if error else "completed", progress.as_dict(),
                 metrics.close(progress.docs_seen), error)
    run = store.runs.find_one({"_id": run_id})
    if error:
        raise LoadError(error)
    return run


def _stream_into(archive: Path, member: str, target: Collection, options: LoadOptions,
                 progress: Progress, metrics: LoadMetrics, store: RunStore, run_id: str) -> None:
    """Producer/consumer loop. Only the main thread touches ``progress`` and the watermark."""
    watermark = Watermark(progress.batches_done, progress.offset)
    resume_below = progress.batches_done
    pending: dict[Future, Batch] = {}
    last_checkpoint = time.monotonic()
    failure: BaseException | None = None

    def write(batch: Batch) -> tuple[int, int]:
        wall, cpu = time.perf_counter(), time.thread_time()
        result = insert_batch(target, batch.docs)
        metrics.record_insert(time.perf_counter() - wall, time.thread_time() - cpu)
        return result

    def collect(done: set[Future]) -> None:
        nonlocal failure
        for future in done:
            batch = pending.pop(future)
            try:
                inserted, duplicates = future.result()
            except Exception as exc:  # keep draining, then report the first failure
                failure = failure or exc
                continue
            progress.inserted += inserted
            progress.duplicates += duplicates
            watermark.complete(batch.index, batch.end_offset)
        progress.batches_done, progress.offset = watermark.next_index, watermark.offset

    def checkpoint() -> None:
        nonlocal last_checkpoint
        started = time.perf_counter()
        store.checkpoint(run_id, progress.as_dict())
        metrics.checkpoint_s += time.perf_counter() - started
        last_checkpoint = time.monotonic()

    with _StopFlag() as stop, ThreadPoolExecutor(options.workers, thread_name_prefix="insert") as pool, \
            open_member(archive, member, pigz=options.pigz) as reader:
        batches = iter_batches(reader, options.batch_docs, options.max_batch_bytes)
        while failure is None and stop.reason is None:
            produce_started, read_before = time.perf_counter(), reader.seconds
            batch = next(batches, None)
            read_spent = reader.seconds - read_before
            metrics.source_wait_s += read_spent
            metrics.split_s += time.perf_counter() - produce_started - read_spent
            if batch is None:
                break
            progress.docs_seen += len(batch.docs)
            # Checked for skipped batches too: skipping a long prefix on resume can take
            # minutes, and the heartbeat must stay younger than HEARTBEAT_TIMEOUT.
            if time.monotonic() - last_checkpoint >= CHECKPOINT_EVERY_S:
                checkpoint()
            if batch.index < resume_below:  # already in the target according to the checkpoint
                progress.docs_skipped += len(batch.docs)
                continue
            if len(pending) >= options.workers * 2:  # bounded memory: at most 2 batches per worker queued
                started = time.perf_counter()
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                metrics.slot_wait_s += time.perf_counter() - started
                collect(done)
            pending[pool.submit(write, batch)] = batch
            progress.docs_sent += len(batch.docs)
            metrics.record_progress(progress.docs_seen)
        # On a stop or failure the stream is left unread; open_member terminates the decompressor.
        if pending:
            collect(wait(pending).done)
        checkpoint()
    if failure is not None:
        raise failure
    if stop.reason is not None:
        raise LoadInterrupted(f"{stop.reason}; resume by rerunning the same command")
