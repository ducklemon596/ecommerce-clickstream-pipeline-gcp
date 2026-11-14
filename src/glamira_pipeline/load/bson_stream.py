"""Stream BSON documents out of a ``.tar.gz`` mongodump without decoding them.

A BSON document starts with its total length as a little-endian int32, so a
dump can be cut into documents by reading that prefix alone. Documents stay as
the original bytes: nothing is decoded or re-encoded on the way to MongoDB.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
from typing import BinaryIO

DEFAULT_MEMBER = "dump/countly/summary.bson"
MIN_BSON_SIZE = 5                      # int32 length + terminating 0x00
MAX_BSON_SIZE = 16 * 1024 * 1024       # MongoDB's document size limit
READ_BLOCK = 8 * 1024 * 1024


class TimedReader:
    """Wrap a binary stream and record time spent waiting in ``read`` and whether EOF was reached.

    With ``pigz`` the wait is time blocked on decompression in the child process;
    with ``tarfile`` it is the in-process decompression itself.
    """

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self.seconds = 0.0
        self.bytes = 0
        self.eof = False

    def read(self, size: int = -1) -> bytes:
        started = time.perf_counter()
        data = self._stream.read(size)
        self.seconds += time.perf_counter() - started
        self.bytes += len(data)
        if not data and size != 0:
            self.eof = True
        return data


def pigz_available() -> bool:
    """Return True when both ``tar`` and ``pigz`` are on PATH."""
    return bool(shutil.which("tar") and shutil.which("pigz"))


@contextmanager
def open_member(archive: Path, member: str = DEFAULT_MEMBER, *, pigz: bool | None = None) -> Iterator[TimedReader]:
    """Yield the decompressed bytes of one member of a ``.tar.gz`` archive.

    ``pigz=None`` uses ``tar`` + ``pigz`` when available (decompression then runs
    in a separate process, in parallel with the caller) and falls back to Python's
    ``tarfile``. Raises ValueError when the member is missing and RuntimeError
    when the decompressor fails after the stream was read to the end.
    """
    if not archive.is_file():
        raise FileNotFoundError(f"archive not found: {archive}")
    if pigz is None:
        pigz = pigz_available()
    if pigz:
        proc = subprocess.Popen(["tar", "--use-compress-program=pigz", "-xOf", str(archive), member],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=READ_BLOCK)
        reader = TimedReader(proc.stdout)
        try:
            yield reader
        finally:
            proc.stdout.close()
            if not reader.eof:
                proc.terminate()  # the caller stopped early; the decompressor's exit status is irrelevant
            stderr = proc.stderr.read().decode(errors="replace").strip()
            proc.stderr.close()
            returncode = proc.wait()
        # Reached only when the caller consumed the stream without raising.
        if returncode != 0 and reader.eof:
            raise RuntimeError(f"tar/pigz failed ({returncode}): {stderr[-500:]}")
        if reader.eof and reader.bytes == 0:
            raise ValueError(f"{member} not found or empty in {archive.name}")
        return
    with tarfile.open(archive, mode="r|gz") as tar:
        for entry in tar:
            if entry.name == member and entry.isfile():
                stream = tar.extractfile(entry)
                if stream is None:
                    break
                with stream:
                    yield TimedReader(stream)
                return
    raise ValueError(f"{member} not found in {archive.name}")


def iter_documents(stream: BinaryIO) -> Iterator[bytes]:
    """Yield each BSON document's bytes, cut by its length prefix.

    Raises ValueError on an impossible length or a document truncated at the
    end of the stream, so a corrupt dump is never loaded silently.
    """
    buffer = b""
    offset = 0
    while True:
        block = stream.read(READ_BLOCK)
        if block:
            buffer = buffer[offset:] + block
            offset = 0
        end = len(buffer)
        while end - offset >= 4:
            size = int.from_bytes(buffer[offset:offset + 4], "little", signed=True)
            if not MIN_BSON_SIZE <= size <= MAX_BSON_SIZE:
                raise ValueError(f"invalid BSON document length {size}")
            if end - offset < size:
                break
            yield buffer[offset:offset + size]
            offset += size
        if not block:
            if offset != end:
                raise ValueError("truncated BSON document at end of stream")
            return


@dataclass(frozen=True)
class Batch:
    """Consecutive documents; ``index`` and ``end_offset`` are deterministic for given limits."""

    index: int
    start_offset: int
    end_offset: int
    docs: list[bytes]

    @property
    def nbytes(self) -> int:
        return self.end_offset - self.start_offset


def iter_batches(stream: BinaryIO, max_docs: int, max_bytes: int) -> Iterator[Batch]:
    """Group documents into batches of at most ``max_docs`` documents and ``max_bytes`` bytes.

    A single document larger than ``max_bytes`` still forms its own batch. The
    same stream and limits always produce the same batch boundaries, which is
    what makes a batch index usable as a resume checkpoint.
    """
    if max_docs < 1 or max_bytes < 1:
        raise ValueError("max_docs and max_bytes must be positive")
    docs: list[bytes] = []
    start = size = index = 0
    for doc in iter_documents(stream):
        if docs and (len(docs) >= max_docs or size + len(doc) > max_bytes):
            yield Batch(index, start, start + size, docs)
            index, start, docs, size = index + 1, start + size, [], 0
        docs.append(doc)
        size += len(doc)
    if docs:
        yield Batch(index, start, start + size, docs)
