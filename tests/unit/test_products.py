"""Focused normalization, transactional recovery and count accounting tests."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from glamira_pipeline.products.normalize import InvalidConfiguration, normalize_event
from glamira_pipeline.products.pipeline import run_deduplication
from glamira_pipeline.products.storage import commit_batch, open_state, read_state


def event(query="", **changes):
    """Return a synthetic detail event with customizable source fields."""
    return {"collection": "view_product_detail", "product_id": "101", "store_id": "7",
            "current_url": "https://www.glamira.co.uk/ring.html" + query,
            "option": [], **changes}


class ProductNormalizationTests(unittest.TestCase):
    def test_order_tracking_and_html_escaping(self):
        first, _ = normalize_event(event("?alloy=yellow-375&amp;diamond=ruby&gclid=secret"))
        second, _ = normalize_event(event("?fbclid=secret&diamond=ruby&alloy=yellow-375&utm_source=ad"))
        self.assertEqual(first["normalized_options"], second["normalized_options"])
        self.assertEqual(first["normalized_options"], {"alloy": "yellow-375", "diamond": "ruby"})
        self.assertEqual(first["store_id"], "7")
        self.assertEqual(first["hostname"], "www.glamira.co.uk")

    def test_empty_unspecified_and_unknown_values(self):
        for query in ("", "?alloy=&diamond=", "?fbclid=x"):
            self.assertEqual(normalize_event(event(query))[0]["normalized_options"], {})
        row, warnings = normalize_event(event("?custom=Original%20Text&alloy=WHITE-585"))
        self.assertEqual(row["normalized_options"], {"alloy": "WHITE-585", "custom": "Original Text"})
        self.assertIn("unknown_parameters_retained", warnings)

    def test_duplicate_values_and_conflicts(self):
        row, _ = normalize_event(event("?alloy=&alloy=red&alloy=red"))
        self.assertEqual(row["normalized_options"], {"alloy": "red"})
        with self.assertRaisesRegex(InvalidConfiguration, "conflicting"):
            normalize_event(event("?alloy=red&alloy=white"))

    def test_invalid_fields_and_malformed_urls(self):
        for changes in ({"product_id": None}, {"store_id": 12}, {"current_url": "relative/path"},
                        {"current_url": "https://[bad"}, {"current_url": "https://host.com/?x=%QQ"},
                        {"current_url": "https://host.com/?;alloy=red"}):
            with self.subTest(changes=changes), self.assertRaises(InvalidConfiguration):
                normalize_event(event(**changes))

    def test_option_ids_do_not_supply_defaults(self):
        row, warnings = normalize_event(event(option=[{"option_label": "alloy", "value_id": "999"}]))
        self.assertEqual(row["normalized_options"], {})
        self.assertIn("option_values_not_comparable", warnings)

    def test_unknown_parameters_are_not_silently_classified_as_tracking(self):
        row, _ = normalize_event(event("?smartid=3657&discountid=16&custom=x"))
        self.assertEqual(row["normalized_options"], {"smartid": "3657", "discountid": "16", "custom": "x"})


class ProductPipelineTests(unittest.TestCase):
    def test_current_urls_from_all_events_resolve_without_using_referrers(self):
        records = [
            {"collection": "view_home_page", "referrer_url": "https://www.glamira.co.uk/referrer-only.html"},
            event("?alloy=white"),
            {"collection": "select_product_option", "product_id": "202", "store_id": "7",
             "current_url": "https://www.glamira.co.uk/other.html",
             "referrer_url": "https://www.glamira.co.uk/another-referrer.html"},
            {"collection": "view_static_page", "current_url": "https://www.glamira.co.uk/about.html"},
            {"collection": "view_listing_page", "current_url": "https://www.glamira.co.uk/rings/"},
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text(json.dumps(records))
            result = run_deduplication(root / "out", sample=sample, batch_size=1)
            rows = [json.loads(line) for line in (root / "out" / "product_urls.jsonl").read_text().splitlines()]
            product = next(row for row in rows if row["source_url"].endswith("alloy=white"))
            self.assertEqual(product["occurrence_count"], 1)
            self.assertEqual(product["product_store_mappings"], [
                {"id_field": "product_id", "product_id": "101", "store_id": "7"}])
            self.assertEqual(result["product_urls_unique"], 2)
            self.assertEqual(result["unverified_product_urls_unique"], 1)
            self.assertEqual(result["all_valid_urls_unique"], 4)
            self.assertFalse(any("referrer" in row["source_url"] for row in rows))

    def test_checkout_urls_do_not_establish_product_page_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text(json.dumps([event(current_url="https://www.glamira.co.uk/checkout/cart/")]))
            result = run_deduplication(root / "out", sample=sample)
            self.assertEqual(result["product_urls_unique"], 0)

    def test_magento_product_routes_and_trailing_slashes(self):
        from glamira_pipeline.products.urls import product_path
        self.assertTrue(product_path('/catalog/product/view/id/95560'))
        self.assertTrue(product_path('/glgb/catalog/product/view/id/95560/'))
        self.assertTrue(product_path('/ring.html/'))
        self.assertFalse(product_path('/checkout/cart/configure/id/95560/'))

    def test_counts_store_product_host_and_completed_rerun(self):
        records = [event("?alloy=red&diamond=ruby"), event("?diamond=ruby&alloy=red"),
                   event(product_id="102"), event(store_id="8"),
                   event(current_url="https://www.glamira.sk/ring.html"), event(),
                   event(product_id=None), {"collection": "other"}]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text(json.dumps(records))
            output = root / "output"
            first = run_deduplication(output, sample=sample, limit=8, batch_size=2)
            second = run_deduplication(output, sample=sample, limit=8, batch_size=3)
            self.assertEqual(first["documents_scanned"], 8)
            self.assertEqual(first["unique_configurations"], 5)
            self.assertEqual(first["duplicate_events"], 1)
            self.assertEqual(first["rejected_events"], 1)
            self.assertEqual(first["occurrence_sum"], 6)
            self.assertEqual(second["occurrence_sum"], 6)
            rows = [json.loads(line) for line in (output / "configurations.jsonl").read_text().splitlines()]
            self.assertEqual(sum(row["occurrence_count"] for row in rows), 6)
            self.assertEqual((output / "configurations.sqlite3").stat().st_mode & 0o777, 0o600)
            sample.write_text("[]")
            with self.assertRaisesRegex(ValueError, "changed"):
                run_deduplication(output, sample=sample, limit=8)

    def test_interruption_resume_does_not_double_count(self):
        with TemporaryDirectory() as directory:
            sample = Path(directory) / "sample.json"
            sample.write_text(json.dumps([event()] * 7))
            output = Path(directory) / "output"
            calls = 0

            def fail_second(connection, batch):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected interruption")
                commit_batch(connection, batch)

            with patch("glamira_pipeline.products.pipeline.commit_batch", side_effect=fail_second):
                with self.assertRaises(OSError):
                    run_deduplication(output, sample=sample, limit=7, batch_size=2)
            self.assertFalse((output / "configurations.jsonl").exists())
            result = run_deduplication(output, sample=sample, limit=7, batch_size=2)
            self.assertEqual(result["occurrence_sum"], 7)
            self.assertEqual(result["unique_configurations"], 1)

    def test_batch_transaction_rolls_back_counts_and_rows(self):
        with TemporaryDirectory() as directory:
            connection = open_state(Path(directory) / "state.sqlite3", {})
            try:
                with patch("glamira_pipeline.products.storage.normalize_event", side_effect=[normalize_event(event()), RuntimeError("crash")]):
                    with self.assertRaises(RuntimeError):
                        commit_batch(connection, [event(), event()])
                self.assertIsNone(read_state(connection, "counts"))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM configurations").fetchone()[0], 0)
            finally:
                connection.close()

    def test_exact_limit_rejects_short_input(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.json"
            sample.write_text(json.dumps([event()]))
            with self.assertRaisesRegex(ValueError, "fewer"):
                run_deduplication(root / "output", sample=sample, limit=2)
            self.assertFalse((root / "output" / "configurations.jsonl").exists())

    def test_mongodb_reader_projection_sort_batch_and_resume(self):
        from bson import ObjectId
        from unittest.mock import MagicMock
        from glamira_pipeline.products.source import mongo_events, PROJECTION
        last_id, next_id = ObjectId(), ObjectId()
        collection = MagicMock()
        cursor = collection.find.return_value
        cursor.sort.return_value = cursor
        cursor.batch_size.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__iter__.return_value = iter([{"_id": next_id}])
        self.assertEqual(list(mongo_events(collection, last_id, 1, 5000)), [{"_id": next_id}])
        collection.find.assert_called_once_with({"_id": {"$gt": last_id}}, PROJECTION)
        cursor.sort.assert_called_once_with("_id", 1)
        cursor.batch_size.assert_called_once_with(5000)
        cursor.limit.assert_called_once_with(1)
        cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
