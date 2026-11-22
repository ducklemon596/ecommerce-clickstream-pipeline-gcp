"""Unit tests for verify-export: inventory both ways, checksums, committed schema and Parquet footers, optional decode."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from glamira_pipeline.export.exporter import MANIFEST, content_sha256
from glamira_pipeline.export.parquet_files import ParquetPartWriter, part_dicts
from glamira_pipeline.export.schema import parquet_schema, schema_json
from glamira_pipeline.export.state import IDENTITY, LOCK, SUCCESS
from glamira_pipeline.export.verify import VerificationError, table_directories, verify_table

BQ_SCHEMA = [{"name": "v", "mode": "REQUIRED", "type": "INTEGER"}]
SCHEMA_TEXT = schema_json(BQ_SCHEMA)


def build_export(root: Path) -> Path:
    """A finished two-chunk export of table ``t`` (7 rows), as export-avro would leave it."""
    table = root / "t"
    files, chunks = [], []
    for chunk, rows in (("2020-04-01", 4), ("2020-04-02", 3)):
        directory = table / f"chunk={chunk}"
        directory.mkdir(parents=True)
        writer = ParquetPartWriter(directory, parquet_schema(BQ_SCHEMA), rows_per_file=3)
        for value in range(rows):
            writer.write({"v": value})
        parts = part_dicts(writer.close())
        (directory / SUCCESS).write_text(json.dumps({"chunk": chunk, "rows": rows, "files": parts}))
        files += [{**part, "name": f"chunk={chunk}/{part['name']}"} for part in parts]
        chunks.append({"id": chunk, "rows": rows})
    (table / "t.bq.json").write_text(SCHEMA_TEXT)
    (table / IDENTITY).write_text("{}")
    (table / LOCK).write_text("")
    manifest = {"table": "t", "status": "complete", "rows": 7, "bytes": sum(f["bytes"] for f in files),
                "chunks": chunks, "files": files, "content_sha256": content_sha256(files),
                "schema_sha256": hashlib.sha256(SCHEMA_TEXT.encode()).hexdigest()}
    (table / MANIFEST).write_text(json.dumps(manifest))
    return table


class VerifyExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.table = build_export(root / "export")
        self.schemas = root / "schemas"
        self.schemas.mkdir()
        (self.schemas / "t.bq.json").write_text(SCHEMA_TEXT)

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self, **kwargs):
        return verify_table(self.table, self.schemas, **kwargs)

    def test_intact_export_passes_without_and_with_decoding(self):
        result = self.verify()
        self.assertEqual((result.files, result.rows, result.decoded), (3, 7, False))
        self.assertTrue(self.verify(full=True).decoded)

    def test_export_or_table_directory_is_accepted(self):
        self.assertEqual(table_directories(self.table.parent), [self.table])
        self.assertEqual(table_directories(self.table), [self.table])
        with self.assertRaisesRegex(VerificationError, "no _manifest.json"):
            table_directories(self.schemas)

    def test_missing_part_is_reported(self):
        (self.table / "chunk=2020-04-01" / "part-00001.parquet").unlink()
        with self.assertRaisesRegex(VerificationError, r"missing \['chunk=2020-04-01/part-00001.parquet'\]"):
            self.verify()

    def test_extra_part_tmp_file_and_unknown_chunk_are_reported(self):
        cases = ["chunk=2020-04-01/part-00002.parquet", "chunk=2020-04-02/part-00001.parquet.tmp",
                 "chunk=2020-04-09/part-00000.parquet"]
        for relative in cases:
            with self.subTest(relative):
                path = self.table / relative
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b"x")
                with self.assertRaisesRegex(VerificationError, "unexpected"):
                    self.verify()
                path.unlink()

    def test_changed_bytes_are_reported(self):
        part = self.table / "chunk=2020-04-02" / "part-00000.parquet"
        data = bytearray(part.read_bytes())
        data[-1] ^= 1
        part.write_bytes(bytes(data))
        with self.assertRaisesRegex(VerificationError, "SHA-256 differs"):
            self.verify()

    def test_schema_differing_from_the_repository_is_reported(self):
        (self.schemas / "t.bq.json").write_text(SCHEMA_TEXT.replace('"INTEGER"', '"STRING"'))
        with self.assertRaisesRegex(VerificationError, "but the committed t.bq.json"):
            self.verify()

    def test_missing_committed_schema_is_reported(self):
        (self.schemas / "t.bq.json").unlink()
        with self.assertRaisesRegex(VerificationError, "no committed schema"):
            self.verify()

    def test_incomplete_manifest_is_refused(self):
        manifest = json.loads((self.table / MANIFEST).read_text())
        (self.table / MANIFEST).write_text(json.dumps({**manifest, "status": "running"}))
        with self.assertRaisesRegex(VerificationError, "status"):
            self.verify()

    def test_wrong_row_count_is_caught_from_the_footer(self):
        manifest = json.loads((self.table / MANIFEST).read_text())
        manifest["files"][0]["rows"] += 1
        (self.table / MANIFEST).write_text(json.dumps(manifest))
        with self.assertRaisesRegex(VerificationError, "footer holds 3 rows, manifest says 4"):
            self.verify()

    def test_part_written_with_another_schema_is_reported(self):
        other = [{"name": "v", "mode": "NULLABLE", "type": "INTEGER"}]
        directory = self.table / "chunk=2020-04-02"
        for path in directory.glob("part-*"):
            path.unlink()
        writer = ParquetPartWriter(directory, parquet_schema(other), rows_per_file=3)
        for value in range(3):
            writer.write({"v": value})
        parts = part_dicts(writer.close())
        manifest = json.loads((self.table / MANIFEST).read_text())
        manifest["files"] = [f for f in manifest["files"] if not f["name"].startswith("chunk=2020-04-02/")]
        manifest["files"] += [{**part, "name": f"chunk=2020-04-02/{part['name']}"} for part in parts]
        manifest["content_sha256"] = content_sha256(manifest["files"])
        (self.table / MANIFEST).write_text(json.dumps(manifest))
        (directory / SUCCESS).write_text(json.dumps({"chunk": "2020-04-02", "rows": 3, "files": parts}))
        with self.assertRaisesRegex(VerificationError, "Parquet schema differs from the contract"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
