"""Unit tests for resumable export: chunk planning, commit markers, identity, lock, deterministic parts."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from bson.objectid import ObjectId
import pyarrow as pa

from glamira_pipeline.export.chunks import Chunk, CoverageError, check_coverage, daily_chunks
from glamira_pipeline.export.exporter import content_sha256
from glamira_pipeline.export.parquet_files import ParquetPartWriter, part_dicts
from glamira_pipeline.export.state import (SUCCESS, StateError, claim_identity, commit_chunk, committed_chunk,
                                           exclusive_lock, reset_chunk)

SCHEMA = pa.schema([pa.field("v", pa.int64(), nullable=False)])


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def write_parts(directory: Path, rows: int, rows_per_file: int = 4):
    writer = ParquetPartWriter(directory, SCHEMA, rows_per_file=rows_per_file, row_group_rows=2)
    for value in range(rows):
        writer.write({"v": value})
    return writer.close()


class ChunkPlanTests(unittest.TestCase):
    def test_daily_chunks_are_contiguous_half_open_utc_days(self):
        chunks = daily_chunks(utc(2020, 4, 1, 0, 0, 5), utc(2020, 4, 3, 10, 21, 32))
        self.assertEqual([c.id for c in chunks], ["2020-04-01", "2020-04-02", "2020-04-03"])
        for left, right in zip(chunks, chunks[1:]):
            self.assertEqual(left.upper, right.lower)
        self.assertEqual(chunks[0].lower.generation_time, utc(2020, 4, 1))
        self.assertEqual(chunks[-1].upper.generation_time, utc(2020, 4, 4))
        self.assertEqual(chunks[0].query, {"_id": {"$gte": chunks[0].lower, "$lt": chunks[0].upper}})

    def test_last_second_of_a_day_stays_in_that_day(self):
        oid = ObjectId.from_datetime(utc(2020, 4, 1, 23, 59, 59))
        chunk = daily_chunks(utc(2020, 4, 1), utc(2020, 4, 2))[0]
        self.assertTrue(chunk.lower <= oid < chunk.upper)

    def test_whole_collection_chunk_has_no_filter(self):
        self.assertEqual(Chunk("all").query, {})
        self.assertEqual(Chunk("all", limit=10).describe(), {"id": "all", "range": "all", "limit": 10})

    def test_coverage_must_be_exact(self):
        check_coverage({"a": 2, "b": 3}, 5)
        with self.assertRaisesRegex(CoverageError, "cover 4 documents but the collection holds 5"):
            check_coverage({"a": 1, "b": 3}, 5)


class DeterministicPartTests(unittest.TestCase):
    def test_same_rows_give_identical_bytes(self):
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            first, second = write_parts(Path(a), 10), write_parts(Path(b), 10)
            self.assertEqual([p.sha256 for p in first], [p.sha256 for p in second])
            self.assertEqual(len(first), 3)

    def test_bytes_do_not_depend_on_the_process_hash_seed(self):
        """Worker processes have their own hash seeds; the Parquet bytes must not depend on them."""
        script = ("import tempfile, pathlib\n"
                  "from glamira_pipeline.export.parquet_files import ParquetPartWriter\n"
                  "from glamira_pipeline.export.schema import bigquery_schema, parquet_schema\n"
                  "from glamira_pipeline.export.tables import PRODUCT_OPTION_VALUES\n"
                  "w = ParquetPartWriter(pathlib.Path(tempfile.mkdtemp()), "
                  "parquet_schema(bigquery_schema(PRODUCT_OPTION_VALUES)))\n"
                  "for i in range(5):\n"
                  "    w.write({'product_id': str(i), 'option_id': 'o', 'is_require': True, 'run_id': 'r', "
                  "'crawled_at': 1_600_000_000_000_000 + i})\n"
                  "print(w.close()[0].sha256)\n")
        digests = {subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True,
                                  env={**os.environ, "PYTHONHASHSEED": str(seed)}).stdout for seed in (1, 2, 3, 4)}
        self.assertEqual(len(digests), 1)

    def test_content_hash_ignores_part_order(self):
        files = [{"name": "chunk=a/part-00000.parquet", "sha256": "1"}, {"name": "chunk=b/part-00000.parquet", "sha256": "2"}]
        self.assertEqual(content_sha256(files), content_sha256(files[::-1]))
        self.assertNotEqual(content_sha256(files), content_sha256([{**files[0], "sha256": "3"}, files[1]]))


class ChunkStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.chunk = Path(self.tmp.name) / "chunk=2020-04-01"
        self.chunk.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, rows=5):
        parts = write_parts(self.chunk, rows)
        commit_chunk(self.chunk, {"chunk": "2020-04-01", "rows": rows, "files": part_dicts(parts)})

    def test_uncommitted_chunk_is_reset(self):
        write_parts(self.chunk, 5)
        (self.chunk / "part-00002.parquet.tmp").write_bytes(b"partial")
        self.assertIsNone(committed_chunk(self.chunk))
        self.assertEqual(reset_chunk(self.chunk), 3)
        self.assertEqual(list(self.chunk.iterdir()), [])

    def test_committed_chunk_is_verified(self):
        self.commit()
        self.assertEqual(committed_chunk(self.chunk)["rows"], 5)
        self.assertFalse(list(self.chunk.glob("*.tmp")))

    def test_modified_committed_part_is_refused(self):
        self.commit()
        with (self.chunk / "part-00000.parquet").open("ab") as stream:
            stream.write(b"x")
        with self.assertRaisesRegex(StateError, "SHA-256 differs"):
            committed_chunk(self.chunk)

    def test_missing_or_extra_part_is_refused(self):
        self.commit()
        (self.chunk / "part-00001.parquet").unlink()
        with self.assertRaisesRegex(StateError, "differ from the marker"):
            committed_chunk(self.chunk)

    def test_committed_chunk_is_never_reset(self):
        self.commit()
        with self.assertRaisesRegex(StateError, "committed"):
            reset_chunk(self.chunk)

    def test_foreign_files_are_not_deleted(self):
        (self.chunk / "notes.txt").write_text("keep")
        with self.assertRaisesRegex(StateError, "unexpected files"):
            reset_chunk(self.chunk)
        self.assertTrue((self.chunk / "notes.txt").exists())
        self.assertFalse((self.chunk / SUCCESS).exists())


class IdentityAndLockTests(unittest.TestCase):
    def test_same_identity_resumes_and_other_identity_is_refused(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            first = claim_identity(directory, {"schema": "a", "key": "k"}, {"git_sha": "1"})
            again = claim_identity(directory, {"schema": "a", "key": "k"}, {"git_sha": "2"})
            self.assertEqual(again, first)  # recorded context is kept from the first run
            with self.assertRaisesRegex(StateError, r"other inputs \(key\)"):
                claim_identity(directory, {"schema": "a", "key": "other"}, {})

    def test_second_writer_is_locked_out(self):
        with TemporaryDirectory() as tmp, exclusive_lock(Path(tmp)):
            with self.assertRaisesRegex(StateError, "locked"):
                with exclusive_lock(Path(tmp)):
                    pass


if __name__ == "__main__":
    unittest.main()
