"""Write rows into numbered Parquet part files with bounded size and checksums.

Each part is written as ``*.parquet.tmp`` and renamed only after its footer is
written and the file is fsynced, so a visible ``part-NNNNN.parquet`` is always
complete. Several parts let ``gcloud storage`` upload and BigQuery read in
parallel; ``rows_per_file`` bounds the size of each part.

Rows are buffered and written ``row_group_rows`` at a time: pyarrow converts a
whole batch in C++, which is several times faster than row-by-row encoding, at
the cost of holding one row group in memory (about 330 MB for 50,000 events).

Output is deterministic: row groups always break at the same row counts, and
the footer holds only the writer version and the Arrow schema, so the same
rows in the same order give the same bytes and SHA-256 in any process. Each
part's SHA-256 is computed while it is written.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
from typing import BinaryIO

import pyarrow as pa
import pyarrow.parquet as pq

COMPRESSION = "snappy"  # supported by BigQuery; fast to write and read
FORMAT_VERSION = "2.6"
ROW_GROUP_ROWS = 50_000


@dataclass(frozen=True)
class PartFile:
    """A finished part, as recorded in the chunk marker and the manifest."""

    name: str
    rows: int
    bytes: int
    sha256: str


class _HashingFile:
    """File wrapper that hashes and counts every byte pyarrow writes through it."""

    def __init__(self, stream: BinaryIO) -> None:
        self.stream = stream
        self.sha256 = hashlib.sha256()
        self.size = 0
        self.closed = False

    def write(self, data) -> int:
        data = bytes(data)
        self.sha256.update(data)
        self.size += len(data)
        return self.stream.write(data)

    def tell(self) -> int:
        return self.size

    def flush(self) -> None:
        self.stream.flush()

    def close(self) -> None:  # pyarrow closes the sink after the footer; the real file is closed by the part writer
        self.closed = True


class ParquetPartWriter:
    """Append rows to ``<directory>/part-NNNNN.parquet``, starting a new part every ``rows_per_file`` rows."""

    def __init__(self, directory: Path, schema: pa.Schema, *, rows_per_file: int = 1_000_000,
                 row_group_rows: int = ROW_GROUP_ROWS) -> None:
        if rows_per_file < 1 or row_group_rows < 1:
            raise ValueError("rows_per_file and row_group_rows must be positive")
        self.directory = directory
        self.schema = schema
        self.rows_per_file = rows_per_file
        self.row_group_rows = min(row_group_rows, rows_per_file)
        self.parts: list[PartFile] = []
        self._stream: BinaryIO | None = None
        self._hashing: _HashingFile | None = None
        self._writer: pq.ParquetWriter | None = None
        self._buffer: list[dict] = []
        self._rows = 0  # rows of the open part, written or buffered

    def write(self, row: dict) -> None:
        """Add one row; raises (pyarrow's ArrowInvalid/ArrowTypeError) when a buffered row does not fit the schema."""
        self._buffer.append(row)
        self._rows += 1
        if len(self._buffer) >= self.row_group_rows:
            self._flush_row_group()
        if self._rows >= self.rows_per_file:
            self._close_part()

    def close(self) -> list[PartFile]:
        """Finish the open part (if any) and return every finished part."""
        if self._rows:
            self._close_part()
        return self.parts

    def abort(self) -> None:
        """Discard the open part; finished parts stay on disk."""
        if self._writer is not None:
            try:
                self._writer.close()  # release pyarrow's writer; the footer goes to the file deleted below
            except (pa.ArrowException, OSError, ValueError):
                pass
        if self._stream is not None:
            self._stream.close()
        self._tmp_path().unlink(missing_ok=True)
        self._stream = self._hashing = self._writer = None
        self._buffer = []
        self._rows = 0

    def _name(self) -> str:
        return f"part-{len(self.parts):05d}.parquet"

    def _tmp_path(self) -> Path:
        return self.directory / (self._name() + ".tmp")

    def _flush_row_group(self) -> None:
        if not self._buffer:
            return
        table = pa.Table.from_pylist(self._buffer, schema=self.schema)
        if self._writer is None:
            self._stream = self._tmp_path().open("xb")
            self._hashing = _HashingFile(self._stream)
            self._writer = pq.ParquetWriter(self._hashing, self.schema, compression=COMPRESSION,
                                            version=FORMAT_VERSION)
        self._writer.write_table(table, row_group_size=self.row_group_rows)
        self._buffer = []

    def _close_part(self) -> None:
        self._flush_row_group()
        assert self._writer is not None and self._stream is not None and self._hashing is not None
        self._writer.close()  # writes the footer
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._stream.close()
        name = self._name()
        os.replace(self._tmp_path(), self.directory / name)
        self.parts.append(PartFile(name, self._rows, self._hashing.size, self._hashing.sha256.hexdigest()))
        self._stream = self._hashing = self._writer = None
        self._rows = 0


def part_dicts(parts: list[PartFile]) -> list[dict]:
    """Manifest form of the finished parts."""
    return [asdict(p) for p in parts]
