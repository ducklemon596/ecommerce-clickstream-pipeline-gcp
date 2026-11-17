"""Unit tests for the warehouse stage: load spec, GCS publish, BigQuery load and the Cloud Function.

GCS and BigQuery are replaced by small in-memory fakes; nothing here calls Google Cloud.
"""
import base64
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from google.api_core.exceptions import PreconditionFailed

from glamira_pipeline.export.exporter import MANIFEST, content_sha256
from glamira_pipeline.export.schema import bigquery_schema, schema_json
from glamira_pipeline.export.tables import PRODUCTS
from glamira_pipeline.warehouse.publish import PublishError, file_crc32c, publish_table
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LoadSpec, LoadSpecError, Source

SHA = "ab" * 32


def spec(**overrides) -> LoadSpec:
    values = dict(export_id="2026-11-17", table="events", dataset="raw", rows=10, content_sha256=SHA,
                  sources=(Source("gs://b/raw/events/export_id=2026-11-17/chunk=a/part-00000.avro", 5),),
                  schema=({"name": "_id", "type": "STRING", "mode": "REQUIRED"},
                          {"name": "time_stamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
                          {"name": "collection", "type": "STRING", "mode": "REQUIRED"}),
                  partition_by="time_stamp", cluster_by=("collection",))
    values.update(overrides)
    return LoadSpec(**values)


class FakeBlob:
    def __init__(self, bucket, name):
        self.bucket, self.name, self.crc32c = bucket, name, None

    def _create(self, data: bytes, if_generation_match):
        assert if_generation_match == 0, "objects must be created, never overwritten"
        if self.name in self.bucket.objects:
            raise PreconditionFailed("exists")
        self.bucket.objects[self.name] = data
        self.bucket.order.append(self.name)

    def upload_from_filename(self, filename, if_generation_match=None, checksum=None):
        self._create(Path(filename).read_bytes(), if_generation_match)

    def upload_from_string(self, data, content_type=None, if_generation_match=None, checksum=None):
        self._create(data if isinstance(data, bytes) else data.encode(), if_generation_match)

    def reload(self):
        import base64
        import google_crc32c
        self.crc32c = base64.b64encode(google_crc32c.Checksum(self.bucket.objects[self.name]).digest()).decode()

    def download_as_bytes(self):
        return self.bucket.objects[self.name]

    def download_as_text(self):
        return self.bucket.objects[self.name].decode()

    def exists(self):
        return self.name in self.bucket.objects


class FakeBucket:
    def __init__(self, name="bkt"):
        self.name, self.objects, self.order = name, {}, []

    def blob(self, name):
        return FakeBlob(self, name)

    def get_blob(self, name):
        if name not in self.objects:
            return None
        blob = FakeBlob(self, name)
        blob.size = len(self.objects[name])
        return blob


def build_products_export(root: Path) -> Path:
    """A finished ``products`` export as export-avro leaves it (part bytes are placeholders)."""
    table = root / "products"
    files = []
    for chunk_part, payload in (("chunk=all/part-00000.avro", b"first part"), ("chunk=all/part-00001.avro", b"2nd")):
        path = table / chunk_part
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        files.append({"name": chunk_part, "rows": 2, "bytes": len(payload),
                      "sha256": hashlib.sha256(payload).hexdigest()})
    (table / "chunk=all" / "_SUCCESS.json").write_text("{}")
    (table / "_export.json").write_text("{}")
    (table / ".lock").write_text("")
    (table / "products.avsc").write_text("{}")
    (table / "products.bq.json").write_text(schema_json(bigquery_schema(PRODUCTS)))
    manifest = {"table": "products", "export_id": "x-1", "status": "complete", "rows": 4, "files": files,
                "content_sha256": content_sha256(files)}
    (table / MANIFEST).write_text(json.dumps(manifest))
    return table


class LoadSpecTests(unittest.TestCase):
    def test_round_trip_is_stable(self):
        text = spec().to_json()
        self.assertEqual(LoadSpec.from_json(text), spec())
        self.assertEqual(LoadSpec.from_json(text).to_json(), text)

    def test_job_id_is_deterministic_and_safe(self):
        self.assertEqual(spec().job_id(), f"load_raw_events_2026-11-17_{SHA[:12]}")
        self.assertEqual(spec(export_id="a.b/c").job_id(2), f"load_raw_events_a_b_c_{SHA[:12]}_r2")
        self.assertNotEqual(spec().job_id(), spec(dataset="raw_sample").job_id())

    def test_invalid_specs_are_refused(self):
        cases = [dict(dataset="raw-x"), dict(rows=-1), dict(content_sha256="x"), dict(sources=()),
                 dict(sources=(Source("/tmp/a.avro", 1),)), dict(partition_by="missing")]
        for overrides in cases:
            with self.subTest(overrides), self.assertRaises(LoadSpecError):
                spec(**overrides)
        with self.assertRaisesRegex(LoadSpecError, "malformed"):
            LoadSpec.from_json('{"table": "events"}')


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.table = build_products_export(Path(self.tmp.name))
        self.bucket = FakeBucket()

    def tearDown(self):
        self.tmp.cleanup()

    def publish(self, **kwargs):
        return publish_table(self.table, self.bucket, prefix="raw", dataset="raw", schema_dir=Path(self.tmp.name),
                             workers=2, verify=lambda *a: None, **kwargs)

    def test_parts_then_schemas_and_manifest_then_load_spec_last(self):
        result = self.publish()
        base = "raw/products/export_id=x-1"
        self.assertEqual(set(self.bucket.objects), {
            f"{base}/chunk=all/part-00000.avro", f"{base}/chunk=all/part-00001.avro", f"{base}/products.avsc",
            f"{base}/products.bq.json", f"{base}/{MANIFEST}", f"{base}/{LOAD_SPEC}"})
        self.assertEqual(self.bucket.order[-2:], [f"{base}/{MANIFEST}", f"{base}/{LOAD_SPEC}"])
        self.assertEqual((result.uploaded, result.skipped), (6, 0))
        loaded = LoadSpec.from_json(self.bucket.objects[f"{base}/{LOAD_SPEC}"].decode())
        self.assertEqual(loaded.rows, 4)
        self.assertEqual([s.uri for s in loaded.sources],
                         [f"gs://bkt/{base}/chunk=all/part-00000.avro", f"gs://bkt/{base}/chunk=all/part-00001.avro"])
        self.assertEqual((loaded.partition_by, loaded.cluster_by), (None, ()))

    def test_rerun_skips_everything_already_uploaded(self):
        self.publish()
        result = self.publish()
        self.assertEqual((result.uploaded, result.skipped, result.bytes_uploaded), (0, 6, 0))

    def test_existing_object_with_other_content_stops_the_publish(self):
        self.bucket.objects["raw/products/export_id=x-1/chunk=all/part-00001.avro"] = b"other"
        with self.assertRaisesRegex(PublishError, "exists with other content"):
            self.publish()
        self.assertFalse(any(name.endswith(LOAD_SPEC) for name in self.bucket.objects))

    def test_schema_drift_from_the_contract_is_refused(self):
        (self.table / "products.bq.json").write_text("[]")
        with self.assertRaisesRegex(PublishError, "differs from the contract"):
            self.publish()
        self.assertEqual(self.bucket.objects, {})

    def test_crc32c_uses_the_gcs_encoding(self):
        path = Path(self.tmp.name) / "check"
        path.write_bytes(b"123456789")  # CRC32C check value 0xE3069283
        self.assertEqual(file_crc32c(path), base64.b64encode(bytes.fromhex("e3069283")).decode())

if __name__ == "__main__":
    unittest.main()
