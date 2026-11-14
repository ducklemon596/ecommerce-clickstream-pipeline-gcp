"""Measure each stage of a full BSON load separately.

Benchmark only, not part of the production package. Every stage processes
the whole source and appends one JSON line of measurements to ``--results``.

Stages
    decompress  gzip → BSON bytes (Python ``tarfile`` or ``tar`` + ``pigz``)
    read        raw disk read of an extracted ``.bson`` file
    split       cut the stream into batches: ``raw`` (length prefix only),
                ``decode`` (``bson.decode`` per document) or ``gzip``
                (raw batches re-compressed, as the original chunked loader did)
    restore     ``mongorestore`` of an extracted ``.bson`` file
    insert      Python ``insert_many`` of undecoded ``RawBSONDocument`` batches
                with N worker threads, or ``--upsert`` (decode + ``ReplaceOne``)

MongoDB stages write only to database ``glamira_bench`` and refuse an existing
target collection. The URI comes from ``MONGODB_URI`` and is never printed.

Example (on the VM)::

    uv run python scripts/bench_load.py split --source /data/bench/summary.bson --mode raw
"""
from __future__ import annotations

import argparse
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from typing import BinaryIO

import bson
from bson.raw_bson import RawBSONDocument
from pymongo import ReplaceOne

from glamira_pipeline.mongo import URI_ENV, client_from_env

MEMBER = "dump/countly/summary.bson"
MAX_BSON_SIZE = 16 * 1024 * 1024
BENCH_DATABASE = "glamira_bench"
READ_BLOCK = 8 * 1024 * 1024
WINDOW_DOCS = 1_000_000


class Meter:
    """Wall time, CPU (self + children), peak RSS and per-window throughput."""

    def __init__(self, stage: str, params: dict) -> None:
        self.stage, self.params = stage, params
        self.docs = self.bytes = 0
        self.windows: list[dict] = []
        self._lock = threading.Lock()
        self._next_window = WINDOW_DOCS
        self._window_start = self._start = time.perf_counter()
        self._cpu0 = self._cpu()

    @staticmethod
    def _cpu() -> tuple[float, float]:
        own, kids = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        return own.ru_utime + kids.ru_utime, own.ru_stime + kids.ru_stime

    def add(self, docs: int, nbytes: int) -> None:
        with self._lock:
            self._add(docs, nbytes)

    def _add(self, docs: int, nbytes: int) -> None:
        self.docs += docs
        self.bytes += nbytes
        while self.docs >= self._next_window:
            now = time.perf_counter()
            self.windows.append({"upto": self._next_window,
                                 "docs_per_s": round(WINDOW_DOCS / (now - self._window_start))})
            print(f"[{self.stage}] {self._next_window:,} docs, {self.windows[-1]['docs_per_s']:,} docs/s",
                  file=sys.stderr, flush=True)
            self._window_start, self._next_window = now, self._next_window + WINDOW_DOCS

    def result(self, **extra) -> dict:
        wall = time.perf_counter() - self._start
        user, system = (a - b for a, b in zip(self._cpu(), self._cpu0))
        own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        kids = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        return {
            "stage": self.stage, "params": self.params,
            "at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "docs": self.docs, "bytes": self.bytes, "wall_s": round(wall, 2),
            "cpu_user_s": round(user, 2), "cpu_sys_s": round(system, 2),
            "peak_rss_mb": round(own / 1024), "child_peak_rss_mb": round(kids / 1024),
            "MB_per_s": round(self.bytes / wall / 1e6, 1) if self.bytes else None,
            "docs_per_s": round(self.docs / wall) if self.docs else None,
            "windows": self.windows, **extra,
        }


@contextmanager
def open_source(path: Path, *, pigz: bool = False) -> Iterator[BinaryIO]:
    """Yield the BSON byte stream of a ``.bson`` file or of the dump member in a ``.tar.gz``."""
    if path.suffix == ".bson":
        with path.open("rb", buffering=0) as stream:
            yield stream
        return
    if pigz:
        proc = subprocess.Popen(["tar", "--use-compress-program=pigz", "-xOf", str(path), MEMBER],
                                stdout=subprocess.PIPE, bufsize=READ_BLOCK)
        try:
            yield proc.stdout
        finally:
            proc.stdout.close()
            if proc.wait() != 0:
                raise RuntimeError(f"tar/pigz exited with {proc.returncode}")
        return
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            if member.name == MEMBER and member.isfile():
                stream = archive.extractfile(member)
                assert stream is not None
                yield stream
                return
    raise ValueError(f"{MEMBER} not found in {path}")


def iter_documents(stream: BinaryIO) -> Iterator[memoryview]:
    """Yield each BSON document as a view, using only its 4-byte length prefix (no decoding)."""
    buffer = bytearray()
    offset = 0
    while True:
        block = stream.read(READ_BLOCK)
        if block:
            buffer = buffer[offset:] + block
            offset = 0
        view = memoryview(buffer)
        end = len(buffer)
        while end - offset >= 4:
            size = int.from_bytes(view[offset:offset + 4], "little", signed=True)
            if not 5 <= size <= MAX_BSON_SIZE:
                raise ValueError(f"invalid BSON document size {size}")
            if end - offset < size:
                break
            yield view[offset:offset + size]
            offset += size
        view.release()
        if not block:
            if offset != end:
                raise ValueError("truncated BSON document at end of stream")
            return


def iter_batches(stream: BinaryIO, docs_per_batch: int, max_bytes: int | None = None) -> Iterator[list[bytes]]:
    """Group documents into batches of at most ``docs_per_batch`` docs (and ``max_bytes``)."""
    batch: list[bytes] = []
    size = 0
    for doc in iter_documents(stream):
        if batch and (len(batch) >= docs_per_batch or (max_bytes and size + len(doc) > max_bytes)):
            yield batch
            batch, size = [], 0
        batch.append(bytes(doc))
        size += len(doc)
    if batch:
        yield batch


# --- stages -----------------------------------------------------------------

def stage_decompress(args: argparse.Namespace) -> dict:
    tool = "pigz" if args.pigz else "python-gzip"
    meter = Meter("decompress", {"tool": tool, "output": args.output})
    with open_source(args.archive, pigz=args.pigz) as stream, open(args.output, "wb") as out:
        while block := stream.read(READ_BLOCK):
            out.write(block)
            meter.add(0, len(block))
    return meter.result()


def stage_read(args: argparse.Namespace) -> dict:
    meter = Meter("read", {"source": str(args.source)})
    with args.source.open("rb", buffering=0) as stream:
        while block := stream.read(READ_BLOCK):
            meter.add(0, len(block))
    return meter.result()


def stage_split(args: argparse.Namespace) -> dict:
    meter = Meter("split", {"mode": args.mode, "source": str(args.source), "pigz": args.pigz,
                            "batch_docs": args.batch_docs})
    batches = gzip_bytes = 0
    with open_source(args.source, pigz=args.pigz) as stream:
        for batch in iter_batches(stream, args.batch_docs):
            nbytes = sum(map(len, batch))
            if args.mode == "decode":
                for doc in batch:
                    bson.decode(doc)
            elif args.mode == "gzip":
                gzip_bytes += len(gzip.compress(b"".join(batch), compresslevel=args.gzip_level))
            batches += 1
            meter.add(len(batch), nbytes)
    return meter.result(batches=batches, gzip_bytes=gzip_bytes or None)


def bench_collection(name: str):
    """Return a new collection in the benchmark database, refusing to reuse one."""
    client = client_from_env()
    db = client[BENCH_DATABASE]
    if name in db.list_collection_names():
        raise SystemExit(f"{BENCH_DATABASE}.{name} already exists; choose a new --collection")
    return client, db[name]


def stage_insert(args: argparse.Namespace) -> dict:
    client, coll = bench_collection(args.collection)
    params = {"collection": args.collection, "workers": args.workers, "batch_docs": args.batch_docs,
              "upsert": args.upsert, "source": str(args.source), "pigz": args.pigz}
    meter = Meter("upsert" if args.upsert else "insert", params)

    def write(batch: list[bytes]) -> int:
        if args.upsert:
            docs = [bson.decode(doc) for doc in batch]
            coll.bulk_write([ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs], ordered=False)
        else:
            coll.insert_many([RawBSONDocument(doc) for doc in batch], ordered=False)
        return len(batch)

    pending: set = set()
    try:
        with ThreadPoolExecutor(args.workers) as pool, open_source(args.source, pigz=args.pigz) as stream:
            for batch in iter_batches(stream, args.batch_docs, max_bytes=MAX_BSON_SIZE):
                if len(pending) >= args.workers * 2:  # bounded in-flight batches
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
                nbytes = sum(map(len, batch))
                future = pool.submit(write, batch)
                future.add_done_callback(lambda f, n=len(batch), b=nbytes: f.exception() or meter.add(n, b))
                pending.add(future)
            for future in pending:
                future.result()
        stored = coll.estimated_document_count()
    finally:
        client.close()
    return meter.result(stored_docs=stored)


def stage_restore(args: argparse.Namespace) -> dict:
    client, _ = bench_collection(args.collection)
    client.close()
    uri = os.environ[URI_ENV]
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as config:
        os.chmod(config.name, 0o600)
        config.write(f"uri: {json.dumps(uri)}\n")
    meter = Meter("restore", {"collection": args.collection, "workers": args.workers, "source": str(args.source)})
    streamed = args.source.suffix != ".bson"
    command = ["mongorestore", f"--config={config.name}", f"--db={BENCH_DATABASE}",
               f"--collection={args.collection}", f"--numInsertionWorkersPerCollection={args.workers}",
               "--noIndexRestore", "-" if streamed else str(args.source)]
    try:
        if streamed:  # tar + pigz piped into mongorestore stdin, as the original restore ran
            tar = subprocess.Popen(["tar", "--use-compress-program=pigz", "-xOf", str(args.source), MEMBER],
                                   stdout=subprocess.PIPE)
            proc = subprocess.run(command, stdin=tar.stdout, capture_output=True, text=True)
            tar.stdout.close()
            if tar.wait() != 0:
                raise SystemExit(f"tar/pigz exited with {tar.returncode}")
        else:
            proc = subprocess.run(command, capture_output=True, text=True)
    finally:
        os.unlink(config.name)
    if proc.returncode:
        print(proc.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"mongorestore exited with {proc.returncode}")
    summary = [line for line in proc.stderr.splitlines() if "document(s)" in line]
    meter.bytes = 0 if streamed else args.source.stat().st_size
    with client_from_env() as check:
        stored = check[BENCH_DATABASE][args.collection].estimated_document_count()
    meter.docs = stored
    return meter.result(stored_docs=stored, mongorestore_summary=summary[-2:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=Path("data/bench/results.jsonl"))
    parser.add_argument("--vmstat-log", type=Path, help="also record `vmstat 5` output to this file")
    sub = parser.add_subparsers(dest="stage", required=True)

    p = sub.add_parser("decompress")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", default=os.devnull)
    p.add_argument("--pigz", action="store_true")
    p.set_defaults(func=stage_decompress)

    p = sub.add_parser("read")
    p.add_argument("--source", type=Path, required=True)
    p.set_defaults(func=stage_read)

    p = sub.add_parser("split")
    p.add_argument("--source", type=Path, required=True, help=".bson file or .tar.gz archive")
    p.add_argument("--mode", choices=("raw", "decode", "gzip"), default="raw")
    p.add_argument("--batch-docs", type=int, default=100_000)
    p.add_argument("--gzip-level", type=int, default=6)
    p.add_argument("--pigz", action="store_true")
    p.set_defaults(func=stage_split)

    p = sub.add_parser("restore")
    p.add_argument("--source", type=Path, required=True, help=".bson file or .tar.gz (streamed via pigz)")
    p.add_argument("--collection", required=True)
    p.add_argument("--workers", type=int, default=1)
    p.set_defaults(func=stage_restore)

    p = sub.add_parser("insert")
    p.add_argument("--source", type=Path, required=True, help=".bson file or .tar.gz archive")
    p.add_argument("--pigz", action="store_true", help="decompress a .tar.gz source with tar + pigz")
    p.add_argument("--collection", required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--batch-docs", type=int, default=1_000)
    p.add_argument("--upsert", action="store_true", help="decode and ReplaceOne(upsert=True), like the old loader")
    p.set_defaults(func=stage_insert)

    args = parser.parse_args()
    vmstat = None
    if args.vmstat_log:
        args.vmstat_log.parent.mkdir(parents=True, exist_ok=True)
        vmstat = subprocess.Popen(["vmstat", "-t", "5"], stdout=args.vmstat_log.open("w"))
    try:
        result = args.func(args)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc
    finally:
        if vmstat:
            vmstat.terminate()
    line = json.dumps(result)
    print(line)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("a", encoding="utf-8") as out:
        out.write(line + "\n")


if __name__ == "__main__":
    main()
