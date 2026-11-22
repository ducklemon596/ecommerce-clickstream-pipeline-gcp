"""Unit tests for the warehouse stage: load spec, GCS publish, BigQuery load and the Cloud Function.

GCS and BigQuery are replaced by small in-memory fakes; nothing here calls Google Cloud.
"""
import base64
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from concurrent.futures import TimeoutError as FutureTimeout
from types import SimpleNamespace

from google.api_core.exceptions import BadRequest, Conflict, InternalServerError, NotFound, PreconditionFailed
from google.cloud import bigquery

from glamira_pipeline.export.exporter import MANIFEST, content_sha256
from glamira_pipeline.export.schema import bigquery_schema, schema_json
from glamira_pipeline.export.tables import PRODUCTS
from glamira_pipeline.warehouse.bigquery import LoadError, TransientLoadError, load
from glamira_pipeline.warehouse.function import handle
from glamira_pipeline.warehouse.publish import PublishError, file_crc32c, publish_table
from glamira_pipeline.warehouse.runner import process_load_spec
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LOADED, LoadSpec, LoadSpecError, Source

SHA = "ab" * 32


def spec(**overrides) -> LoadSpec:
    values = dict(export_id="2026-11-17", table="events", dataset="raw", rows=10, content_sha256=SHA,
                  sources=(Source("gs://b/raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet", 5),),
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


class FakeGcs:
    def __init__(self, *buckets):
        self.buckets = {b.name: b for b in buckets}

    def bucket(self, name):
        return self.buckets.setdefault(name, FakeBucket(name))


class FakeJob:
    def __init__(self, bq, job_id, outcome):
        self.bq, self.job_id, self.outcome, self.error_result, self.state = bq, job_id, outcome, None, "RUNNING"

    def result(self, timeout=None):
        if self.outcome == "timeout":
            raise FutureTimeout()
        self.state = "DONE"
        if self.outcome == "ok":
            self.bq.tables[self.bq.destination].num_rows = self.bq.rows_after_load
            return self
        self.error_result = {"reason": self.outcome}
        raise (InternalServerError if self.outcome == "backendError" else BadRequest)(self.outcome)


class FakeBigQuery:
    """Tables, jobs (with scripted outcomes per job ID) and 409 on a reused job ID."""

    project = "proj"

    def __init__(self, outcomes=None, rows_after_load=10):
        self.tables, self.jobs, self.submitted = {}, {}, []
        self.outcomes, self.rows_after_load = outcomes or {}, rows_after_load
        self.destination = None

    def get_dataset(self, name):
        return SimpleNamespace(location="asia-southeast1")

    def get_table(self, ref):
        if ref not in self.tables:
            raise NotFound(ref)
        return self.tables[ref]

    def create_table(self, table):
        self.tables[f"{table.project}.{table.dataset_id}.{table.table_id}"] = SimpleNamespace(
            schema=table.schema, time_partitioning=table.time_partitioning,
            clustering_fields=table.clustering_fields, num_rows=0)

    def load_table_from_uri(self, uris, destination, job_id, location, job_config):
        if job_id in self.jobs:
            raise Conflict(job_id)
        assert location == "asia-southeast1" and job_config.write_disposition == "WRITE_TRUNCATE_DATA"
        assert job_config.source_format == "PARQUET" and job_config.parquet_options.enable_list_inference
        self.destination = destination
        self.submitted.append((job_id, list(uris)))
        self.jobs[job_id] = FakeJob(self, job_id, self.outcomes.get(job_id, "ok"))
        return self.jobs[job_id]

    def get_job(self, job_id, location):
        return self.jobs[job_id]


def build_products_export(root: Path) -> Path:
    """A finished ``products`` export as export-raw leaves it (part bytes are placeholders)."""
    table = root / "products"
    files = []
    for chunk_part, payload in (("chunk=all/part-00000.parquet", b"first part"), ("chunk=all/part-00001.parquet", b"2nd")):
        path = table / chunk_part
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        files.append({"name": chunk_part, "rows": 2, "bytes": len(payload),
                      "sha256": hashlib.sha256(payload).hexdigest()})
    (table / "chunk=all" / "_SUCCESS.json").write_text("{}")
    (table / "_export.json").write_text("{}")
    (table / ".lock").write_text("")
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
                 dict(sources=(Source("/tmp/a.parquet", 1),)), dict(partition_by="missing")]
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
            f"{base}/chunk=all/part-00000.parquet", f"{base}/chunk=all/part-00001.parquet",
            f"{base}/products.bq.json", f"{base}/{MANIFEST}", f"{base}/{LOAD_SPEC}"})
        self.assertEqual(self.bucket.order[-2:], [f"{base}/{MANIFEST}", f"{base}/{LOAD_SPEC}"])
        self.assertEqual((result.uploaded, result.skipped), (5, 0))
        loaded = LoadSpec.from_json(self.bucket.objects[f"{base}/{LOAD_SPEC}"].decode())
        self.assertEqual(loaded.rows, 4)
        self.assertEqual([s.uri for s in loaded.sources],
                         [f"gs://bkt/{base}/chunk=all/part-00000.parquet", f"gs://bkt/{base}/chunk=all/part-00001.parquet"])
        self.assertEqual((loaded.partition_by, loaded.cluster_by), (None, ()))

    def test_rerun_skips_everything_already_uploaded(self):
        self.publish()
        result = self.publish()
        self.assertEqual((result.uploaded, result.skipped, result.bytes_uploaded), (0, 5, 0))

    def test_existing_object_with_other_content_stops_the_publish(self):
        self.bucket.objects["raw/products/export_id=x-1/chunk=all/part-00001.parquet"] = b"other"
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

class BigQueryLoadTests(unittest.TestCase):
    def setUp(self):
        self.spec = spec()
        self.bucket = FakeBucket("b")
        self.bucket.objects["raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet"] = b"12345"
        self.gcs = FakeGcs(self.bucket)

    def test_first_load_creates_the_partitioned_table_and_checks_rows(self):
        bq = FakeBigQuery()
        result = load(self.spec, bq, self.gcs)
        table = bq.tables["proj.raw.events"]
        self.assertEqual((table.time_partitioning.field, table.clustering_fields), ("time_stamp", ["collection"]))
        self.assertEqual((result.rows, result.created_table, result.job_id), (10, True, self.spec.job_id()))
        self.assertEqual(bq.submitted, [(self.spec.job_id(), [s.uri for s in self.spec.sources])])

    def test_repeat_reuses_the_job_instead_of_loading_twice(self):
        bq = FakeBigQuery()
        load(self.spec, bq, self.gcs)
        result = load(self.spec, bq, self.gcs)
        self.assertEqual((len(bq.submitted), result.created_table), (1, False))

    def test_transient_job_failure_is_retried_under_a_new_id(self):
        bq = FakeBigQuery(outcomes={self.spec.job_id(): "backendError"})
        self.assertEqual(load(self.spec, bq, self.gcs).job_id, self.spec.job_id(2))
        bq = FakeBigQuery(outcomes={self.spec.job_id(n): "backendError" for n in (1, 2, 3)})
        with self.assertRaises(TransientLoadError):
            load(self.spec, bq, self.gcs)

    def test_permanent_job_failure_and_timeout(self):
        with self.assertRaisesRegex(LoadError, "invalid"):
            load(self.spec, FakeBigQuery(outcomes={self.spec.job_id(): "invalid"}), self.gcs)
        with self.assertRaisesRegex(TransientLoadError, "still running"):
            load(self.spec, FakeBigQuery(outcomes={self.spec.job_id(): "timeout"}), self.gcs, wait_seconds=1)

    def test_missing_or_resized_source_stops_before_any_job(self):
        bq = FakeBigQuery()
        self.bucket.objects["raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet"] = b"1234"
        with self.assertRaisesRegex(LoadError, "4 bytes, the export wrote 5"):
            load(self.spec, bq, self.gcs)
        self.bucket.objects.clear()
        with self.assertRaisesRegex(LoadError, "missing source"):
            load(self.spec, bq, self.gcs)
        self.assertEqual(bq.submitted, [])

    def test_existing_table_with_another_layout_is_refused(self):
        bq = FakeBigQuery()
        load(self.spec, bq, self.gcs)
        bq.tables["proj.raw.events"].schema = [bigquery.SchemaField("_id", "INT64", "REQUIRED")]
        with self.assertRaisesRegex(LoadError, "schema"):
            load(spec(content_sha256="cd" * 32), bq, self.gcs)
        bq.tables["proj.raw.events"].schema = [bigquery.SchemaField.from_api_repr(f) for f in self.spec.schema]
        bq.tables["proj.raw.events"].clustering_fields = None
        with self.assertRaisesRegex(LoadError, "clustered by"):
            load(spec(content_sha256="cd" * 32), bq, self.gcs)

    def test_row_count_mismatch_is_an_error(self):
        with self.assertRaisesRegex(LoadError, "holds 9 rows"):
            load(self.spec, FakeBigQuery(rows_after_load=9), self.gcs)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.bucket = FakeBucket("b")
        self.bucket.objects["raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet"] = b"12345"
        self.name = f"raw/events/export_id=2026-11-17/{LOAD_SPEC}"
        self.bucket.objects[self.name] = spec().to_json().encode()
        self.gcs = FakeGcs(self.bucket)

    def test_only_load_specs_are_processed(self):
        outcome = process_load_spec(self.gcs, None, "b", "raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet")
        self.assertEqual(outcome.status, "ignored")

    def test_marker_is_written_and_stops_repeats(self):
        bq = FakeBigQuery()
        first = process_load_spec(self.gcs, bq, "b", self.name)
        marker = json.loads(self.bucket.objects[f"raw/events/export_id=2026-11-17/{LOADED}"])
        self.assertEqual((first.status, marker["rows"], marker["job_id"]), ("loaded", 10, spec().job_id()))
        again = process_load_spec(self.gcs, None, "b", self.name)  # no BigQuery call at all
        self.assertEqual(again.status, "already_loaded")
        forced = process_load_spec(self.gcs, bq, "b", self.name, ignore_marker=True)
        self.assertEqual((forced.status, len(bq.submitted)), ("loaded", 1))

    def test_dataset_outside_the_allowlist_is_refused(self):
        with self.assertRaisesRegex(LoadError, "not in the allowed datasets"):
            process_load_spec(self.gcs, FakeBigQuery(), "b", self.name, allowed_datasets={"raw_sample"})

    def test_malformed_spec_is_a_permanent_error(self):
        self.bucket.objects[self.name] = b"{}"
        with self.assertRaises(LoadSpecError):
            process_load_spec(self.gcs, FakeBigQuery(), "b", self.name)


class FunctionTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[2]

    def setUp(self):
        self.bucket = FakeBucket("b")
        self.bucket.objects["raw/events/export_id=2026-11-17/chunk=a/part-00000.parquet"] = b"12345"
        self.name = f"raw/events/export_id=2026-11-17/{LOAD_SPEC}"
        self.bucket.objects[self.name] = spec().to_json().encode()
        self.env = {"ALLOWED_DATASETS": "raw, raw_sample"}

    def call(self, bq, name=None, env=None):
        logs = io.StringIO()
        with redirect_stdout(logs):
            outcome = handle({"bucket": "b", "name": name or self.name}, env=self.env if env is None else env,
                             clients=(FakeGcs(self.bucket), bq))
        return outcome, [json.loads(line) for line in logs.getvalue().splitlines()]

    def test_parts_and_other_objects_are_ignored_without_clients(self):
        outcome = handle({"bucket": "b", "name": "raw/events/export_id=x/chunk=a/part-00000.parquet"}, env={})
        self.assertEqual(outcome.status, "ignored")

    def test_load_spec_is_loaded_and_logged(self):
        outcome, logs = self.call(FakeBigQuery())
        self.assertEqual(outcome.status, "loaded")
        self.assertEqual((logs[-1]["severity"], logs[-1]["rows"]), ("INFO", 10))

    def test_transient_failure_is_raised_for_redelivery(self):
        with self.assertRaises(TransientLoadError):
            self.call(FakeBigQuery(outcomes={spec().job_id(): "timeout"}))

    def test_permanent_failures_are_logged_not_retried(self):
        outcome, logs = self.call(FakeBigQuery(rows_after_load=9))
        self.assertIsNone(outcome)
        self.assertEqual((logs[-1]["severity"], logs[-1]["error"]), ("ERROR", "LoadError"))
        outcome, logs = self.call(FakeBigQuery(), env={"ALLOWED_DATASETS": "raw_sample"})
        self.assertIn("not in the allowed datasets", logs[-1]["message"])
        outcome, logs = self.call(FakeBigQuery(), env={})
        self.assertIsNone(outcome)
        self.assertIn("ALLOWED_DATASETS is not set", logs[-1]["message"])

    def test_deployed_modules_do_not_import_the_export_package(self):
        """The deploy script ships only some warehouse modules; they must import nothing else of the project."""
        script = (self.ROOT / "scripts/deploy_bigquery_loader.sh").read_text()
        modules = re.search(r"for module in ([\w ]+); do", script).group(1).split()
        with TemporaryDirectory() as tmp:
            package = Path(tmp) / "glamira_pipeline" / "warehouse"
            package.mkdir(parents=True)
            shutil.copy(self.ROOT / "src/glamira_pipeline/__init__.py", package.parent)
            for module in modules:
                shutil.copy(self.ROOT / f"src/glamira_pipeline/warehouse/{module}.py", package)
            shutil.copy(self.ROOT / "functions/bigquery_loader/main.py", tmp)
            check = ("import sys; sys.path.insert(0, '.'); import main; "
                     "bad = [m for m in sys.modules if m.startswith(('glamira_pipeline.export', 'pymongo'))]; "
                     "assert main.handle.__module__ == 'glamira_pipeline.warehouse.function', main.handle; "
                     "assert not bad, bad")
            subprocess.run([sys.executable, "-W", "ignore", "-c", check], cwd=tmp, check=True)
            # The function loads Parquet server side; it never needs pyarrow (google-cloud-bigquery imports it
            # opportunistically when installed, so check the shipped sources instead of sys.modules).
            for module in modules:
                self.assertNotIn("pyarrow", (package / f"{module}.py").read_text())


if __name__ == "__main__":
    unittest.main()
