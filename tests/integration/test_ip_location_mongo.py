"""Optional local MongoDB integration tests for sample seeding and resume."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import uuid

from glamira_pipeline.ip_location.pipeline import enrich_sample
from glamira_pipeline.ip_location.source import local_client, seed_sample

URI = os.environ.get("GLAMIRA_TEST_MONGODB_URI")
BIN = Path("IP-COUNTRY-REGION-CITY.BIN")


@unittest.skipUnless(URI and BIN.is_file(), "local MongoDB URI and IP2Location BIN are required")
class IpMongoIntegrationTests(unittest.TestCase):
    def test_seed_resume_and_reject_source_or_result_changes(self):
        client = local_client(URI)
        name = "glamira_ip_sample_test_" + uuid.uuid4().hex
        db = client[name]
        try:
            with TemporaryDirectory() as directory:
                root = Path(directory)
                sample = root / "sample.json"
                sample.write_text(json.dumps([{"ip": "8.8.8.8"}, {"ip": "8.8.8.8"},
                                              {"ip": "2001:4860:4860::8888"}, {"ip": "bad"}, {}]))
                seed_sample(db, sample, 5)
                first = enrich_sample(db, URI, sample, BIN, root / "state.sqlite3", root / "output")
                second = enrich_sample(db, URI, sample, BIN, root / "state.sqlite3", root / "output")
                self.assertEqual(first, second)
                self.assertEqual(first["events"], 5)
                self.assertEqual(first["unique_ips"], 2)
                self.assertEqual(first["lookup_statuses"]["unsupported_ipv6"]["events"], 1)
                self.assertEqual(db.ip_locations.count_documents({}), 2)
                location = db.ip_locations.find_one({"_id": "8.8.8.8"})
                self.assertEqual(set(location), {"_id", "ip_version", "status", "country_code", "country_name", "region", "city", "database_id"})
                self.assertNotIn("event_count", location)
                run = db.enrichment_runs.find_one({"_id": first["bin"]["database_id"]})
                self.assertEqual(run["source"], BIN.name)
                self.assertEqual(run["database_sha256"], first["bin"]["sha256"])
                self.assertIn("processed_at", run)
                db.events.update_one({"_id": 0}, {"$set": {"ip": "1.1.1.1"}})
                with self.assertRaises(ValueError):
                    enrich_sample(db, URI, sample, BIN, root / "state.sqlite3", root / "output")
                db.events.update_one({"_id": 0}, {"$set": {"ip": "8.8.8.8"}})
                sample.write_text("[]")
                with self.assertRaises(ValueError):
                    enrich_sample(db, URI, sample, BIN, root / "state.sqlite3", root / "output")
                sample.write_text(json.dumps([{"ip": "8.8.8.8"}, {"ip": "8.8.8.8"},
                                              {"ip": "2001:4860:4860::8888"}, {"ip": "bad"}, {}]))
                db.ip_locations.drop()
                db.create_collection("ip_locations")
                with self.assertRaises(ValueError):
                    enrich_sample(db, URI, sample, BIN, root / "state.sqlite3", root / "output")
        finally:
            client.drop_database(name)
            client.close()

    def test_changed_bin_refuses_resume(self):
        client = local_client(URI)
        name = "glamira_ip_sample_test_" + uuid.uuid4().hex
        db = client[name]
        try:
            with TemporaryDirectory() as directory:
                root = Path(directory)
                sample = root / "sample.json"
                sample.write_text(json.dumps([{"ip": "8.8.8.8"}]))
                test_bin = root / "fixture.bin"
                with BIN.open("rb") as source:
                    test_bin.write_bytes(source.read(64))
                seed_sample(db, sample, 1)
                reader = SimpleNamespace(
                    get_all=lambda _: SimpleNamespace(country_short="US", country_long="United States", region="-", city="-"),
                    close=lambda: None,
                )
                with patch("glamira_pipeline.ip_location.pipeline.IP2Location.IP2Location", return_value=reader):
                    enrich_sample(db, URI, sample, test_bin, root / "state.sqlite3", root / "output")
                    contents = bytearray(test_bin.read_bytes())
                    contents[-1] ^= 1
                    test_bin.write_bytes(contents)
                    with self.assertRaises(ValueError):
                        enrich_sample(db, URI, sample, test_bin, root / "state.sqlite3", root / "output")
        finally:
            client.drop_database(name)
            client.close()


if __name__ == "__main__":
    unittest.main()
