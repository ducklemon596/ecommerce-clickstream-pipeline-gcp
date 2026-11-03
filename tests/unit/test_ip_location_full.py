"""Tests for bounded full-collection IP enrichment and BSON checkpoints."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bson import ObjectId

from glamira_pipeline.ip_location.full_pipeline import (
    _last_source_id,
    _save_scan_batch,
    full_metrics,
    lookup_pending,
    open_full_checkpoint,
)


class FakeReader:
    def __init__(self, _path, mode):
        self.mode = mode

    def get_all(self, _ip):
        return SimpleNamespace(country_short="US", country_long="United States",
                               region="California", city="Mountain View")

    def close(self):
        pass


class FakeTarget:
    def __init__(self):
        self.documents = {}

    def bulk_write(self, operations, ordered):
        self.assert_ordered = ordered
        for operation in operations:
            self.documents[operation._filter["_id"]] = operation._doc


class FullIpLocationTests(unittest.TestCase):
    def test_checkpoint_keeps_bson_cursor_and_deduplicated_counts(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.sqlite3"
            connection = open_full_checkpoint(path, {"source": "countly.summary", "bin": "abc"})
            indexes = {row[1] for row in connection.execute("PRAGMA index_list(addresses)")}
            self.assertIn("idx_addresses_status_ip", indexes)
            first_id, last_id = ObjectId(), ObjectId()
            _save_scan_batch(connection, [
                {"_id": first_id, "ip": "8.8.8.8"},
                {"_id": last_id, "user_ip": "8.8.8.8"},
            ])
            self.assertEqual(_last_source_id(connection), last_id)
            row = connection.execute("SELECT * FROM addresses WHERE ip='8.8.8.8'").fetchone()
            self.assertEqual((row["version"], row["events"], row["status"]), (4, 1, "pending"))
            invalid = connection.execute("SELECT category, events FROM invalid").fetchone()
            self.assertEqual((invalid["category"], invalid["events"]), ("missing", 1))
            connection.close()
            with self.assertRaises(ValueError):
                open_full_checkpoint(path, {"source": "different", "bin": "abc"})

    def test_lookup_upserts_agreed_schema_in_memory_mode(self):
        with TemporaryDirectory() as directory:
            connection = open_full_checkpoint(Path(directory) / "state.sqlite3", {"source": "s", "bin": "b"})
            _save_scan_batch(connection, [{"_id": ObjectId(), "ip": "8.8.8.8"}])
            target = FakeTarget()
            info = {"ipv6_supported": False, "database_id": "sha256"}
            with patch("glamira_pipeline.ip_location.full_pipeline.IP2Location.IP2Location", side_effect=FakeReader) as factory:
                self.assertEqual(lookup_pending(connection, target, Path("database.bin"), info), 1)
                factory.assert_called_once_with("database.bin", mode="SHARED_MEMORY")
            document = target.documents["8.8.8.8"]
            self.assertEqual(set(document), {"_id", "ip_version", "status", "country_code",
                                             "country_name", "region", "city", "database_id"})
            self.assertEqual(document["database_id"], "sha256")
            self.assertNotIn("event_count", document)
            summary = full_metrics(connection, {"database_id": "sha256"})
            self.assertEqual(summary["events"], 1)
            self.assertEqual(summary["event_coverage_percent"], 100)
            connection.close()


if __name__ == "__main__":
    unittest.main()
