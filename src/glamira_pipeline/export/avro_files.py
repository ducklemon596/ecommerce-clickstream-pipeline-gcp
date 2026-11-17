"""Write rows into numbered Avro part files with bounded size and checksums.

Each part is written as ``*.avro.tmp`` and renamed only after it is closed and
fsynced, so a visible ``part-NNNNN.avro`` is always complete. Several parts let
``gcloud storage`` upload and BigQuery read in parallel; ``rows_per_file``
bounds the size of each part.

Output is deterministic: each part's 16-byte Avro sync marker is derived from
``sync_seed`` and the part name instead of being random, so the same rows in
the same order always give the same bytes and the same SHA-256.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
from typing import BinaryIO

from fastavro import parse_schema
from fastavro.write import Writer

CODEC = "deflate"  # supported by BigQuery and built into fastavro


@dataclass(frozen=True)
class PartFile:
    """A finished part, as recorded in the manifest."""

    name: str
    rows: int
    bytes: int
    sha256: str


class _HashingFile:
    """File wrapper that hashes and counts every byte written through it."""

    def __init__(self, stream: BinaryIO) -> None:
        self.stream = stream
        self.sha256 = hashlib.sha256()
        self.size = 0

    def write(self, data: bytes) -> int:
        self.sha256.update(data)
        self.size += len(data)
        return self.stream.write(data)

    def flush(self) -> None:
        self.stream.flush()

    def seekable(self) -> bool:
        return False  # tells fastavro this is a fresh file, never an append


class AvroPartWriter:
    """Append rows to ``<directory>/part-NNNNN.avro``, starting a new part every ``rows_per_file``."""

    def __init__(self, directory: Path, schema: dict, *, rows_per_file: int = 1_000_000,
                 sync_seed: str = "") -> None:
        if rows_per_file < 1:
            raise ValueError("rows_per_file must be positive")
        self.directory = directory
        self.sync_seed = sync_seed
        self.schema = parse_schema(schema)
        self.rows_per_file = rows_per_file
        self.parts: list[PartFile] = []
        self._stream: BinaryIO | None = None
        self._hashing: _HashingFile | None = None
        self._writer: Writer | None = None
        self._rows = 0

    @property
    def rows(self) -> int:
        """Rows written so far, including the open part."""
        return sum(p.rows for p in self.parts) + self._rows

    def write(self, row: dict) -> None:
        if self._writer is None:
            self._open()
        self._writer.write(row)  # type: ignore[union-attr]
        self._rows += 1
        if self._rows >= self.rows_per_file:
            self._close_part()

    def close(self) -> list[PartFile]:
        """Finish the open part (if any) and return every finished part."""
        if self._writer is not None:
            self._close_part()
        return self.parts

    def abort(self) -> None:
        """Discard the open part; finished parts stay on disk."""
        if self._stream is not None:
            self._stream.close()
            self._tmp_path().unlink(missing_ok=True)
        self._stream = self._hashing = self._writer = None
        self._rows = 0

    def _name(self) -> str:
        return f"part-{len(self.parts):05d}.avro"

    def _tmp_path(self) -> Path:
        return self.directory / (self._name() + ".tmp")

    def _open(self) -> None:
        self._stream = self._tmp_path().open("xb")
        self._hashing = _HashingFile(self._stream)
        self._writer = Writer(self._hashing, self.schema, codec=CODEC,
                              sync_marker=sync_marker(self.sync_seed, self._name()))
        self._rows = 0

    def _close_part(self) -> None:
        assert self._writer is not None and self._stream is not None and self._hashing is not None
        self._writer.flush()
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._stream.close()
        name = self._name()
        os.replace(self._tmp_path(), self.directory / name)
        self.parts.append(PartFile(name, self._rows, self._hashing.size, self._hashing.sha256.hexdigest()))
        self._stream = self._hashing = self._writer = None
        self._rows = 0


def sync_marker(seed: str, part_name: str) -> bytes:
    """Deterministic 16-byte Avro sync marker for one part."""
    return hashlib.sha256(f"{seed}/{part_name}".encode()).digest()[:16]


def part_dicts(parts: list[PartFile]) -> list[dict]:
    """Manifest form of the finished parts."""
    return [asdict(p) for p in parts]
