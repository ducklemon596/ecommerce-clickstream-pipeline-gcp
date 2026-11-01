"""Synthetic checks for sample quality metrics and report generation."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from bson import Decimal128, ObjectId, json_util

from glamira_pipeline.quality.assessment import Assessment, assess_sample
from glamira_pipeline.quality.duplicates import duplicate_summary
from glamira_pipeline.quality.reports import DETAIL_FILES, write_reports


class QualityTests(unittest.TestCase):
    def test_nulls_distinguish_missing_and_explicit_null(self):
        assessment = Assessment()
        for document in ({"value": None}, {"value": ""}, {}, {"value": 0}, {"value": False}):
            assessment.observe(document)
        self.assertEqual(assessment.rows, 5)
        self.assertEqual(assessment.nulls.present["value"], 4)
        self.assertEqual(assessment.nulls.explicit_null["value"], 1)
        self.assertEqual(assessment.rows - assessment.nulls.present["value"], 1)

    def test_duplicate_ids_and_ip_timestamp_pairs_are_separate(self):
        assessment = Assessment()
        shared_id = ObjectId()
        for doc in (
            {"_id": shared_id, "ip": "192.0.2.1", "time_stamp": 1},
            {"_id": shared_id, "ip": "192.0.2.1", "time_stamp": 1},
            {"_id": ObjectId(), "ip": "192.0.2.1", "time_stamp": 1},
            {"ip": None, "time_stamp": 1},
            {"ip": "", "time_stamp": 1},
        ):
            assessment.observe(doc)
        self.assertEqual(duplicate_summary(assessment.duplicates.mongo_ids), (1, 1))
        self.assertEqual(duplicate_summary(assessment.duplicates.pairs), (1, 2))
        self.assertEqual(assessment.duplicates.pair_usable, 3)

    def test_timestamps_use_fixed_utc_reference_and_reject_bad_values(self):
        reference = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assessment = Assessment(now=reference)
        for value in (reference.timestamp() - 1, reference.timestamp() + 1, "not-a-time", True, float("nan"), 10**100, None):
            assessment.observe({"time_stamp": value})
        t = assessment.timestamps
        self.assertEqual((t.valid, t.future, t.invalid, t.missing), (2, 1, 4, 1))
        self.assertEqual(t.minimum, reference - timedelta(seconds=1))
        self.assertEqual(t.maximum, reference + timedelta(seconds=1))

    def test_local_times_are_checked_without_timezone_assumptions(self):
        assessment = Assessment()
        for value in ("2020-06-04 8:21:27", "2020-06-04 12:21:27", "bad", 123, None):
            assessment.observe({"local_time": value})
        counts = assessment.timestamps
        self.assertEqual((counts.local_valid, counts.local_invalid, counts.local_missing), (2, 2, 1))
        self.assertEqual(counts.local_minimum, datetime(2020, 6, 4, 8, 21, 27))
        self.assertEqual(counts.local_maximum, datetime(2020, 6, 4, 12, 21, 27))

    def test_checkout_price_signs_and_currencies(self):
        assessment = Assessment()
        assessment.observe({
            "collection": "checkout_success", "currency": "EUR", "cart_products": [
                {"price": "-1.234,50", "currency": "€"},
                {"price": "−4.00", "currency": "$"},
                {"price": "1.234,56", "currency": ""},
                {"price": -3, "currency": None},
                {"price": Decimal128("-0.25")},
                {"price": "£-99", "currency": "EUR"},
                {"price": None}, {"price": ""}, {"price": True}, {}, "not an object",
            ],
        })
        assessment.observe({"collection": "view_shopping_cart", "cart_products": [{"currency": "GBP"}]})
        t = assessment.transactions
        self.assertEqual((t.checkout_events, t.checkout_items, t.checkout_malformed_items), (1, 10, 1))
        self.assertEqual((t.price_string, t.price_string_negative_sign, t.price_string_no_leading_number), (4, 2, 1))
        self.assertEqual((t.price_numeric, t.price_numeric_negative), (2, 2))
        self.assertEqual((t.price_null, t.price_empty, t.price_invalid, t.price_missing), (1, 1, 1, 1))
        self.assertEqual(t.top_level_currencies.values["EUR"], 1)
        self.assertEqual(t.cart_item_currencies.values["€"], 1)
        self.assertEqual(t.cart_item_currencies.values["GBP"], 1)
        self.assertEqual((t.cart_item_currencies.empty, t.cart_item_currencies.null), (1, 1))

    def test_ip_counts_separate_completeness_and_syntax(self):
        assessment = Assessment()
        for doc in ({}, {"ip": None}, {"ip": ""}, {"ip": 1}, {"ip": "not-an-ip"}, {"ip": "192.0.2.1"}, {"user_ip": "2001:db8::1"}):
            assessment.observe(doc)
        ip = assessment.ips
        self.assertEqual((ip.missing, ip.null, ip.empty, ip.invalid_type, ip.invalid_format, ip.ipv4, ip.ipv6), (1, 1, 1, 1, 1, 1, 1))

    def test_quality_report_set_links_and_redacts_addresses(self):
        assessment = Assessment()
        assessment.observe({"_id": ObjectId(), "collection": "checkout_success", "ip": "192.0.2.123", "time_stamp": 1, "cart_products": [{"price": "-12,50", "currency": "€"}]})
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text("[]")
            paths = write_reports(assessment, sample, root / "reports")
            self.assertEqual(len(paths), 7)
            self.assertTrue(all(path.is_file() for path in paths))
            summary = paths[0].read_text()
            for name in DETAIL_FILES:
                self.assertIn(f"data_quality/{name}", summary)
            for path in paths:
                self.assertNotIn("192.0.2.123", path.read_text())
            self.assertIn("Not assessed", (root / "reports/data_quality/revenue.md").read_text())

    def test_sample_cap_and_invalid_input_preserve_existing_report(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text(json_util.dumps([{"_id": 1}, {"_id": 2}]))
            assessment = assess_sample(sample, limit=1)
            self.assertEqual(assessment.rows, 1)
            self.assertTrue(assessment.truncated)
            report = root / "reports/data_quality_report.md"
            report.parent.mkdir()
            report.write_text("previous report")
            sample.write_text('[{"_id":1},]')
            with self.assertRaises(ValueError):
                assess_sample(sample, limit=2)
            self.assertEqual(report.read_text(), "previous report")

    def test_identifier_report_uses_mongo_id(self):
        assessment = Assessment()
        assessment.observe({"_id": ObjectId()})
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text("[]")
            report = write_reports(assessment, sample, root / "reports")[0].read_text()
            self.assertIn("| Duplicate identifiers | _id:", report)
            self.assertNotIn("event_id", report)

    def test_duplicate_ip_versions_and_exact_value_grouping(self):
        assessment = Assessment()
        for event, ip, timestamp in (
            ("view", "192.0.2.1", 1), ("add", "192.0.2.1", 1), ("view", "192.0.2.1", 1),
            ("view", "2001:db8::1", 2), ("view", "2001:db8::1", 2),
            ("view", "::ffff:192.0.2.1", 3), ("view", "::ffff:192.0.2.1", 3),
            ("view", "not-an-ip", 4), ("view", "not-an-ip", 4),
            ("view", "2001:0db8::1", 2),
        ):
            assessment.observe({"_id": ObjectId(), "collection": event, "ip": ip, "time_stamp": timestamp})
        duplicates = assessment.duplicates
        self.assertEqual(duplicate_summary(duplicates.pairs), (4, 5))
        self.assertEqual(Counter(duplicates.pair_versions.values()), {"ipv4": 1, "ipv6": 2, "invalid": 1})
        self.assertEqual(len(duplicates.mixed_event_groups), 1)
        repeated_rows = sum(duplicates.pairs[key] for key in duplicates.pair_versions)
        self.assertEqual(repeated_rows, 9)
        self.assertNotIn("192.0.2.1", repr(duplicates))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text("[]")
            paths = write_reports(assessment, sample, root / "reports")
            self.assertEqual(len(paths), 7)
            public = (root / "reports/data_quality/duplicates.md").read_text()
            self.assertIn("| IPv4 | 1 | 3 | 2 |", public)
            self.assertIn("| IPv6 | 2 | 4 | 2 |", public)
            self.assertIn("| Invalid address | 1 | 2 | 1 |", public)
            self.assertIn("| Valid IPv4 | 3 |", (root / "reports/data_quality/ip_addresses.md").read_text())
            self.assertIn("| Valid IPv6 | 5 |", (root / "reports/data_quality/ip_addresses.md").read_text())
            self.assertNotIn("192.0.2.1", public)
            self.assertNotIn("event_id", public)
            self.assertNotIn("Example repeated pairs", public)
            self.assertEqual(list(root.rglob("*duplicate_ip_timestamp_samples*")), [])

    def test_cli_rejects_removed_duplicate_example_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "glamira_pipeline.quality.cli", "--max-duplicate-examples", "1"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_cli_does_not_log_malformed_sample_values(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text('[{"_id":{"$oid":"secret@example.com"}}]')
            result = subprocess.run(
                [sys.executable, "-m", "glamira_pipeline.quality.cli", "--sample", str(sample), "--output-dir", str(root / "reports")],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("secret@example.com", result.stdout + result.stderr)
            self.assertFalse((root / "reports/data_quality_report.md").exists())


if __name__ == "__main__":
    unittest.main()
