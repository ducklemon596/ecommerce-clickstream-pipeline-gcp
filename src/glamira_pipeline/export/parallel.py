"""Run chunk exports in worker processes.

Conversion and Avro encoding are CPU-bound Python, so threads would share one
core; processes do not. Each worker opens its own ``MongoClient`` (a client
must not cross a fork, so workers are spawned) and exports whole chunks with
the same commit protocol as a single-process run. The parent only schedules
chunks and collects their markers; it writes the manifest after every chunk
is committed.

Stopping: workers ignore SIGINT. The parent polls ``should_stop`` and, on a
signal or the first failing chunk, sets a shared event that every worker
checks between documents. Running chunks then stop uncommitted, queued chunks
are cancelled, and committed chunks stay valid for the next run.
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass
import logging
import multiprocessing
from pathlib import Path
import signal
from typing import TYPE_CHECKING

from pymongo import MongoClient

from glamira_pipeline.export.chunks import Chunk
from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.schema import Table

if TYPE_CHECKING:
    from glamira_pipeline.export.exporter import ExportOptions

LOGGER = logging.getLogger(__name__)
POLL_SECONDS = 0.5
_WORKER = None  # the chunk exporter of this worker process, set by _initialize


@dataclass(frozen=True)
class ChunkJob:
    """Everything a worker needs to export chunks of one table; must be picklable."""

    table: Table
    database: str
    collection: str
    target: Path
    hasher: PiiHasher
    options: ExportOptions


def export_chunks_in_processes(job: ChunkJob, chunks: list[Chunk], expected: dict[str, int], workers: int,
                               connect: Callable[[], MongoClient], should_stop: Callable[[], bool]) -> list[dict]:
    """Export ``chunks`` with ``workers`` processes; return their markers in plan order."""
    from glamira_pipeline.export.exporter import ExportInterrupted

    context = multiprocessing.get_context("spawn")
    stop = context.Event()
    root = logging.getLogger()
    initargs = (connect, job, stop, root.getEffectiveLevel(), bool(root.handlers))
    markers: dict[str, dict] = {}
    with ProcessPoolExecutor(workers, mp_context=context, initializer=_initialize, initargs=initargs) as pool:
        futures: dict[Future, Chunk] = {pool.submit(_export_chunk, chunk, expected[chunk.id]): chunk
                                        for chunk in chunks}
        pending = set(futures)
        error: BaseException | None = None
        while pending and error is None:
            done, pending = wait(pending, timeout=POLL_SECONDS, return_when=FIRST_COMPLETED)
            for future in done:
                try:
                    markers[futures[future].id] = future.result()
                except BaseException as exc:  # noqa: BLE001 - re-raised below, after stopping the others
                    error = error or exc
            if error is None and should_stop():
                error = ExportInterrupted(f"interrupted; {len(markers)} of {len(chunks)} chunks committed")
        if error is not None:
            stop.set()
            for future in pending:
                future.cancel()
            wait(pending)  # running chunks see the event and stop uncommitted
            raise error
    return [markers[chunk.id] for chunk in chunks]


def _initialize(connect: Callable[[], MongoClient], job: ChunkJob, stop, level: int, configure_logging: bool) -> None:
    global _WORKER
    from glamira_pipeline.export.exporter import ChunkExporter

    signal.signal(signal.SIGINT, signal.SIG_IGN)  # the parent decides when to stop
    if configure_logging:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(processName)s %(name)s: %(message)s")
    collection = connect()[job.database][job.collection]
    _WORKER = ChunkExporter(job.table, collection, job.target, job.hasher, job.options, should_stop=stop.is_set)


def _export_chunk(chunk: Chunk, expected: int) -> dict:
    assert _WORKER is not None, "worker not initialized"
    return _WORKER.run(chunk, expected)
