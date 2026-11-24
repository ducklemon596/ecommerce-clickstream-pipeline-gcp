"""Synthetic tests for the in-memory IP enrichment pipeline."""
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from glamira_pipeline.ip_location.counter import CounterScan, counter_rows, persist_counter, scan_in_memory
from glamira_pipeline.ip_location.output import publish_collection, lookup_and_upsert, verify_staging



class Cursor:
    def __init__(self, documents):
        self.documents = iter(documents)
        self.requested_batch_size = None

    def batch_size(self, size):
        self.requested_batch_size = size
        return self

    def close(self):
        self.closed = True

    def limit(self, count):
        import itertools
        self.documents = iter(itertools.islice(self.documents, count))
        return self

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.documents)


class Source:
    def __init__(self, documents):
        self.documents = documents

    def find(self, query, projection):
        self.query = query
        self.projection = projection
        self.cursor = Cursor(self.documents)
        return self.cursor


class Reader:
    def __init__(self, _path, mode):
        self.mode = mode

    def get_all(self, _ip):
        return SimpleNamespace(country_short="US", country_long="United States",
                               region="California", city="Mountain View")

    def close(self):
        pass


class Staging:
    def __init__(self):
        self.documents = {}
        self.rename_called = False
        self.fail_write = False

    def bulk_write(self, operations, ordered):
        if self.fail_write:
            raise OSError("injected bulk write failure")
        self.ordered = ordered
        for operation in operations:
            self.documents[operation._filter["_id"]] = operation._doc

    def aggregate(self, pipeline):
        counts = Counter(doc["status"] for doc in self.documents.values())
        return [{"_id": status, "count": count} for status, count in counts.items()]

    def rename(self, name, dropTarget):
        self.rename_called = True
        self.renamed_to = name


class CounterPipelineTests(unittest.TestCase):
    def test_scan_uses_unsorted_ip_only_cursor_and_counts_invalids(self):
        source = Source([
            {"ip": "8.8.8.8"}, {"ip": " 8.8.8.8 "}, {"ip": None},
            {"ip": "bad"}, {"user_ip": "1.1.1.1"},
        ])
        scan = scan_in_memory(source)
        self.assertEqual(source.query, {})
        self.assertEqual(source.projection, {"_id": 0, "ip": 1})
        self.assertEqual(source.cursor.requested_batch_size, 50_000)
        self.assertEqual(scan.events, 5)
        self.assertEqual(scan.addresses, Counter({("8.8.8.8", 4): 2}))
        self.assertEqual(scan.invalid, Counter({"null": 1, "invalid_format": 1, "missing": 1}))

    def test_counter_file_is_private_atomic_and_checksum_validated(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "ip_counter.jsonl"
            scan = CounterScan(3, Counter({("8.8.8.8", 4): 2}), Counter({"missing": 1}),
                               1.0, 0.5, "start", "finish")
            manifest = persist_counter(scan, target, "countly.summary", "uuid", {
                "sha256": "sha", "database_id": "sha", "date": "2016-11-29", "edition": 3,
            })
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            rows = list(counter_rows(target))
            self.assertEqual(rows, [{"ip": "8.8.8.8", "ip_version": 4, "events": 2}])
            self.assertEqual(manifest["events"], 3)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])
            with self.assertRaises(FileExistsError):
                persist_counter(scan, target, "countly.summary", "uuid", {})
            target.write_text(target.read_text().replace('"events":2', '"events":9'))
            with self.assertRaisesRegex(ValueError, "checksum"):
                list(counter_rows(target))

    def test_lookup_upserts_are_idempotent_and_publish_only_after_verification(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "counter.jsonl"
            scan = CounterScan(2, Counter({("8.8.8.8", 4): 2}), Counter(),
                               1.0, 0.5, "start", "finish")
            persist_counter(scan, path, "countly.summary", "uuid", {
                "sha256": "sha", "database_id": "sha", "date": "2016-11-29", "edition": 3,
            })
            staging = Staging()
            info = {"database_id": "sha", "ipv6_supported": False}
            with patch("glamira_pipeline.ip_location.output.IP2Location.IP2Location", side_effect=Reader):
                first = lookup_and_upsert(path, staging, Path("fake.bin"), info)
                second = lookup_and_upsert(path, staging, Path("fake.bin"), info)
            self.assertEqual(first[0]["status_unique_ips"], {"resolved": 1})
            self.assertEqual(second[1], 1)
            self.assertEqual(len(staging.documents), 1)
            self.assertEqual(verify_staging(staging, 1)["documents"], 1)
            with self.assertRaisesRegex(ValueError, "has 1 documents"):
                verify_staging(staging, 2)
            self.assertFalse(staging.rename_called)
            report_path = Path(directory) / "report.json"
            report_path.with_name(report_path.name + ".tmp").write_text("interrupted")
            with self.assertRaises(FileExistsError):
                publish_collection(staging, "ip_locations", report_path, {})
            self.assertFalse(staging.rename_called)

    def test_failed_bulk_write_leaves_staging_unpublished(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "counter.jsonl"
            persist_counter(CounterScan(1, Counter({("8.8.8.8", 4): 1}), Counter(),
                                        1.0, 0.5, "start", "finish"), path,
                            "countly.summary", "uuid", {"sha256": "s", "database_id": "s"})
            staging = Staging()
            staging.fail_write = True
            with patch("glamira_pipeline.ip_location.output.IP2Location.IP2Location", side_effect=Reader):
                with self.assertRaises(OSError):
                    lookup_and_upsert(path, staging, Path("fake.bin"), {
                        "database_id": "s", "ipv6_supported": False,
                    })
            self.assertFalse(staging.rename_called)
            self.assertEqual(staging.documents, {})

class CounterFailureTests(unittest.TestCase):
    def test_limit_and_cursor_cleanup(self):
        source = Source([{'ip': '8.8.8.8'}, {'ip': '1.1.1.1'}])
        scan = scan_in_memory(source, limit=1)
        self.assertEqual(scan.events, 1)
        self.assertTrue(source.cursor.closed)

    def test_missing_footer_prevents_publish(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'counter.jsonl'
            path.write_text('{"ip":"8.8.8.8","ip_version":4,"events":1}\n')
            staging = Staging()
            with patch('glamira_pipeline.ip_location.output.IP2Location.IP2Location', side_effect=Reader):
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    lookup_and_upsert(path, staging, Path('fake.bin'), {
                        'database_id': 'sha', 'ipv6_supported': False})
            self.assertFalse(staging.rename_called)

    def test_publish_uses_no_overwrite_rename(self):
        with TemporaryDirectory() as directory:
            staging = Staging()
            with patch.object(staging, 'rename', side_effect=ValueError('target exists')) as rename:
                path = Path(directory) / 'metrics.json'
                with self.assertRaises(ValueError):
                    publish_collection(staging, 'existing', path, {})
                rename.assert_called_once_with('existing', dropTarget=False)
                self.assertFalse(path.exists())

    def test_existing_target_rejected_before_scan(self):
        from unittest.mock import MagicMock
        from glamira_pipeline.ip_location.pipeline import enrich_collection
        source = MagicMock(name='source')
        source.name = 'events'
        source.database.list_collection_names.return_value = ['ip_locations']
        with self.assertRaisesRegex(ValueError, 'already exists'):
            enrich_collection(source, 'ip_locations', Path('fake.bin'), Path('unused'))
        source.find.assert_not_called()

    def test_orchestration_weighted_coverage_and_failed_lookup(self):
        from unittest.mock import MagicMock
        from glamira_pipeline.ip_location.pipeline import enrich_collection
        source = MagicMock()
        source.name = 'events'
        source.full_name = 'sample.events'
        source.database.name = 'sample'
        source.database.list_collection_names.return_value = ['events']
        source.database.list_collections.return_value = iter([{'info': {'uuid': b'identity'}}])
        scan = CounterScan(10, Counter({('8.8.8.8', 4): 8, ('1.1.1.1', 4): 1}),
                           Counter({'missing': 1}), 1, 2, 'start', 'finish')
        statuses = {'status_events': {'resolved': 8, 'no_match': 1},
                    'status_unique_ips': {'resolved': 1, 'no_match': 1}}
        with TemporaryDirectory() as directory:
            with patch('glamira_pipeline.ip_location.pipeline._bin_info', return_value={'sha256': 's'}), \
                 patch('glamira_pipeline.ip_location.pipeline.scan_in_memory', return_value=scan), \
                 patch('glamira_pipeline.ip_location.pipeline.persist_counter', return_value={'counter_sha256': 's'}), \
                 patch('glamira_pipeline.ip_location.pipeline._lookup_summary', return_value=(statuses, 1)) as lookup, \
                 patch('glamira_pipeline.ip_location.pipeline._record_provenance'), \
                 patch('glamira_pipeline.ip_location.pipeline.publish_collection') as publish:
                result = enrich_collection(source, 'locations', Path('fake.bin'), Path(directory) / 'ok')
                self.assertEqual(result['event_coverage_percent'], 80)
                self.assertEqual(result['unique_ip_coverage_percent'], 50)
                publish.assert_called_once()
                publish.reset_mock()
                source.database.list_collections.return_value = iter([{'info': {'uuid': b'identity'}}])
                lookup.side_effect = ValueError('incomplete staging')
                with self.assertRaises(ValueError):
                    enrich_collection(source, 'locations', Path('fake.bin'), Path(directory) / 'failed')
                publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
