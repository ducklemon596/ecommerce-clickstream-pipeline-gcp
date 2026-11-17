"""Optional local MongoDB tests for export-avro: full export, verification, failures and interruption.

Run with a disposable server, e.g.::

    docker run -d --rm -p 127.0.0.1:27099:27017 mongo:8.0
    GLAMIRA_TEST_MONGODB_URI=mongodb://127.0.0.1:27099/ uv run python -m unittest tests.integration.test_export_mongo
"""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid

from bson import ObjectId
import fastavro

from glamira_pipeline.export.exporter import (MANIFEST, ExportError, ExportInterrupted, ExportOptions,
                                              export_table, verify_export)
from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.tables import EVENTS
from glamira_pipeline.mongo import connect

URI = os.environ.get("GLAMIRA_TEST_MONGODB_URI")
HASHER = PiiHasher(bytes(range(32)))


def events(n):
    base = {"api_version": "1.0", "store_id": "6", "current_url": "u", "referrer_url": "",
            "device_id": "d", "user_id_db": "", "user_agent": "ua", "email_address": ""}
    out = []
    for i in range(n):
        doc = {"_id": ObjectId(), "collection": "view_listing_page", "time_stamp": 1_585_699_201 + i,
               "ip": f"198.51.100.{i % 250}", **base}
        if i % 3 == 0:
            doc["option"] = {"alloy": "", "diamond": "", "shapediamond": ""}
        elif i % 3 == 1:
            doc.update(collection="checkout_success", order_id=float(1000 + i),
                       cart_products=[{"product_id": 1, "amount": 1, "price": "1,00", "currency": "€", "option": ""}])
        out.append(doc)
    return out


@unittest.skipUnless(URI, "set GLAMIRA_TEST_MONGODB_URI to a disposable local MongoDB")
class ExportMongoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = connect(URI)
        self.db = self.client["glamira_export_test_" + uuid.uuid4().hex[:8]]
        self.collection = self.db["summary"]
        self.collection.insert_many(events(2_500))
        self.tmp = TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.client.drop_database(self.db.name)
        self.client.close()
        self.tmp.cleanup()

    def test_full_export_is_complete_and_verifiable(self):
        manifest = export_table(EVENTS, self.collection, self.out, HASHER, ExportOptions(rows_per_file=1_000))
        self.assertEqual((manifest["rows"], len(manifest["files"])), (2_500, 3))
        self.assertEqual(manifest["source"]["documents_before"], 2_500)
        self.assertEqual(manifest["conversions"]["order_id: double -> string"], 833)
        self.assertEqual(manifest["conversions"]["option: object -> option_filter"], 834)
        self.assertEqual(verify_export(self.out / "events")["rows"], 2_500)
        with (self.out / "events" / "part-00000.avro").open("rb") as stream:
            first = next(fastavro.reader(stream))
        self.assertEqual(first["option_filter"]["alloy"], "")
        self.assertNotIn("198.51.100", (self.out / "events" / "part-00000.avro").read_bytes().decode("latin-1"))

    def test_limit_exports_a_labelled_sample(self):
        manifest = export_table(EVENTS, self.collection, self.out, HASHER, ExportOptions(limit=100))
        self.assertEqual(manifest["rows"], 100)
        self.assertIn("non-random", manifest["selection"])

    def test_violation_stops_without_a_manifest(self):
        self.collection.insert_one({**events(1)[0], "surprise": 1})
        with self.assertRaisesRegex(ExportError, "unknown keys \\['surprise'\\]"):
            export_table(EVENTS, self.collection, self.out, HASHER)
        self.assertFalse((self.out / "events" / MANIFEST).exists())
        self.assertFalse(list((self.out / "events").glob("*.tmp")))

    def test_existing_directory_is_refused(self):
        (self.out / "events").mkdir()
        with self.assertRaises(FileExistsError):
            export_table(EVENTS, self.collection, self.out, HASHER)

    def test_interrupt_discards_the_open_part(self):
        calls = iter(range(10_000))
        with self.assertRaises(ExportInterrupted):
            export_table(EVENTS, self.collection, self.out, HASHER, ExportOptions(rows_per_file=1_000),
                         should_stop=lambda: next(calls) >= 1_500)
        names = sorted(p.name for p in (self.out / "events").iterdir())
        self.assertEqual(names, ["events.avsc", "events.bq.json", "part-00000.avro"])

    def test_tampered_part_fails_verification(self):
        export_table(EVENTS, self.collection, self.out, HASHER)
        manifest_path = self.out / "events" / MANIFEST
        manifest = json.loads(manifest_path.read_text())
        manifest["files"][0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ExportError, "checksum"):
            verify_export(self.out / "events")


if __name__ == "__main__":
    unittest.main()
