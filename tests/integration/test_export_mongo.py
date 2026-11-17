"""Optional local MongoDB tests for export-avro: chunks, resume, retry, determinism and failures.

Run with a disposable server, e.g.::

    docker run -d --rm -p 127.0.0.1:27099:27017 mongo:8.0
    GLAMIRA_TEST_MONGODB_URI=mongodb://127.0.0.1:27099/ uv run python -m unittest tests.integration.test_export_mongo
"""
from datetime import datetime, timezone
from functools import partial
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid

from bson import ObjectId
import fastavro
from pymongo.errors import AutoReconnect

from glamira_pipeline.export.chunks import CoverageError
from glamira_pipeline.export.cli import SCHEMA_DIR
from glamira_pipeline.export.exporter import MANIFEST, ExportError, ExportInterrupted, ExportOptions, export_table
from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.state import SUCCESS, StateError
from glamira_pipeline.export.tables import EVENTS
from glamira_pipeline.export.verify import verify_table
from glamira_pipeline.mongo import connect

URI = os.environ.get("GLAMIRA_TEST_MONGODB_URI")
HASHER = PiiHasher(bytes(range(32)))
DAY0 = int(datetime(2020, 4, 1, tzinfo=timezone.utc).timestamp())
DAYS = ("2020-04-01", "2020-04-02", "2020-04-03")


def events(n):
    """``n`` events spread over three UTC days, with tracker-like ObjectIds (time = time_stamp)."""
    base = {"api_version": "1.0", "store_id": "6", "current_url": "u", "referrer_url": "",
            "device_id": "d", "user_id_db": "", "user_agent": "ua", "email_address": ""}
    out = []
    for i in range(n):
        seconds = DAY0 + (i % 3) * 86_400 + i
        doc = {"_id": ObjectId(f"{seconds:08x}{i:016x}"), "collection": "view_listing_page",
               "time_stamp": seconds, "ip": f"198.51.100.{i % 250}", **base}
        if i % 3 == 0:
            doc["option"] = {"alloy": "", "diamond": "", "shapediamond": ""}
        elif i % 3 == 1:
            doc.update(collection="checkout_success", order_id=float(1000 + i),
                       cart_products=[{"product_id": 1, "amount": 1, "price": "1,00", "currency": "€", "option": ""}])
        out.append(doc)
    return out


class FlakyCollection:
    """Collection proxy whose first ``failures`` calls to ``find`` raise AutoReconnect."""

    def __init__(self, collection, failures):
        self._collection, self.failures = collection, failures

    def __getattr__(self, name):
        return getattr(self._collection, name)

    def find(self, *args, **kwargs):
        if self.failures:
            self.failures -= 1
            raise AutoReconnect("simulated connection reset")
        return self._collection.find(*args, **kwargs)


def stop_after(rows):
    calls = iter(range(10**9))
    return lambda: next(calls) >= rows


@unittest.skipUnless(URI, "set GLAMIRA_TEST_MONGODB_URI to a disposable local MongoDB")
class ExportMongoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = connect(URI)
        self.db = self.client["glamira_export_test_" + uuid.uuid4().hex[:8]]
        self.collection = self.db["summary"]
        self.collection.insert_many(events(2_400))
        self.tmp = TemporaryDirectory()
        self.out = Path(self.tmp.name) / "export-1"
        self.options = ExportOptions(rows_per_file=500, backoff_seconds=0)

    def tearDown(self):
        self.client.drop_database(self.db.name)
        self.client.close()
        self.tmp.cleanup()

    def export(self, out=None, collection=None, **kwargs):
        collection = self.collection if collection is None else collection
        return export_table(EVENTS, collection, out or self.out, HASHER,
                            kwargs.pop("options", self.options), **kwargs)

    def test_full_export_is_chunked_by_day_complete_and_verifiable(self):
        manifest = self.export()
        self.assertEqual([c["id"] for c in manifest["chunks"]], list(DAYS))
        self.assertEqual(manifest["rows"], 2_400)
        self.assertEqual(manifest["source"]["documents"], 2_400)
        self.assertEqual(len(manifest["files"]), 6)  # 800 rows per day, 500 per file
        self.assertEqual(manifest["conversions"]["order_id: double -> string"], 800)
        self.assertEqual(verify_table(self.out / "events", SCHEMA_DIR, full=True).rows, 2_400)
        with (self.out / "events" / "chunk=2020-04-01" / "part-00000.avro").open("rb") as stream:
            rows = list(fastavro.reader(stream))
        self.assertEqual([r["_id"] for r in rows], sorted(r["_id"] for r in rows))
        self.assertFalse(any(r["ip_hash"].startswith("198.51.100") for r in rows))

    def test_rerun_of_a_complete_export_changes_nothing(self):
        first = self.export()
        self.assertEqual(self.export(), first)

    def test_output_does_not_depend_on_physical_order(self):
        reversed_copy = self.db["summary_reversed"]
        reversed_copy.insert_many(list(self.collection.find().sort("_id", -1)))
        first = self.export()
        second = self.export(out=Path(self.tmp.name) / "export-2", collection=reversed_copy)
        self.assertEqual(first["content_sha256"], second["content_sha256"])

    def test_interrupted_export_resumes_and_redoes_only_the_open_chunk(self):
        clean = self.export(out=Path(self.tmp.name) / "clean")
        with self.assertRaises(ExportInterrupted):
            self.export(should_stop=stop_after(1_000))  # day 1 (800 rows) committed, day 2 open
        target = self.out / "events"
        self.assertTrue((target / "chunk=2020-04-01" / SUCCESS).exists())
        self.assertFalse((target / "chunk=2020-04-02" / SUCCESS).exists())
        committed_at = json.loads((target / "chunk=2020-04-01" / SUCCESS).read_text())["committed_at"]

        resumed = self.export()
        self.assertEqual(json.loads((target / "chunk=2020-04-01" / SUCCESS).read_text())["committed_at"], committed_at)
        self.assertEqual(resumed["content_sha256"], clean["content_sha256"])
        self.assertEqual(verify_table(target, SCHEMA_DIR).rows, 2_400)

    def test_transient_error_retries_the_chunk(self):
        slept = []
        manifest = self.export(collection=FlakyCollection(self.collection, failures=2), sleep=slept.append)
        self.assertEqual(manifest["rows"], 2_400)
        self.assertEqual(manifest["chunks"][0]["attempt"], 3)
        self.assertEqual(len(slept), 2)

    def test_transient_errors_beyond_the_budget_fail(self):
        with self.assertRaisesRegex(ExportError, "AutoReconnect after 3 attempts"):
            self.export(collection=FlakyCollection(self.collection, failures=3), sleep=lambda s: None)
        self.assertFalse((self.out / "events" / MANIFEST).exists())

    def test_tampered_committed_chunk_stops_the_resume(self):
        with self.assertRaises(ExportInterrupted):
            self.export(should_stop=stop_after(1_000))
        with (self.out / "events" / "chunk=2020-04-01" / "part-00000.avro").open("r+b") as stream:
            stream.seek(-1, 2)
            stream.write(b"\0")
        with self.assertRaisesRegex(StateError, "SHA-256 differs"):
            self.export()

    def test_other_inputs_cannot_reuse_an_export_id(self):
        with self.assertRaises(ExportInterrupted):
            self.export(should_stop=stop_after(10))
        with self.assertRaisesRegex(StateError, "rows_per_file"):
            self.export(options=ExportOptions(rows_per_file=999))
        with self.assertRaisesRegex(StateError, "pii_key_fingerprint"):
            export_table(EVENTS, self.collection, self.out, PiiHasher(bytes(32)), self.options)

    def test_violation_stops_without_a_marker(self):
        bad = events(1)[0]
        self.collection.insert_one({**bad, "_id": ObjectId(f"{DAY0 + 5:08x}{'f' * 16}"), "surprise": 1})
        with self.assertRaisesRegex(ExportError, "unknown keys \\['surprise'\\]"):
            self.export()
        self.assertFalse((self.out / "events" / "chunk=2020-04-01" / SUCCESS).exists())
        self.assertFalse((self.out / "events" / MANIFEST).exists())
        self.assertFalse(list((self.out / "events").rglob("*.tmp")))

    def test_ids_outside_objectid_ranges_fail_the_coverage_check(self):
        self.collection.insert_one({**events(1)[0], "_id": "not-an-objectid"})
        with self.assertRaisesRegex(CoverageError, "not ObjectIds"):
            self.export()

    def parallel(self, workers=3, **kwargs):
        options = ExportOptions(rows_per_file=500, backoff_seconds=0, workers=workers)
        return self.export(options=options, connect=partial(connect, URI), **kwargs)

    def test_parallel_workers_give_the_same_output(self):
        single = self.export(out=Path(self.tmp.name) / "single")
        manifest = self.parallel()
        self.assertEqual(manifest["workers"], 3)
        self.assertEqual(manifest["content_sha256"], single["content_sha256"])
        self.assertEqual([c["id"] for c in manifest["chunks"]], list(DAYS))
        self.assertEqual(verify_table(self.out / "events", SCHEMA_DIR).rows, 2_400)

    def test_parallel_interrupt_resumes_with_another_worker_count(self):
        single = self.export(out=Path(self.tmp.name) / "single")
        with self.assertRaises(ExportInterrupted):
            self.parallel(should_stop=lambda: True)
        self.assertFalse((self.out / "events" / MANIFEST).exists())
        self.assertFalse(list((self.out / "events").rglob("*.tmp")))
        resumed = self.parallel(workers=2)
        self.assertEqual(resumed["content_sha256"], single["content_sha256"])

    def test_violation_in_a_worker_stops_the_run(self):
        bad = {**events(1)[0], "_id": ObjectId(f"{DAY0 + 86_400 + 5:08x}{'f' * 16}"), "surprise": 1}
        self.collection.insert_one(bad)
        with self.assertRaisesRegex(ExportError, "chunk=2020-04-02 .*unknown keys"):
            self.parallel()
        self.assertFalse((self.out / "events" / "chunk=2020-04-02" / SUCCESS).exists())
        self.assertFalse((self.out / "events" / MANIFEST).exists())

    def test_workers_need_a_connect_function(self):
        with self.assertRaisesRegex(ValueError, "connect is required"):
            self.export(options=ExportOptions(workers=2))

    def test_limit_exports_a_labelled_sample_by_id(self):
        manifest = self.export(options=ExportOptions(limit=100))
        self.assertEqual((manifest["rows"], [c["id"] for c in manifest["chunks"]]), (100, ["all"]))
        self.assertIn("non-random", manifest["selection"])


if __name__ == "__main__":
    unittest.main()
