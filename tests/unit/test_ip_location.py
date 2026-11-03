"""Synthetic tests for IP normalization, checkpoints and coverage."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from glamira_pipeline.ip_location.checkpoint import last_id, open_checkpoint, save_event_batch
from glamira_pipeline.ip_location.lookup import bin_metadata, event_address, lookup_address
from glamira_pipeline.ip_location.pipeline import metrics, process_addresses, write_outputs
from glamira_pipeline.ip_location.source import local_client


class Reader:
    def __init__(self, _path=None, mode="FILE_IO"):
        self.mode = mode
        self.calls = []

    def get_all(self, address):
        self.calls.append(address)
        if address == "1.1.1.1":
            return SimpleNamespace(country_short="-", country_long="-", region="-", city="-")
        if address == "9.9.9.9":
            raise OSError("lookup failed")
        return SimpleNamespace(country_short="US", country_long="United States", region="California", city="Mountain View")

    def close(self):
        pass


class Collection:
    def __init__(self):
        self.docs = {}
        self.fail_after_write = False

    def replace_one(self, query, document, upsert):
        self.docs[query["_id"]] = document
        if self.fail_after_write:
            self.fail_after_write = False
            raise OSError("simulated interruption after write")

    def bulk_write(self, operations, ordered):
        for operation in operations:
            self.docs[operation._filter["_id"]] = operation._doc


class Database:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, key):
        return self.collections.setdefault(key, Collection())


class IpLocationTests(unittest.TestCase):
    def test_event_classification_uses_only_ip(self):
        self.assertEqual(event_address({"ip": None})[0], "null")
        self.assertEqual(event_address({"user_ip": "8.8.8.8"})[0], "missing")
        self.assertEqual(event_address({"ip": "bad"})[0], "invalid_format")
        self.assertEqual(event_address({"ip": 123})[0], "invalid_type")
        self.assertEqual(event_address({"ip": "  "})[0], "empty")
        self.assertEqual(event_address({})[0], "missing")
        self.assertEqual(event_address({"ip": "2001:4860:4860:0:0:0:0:8888"})[1], "2001:4860:4860::8888")

    def test_lookup_outcomes(self):
        reader = Reader()
        self.assertEqual(lookup_address(reader, "8.8.8.8", False)["status"], "resolved")
        self.assertEqual(lookup_address(reader, "1.1.1.1", False)["status"], "no_match")
        self.assertEqual(lookup_address(reader, "9.9.9.9", False)["status"], "lookup_failed")
        self.assertEqual(lookup_address(reader, "10.0.0.1", False)["status"], "not_public")
        self.assertEqual(lookup_address(reader, "2001:4860:4860::8888", False)["status"], "unsupported_ipv6")

    def test_checkpoint_resume_and_event_weighted_coverage(self):
        events = [{"_id": 0, "ip": "8.8.8.8"}, {"_id": 1, "ip": " 8.8.8.8 "},
                  {"_id": 2, "ip": "1.1.1.1"}, {"_id": 3, "ip": None},
                  {"_id": 4, "ip": "invalid"}, {"_id": 5, "ip": "2001:4860:4860::8888"},
                  {"_id": 6, "ip": "9.9.9.9"}]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.sqlite3"
            identity = {"source": "fixture", "bin": "a"}
            connection = open_checkpoint(path, identity)
            save_event_batch(connection, events[:3])
            connection.close()
            connection = open_checkpoint(path, identity)
            self.assertEqual(last_id(connection), 2)
            save_event_batch(connection, events[3:])
            with self.assertRaises(ValueError):
                save_event_batch(connection, [{"_id": 9, "ip": "8.8.8.8"}])
            self.assertEqual(last_id(connection), 6)
            database = Database()
            info = {"edition": 3, "date": "2016-11-29", "ipv6_supported": False,
                    "sha256": "fixture-sha256", "database_id": "fixture-sha256"}
            with patch("glamira_pipeline.ip_location.pipeline.IP2Location.IP2Location", side_effect=Reader) as reader_factory:
                database["ip_locations"].fail_after_write = True
                with self.assertRaises(OSError):
                    process_addresses(database, connection, Path("fake.bin"), info)
                process_addresses(database, connection, Path("fake.bin"), info)
                reader_factory.assert_called_with("fake.bin", mode="SHARED_MEMORY")
            summary = metrics(connection, info)
            self.assertEqual(summary["events"], 7)
            self.assertEqual(summary["unique_ips"], 4)
            self.assertAlmostEqual(summary["event_coverage_percent"], 200 / 7)
            self.assertEqual(summary["unique_ip_coverage_percent"], 25)
            self.assertEqual(summary["lookup_statuses"]["lookup_failed"]["events"], 1)
            self.assertEqual(len(database["ip_locations"].docs), 4)
            saved = database["ip_locations"].docs["8.8.8.8"]
            self.assertEqual(set(saved), {"_id", "ip_version", "status", "country_code", "country_name", "region", "city", "database_id"})
            self.assertNotIn("event_count", saved)
            run = next(iter(database["enrichment_runs"].docs.values()))
            self.assertEqual(set(run), {"_id", "database_id", "source", "database_date", "database_edition", "database_sha256", "processed_at"})
            self.assertEqual(run["source"], "fake.bin")
            write_outputs(connection, Path(tmp), summary)
            self.assertNotIn("8.8.8.8", (Path(tmp) / "ip_location_report.md").read_text())
            self.assertNotIn("8.8.8.8", (Path(tmp) / "ip_location_metrics.json").read_text())
            self.assertIn("8.8.8.8", (Path(tmp) / "ip_locations.csv").read_text())
            csv_text = (Path(tmp) / "ip_locations.csv").read_text()
            self.assertTrue(csv_text.startswith("_id,ip_version,status,"))
            self.assertNotIn("event_count", csv_text)
            class RecoveringReader(Reader):
                def get_all(self, address):
                    if address == "9.9.9.9":
                        return SimpleNamespace(country_short="US", country_long="United States", region="-", city="-")
                    return super().get_all(address)

            with patch("glamira_pipeline.ip_location.pipeline.IP2Location.IP2Location", RecoveringReader):
                process_addresses(database, connection, Path("fake.bin"), info, retry_failed=True)
            self.assertAlmostEqual(metrics(connection, info)["event_coverage_percent"], 300 / 7)
            self.assertEqual(len(database["ip_locations"].docs), 4)
            connection.close()
            with self.assertRaises(ValueError):
                open_checkpoint(path, {"source": "fixture", "bin": "changed"})

    def test_loopback_uri_only(self):
        with self.assertRaises(ValueError):
            local_client("mongodb://example.com:27017/")
        with self.assertRaises(ValueError):
            local_client("mongodb+srv://example.com/")
        client = local_client("mongodb://127.0.0.1:27017/")
        client.close()

    def test_real_bin_header_if_available(self):
        path = Path("IP-COUNTRY-REGION-CITY.BIN")
        if not path.exists():
            self.skipTest("local IP2Location BIN not present")
        info = bin_metadata(path)
        self.assertEqual(info["edition"], 3)
        self.assertFalse(info["ipv6_supported"])


if __name__ == "__main__":
    unittest.main()
