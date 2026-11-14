"""Synthetic checks for per-event-type schema profiling and its reports."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from bson import Decimal128, Int64, ObjectId

from glamira_pipeline.profiling.report import render_markdown, write_outputs
from glamira_pipeline.profiling.schema import (MISSING_EVENT_TYPE, SchemaProfile, bson_type,
                                               container_count, missing_count)
from glamira_pipeline.sampling.mongo_sample import sample_documents, uses_random_cursor

METADATA = {"namespace": "countly.summary", "observed_at": "2026-11-15T00:00:00+00:00",
            "requested": 3, "collection_estimate": 100, "method": "synthetic", "git_sha": None}


class BsonTypeTests(unittest.TestCase):
    def test_names_match_bson(self):
        cases = [(None, "null"), (True, "bool"), (1, "int"), (2**40, "long"), (Int64(1), "long"),
                 (1.5, "double"), ("x", "string"), ({}, "object"), ([], "array"),
                 (ObjectId(), "objectId"), (Decimal128("1.0"), "decimal"),
                 (datetime(2019, 1, 1, tzinfo=timezone.utc), "date"), (b"x", "binData")]
        for value, expected in cases:
            self.assertEqual(bson_type(value), expected, value)


class SchemaProfileTests(unittest.TestCase):
    def test_top_level_missing_null_empty_are_separate_per_event_type(self):
        profile = SchemaProfile()
        for document in ({"collection": "checkout_success", "order_id": "1"},
                         {"collection": "checkout_success", "order_id": None},
                         {"collection": "checkout_success", "order_id": "  "},
                         {"collection": "checkout_success"},
                         {"collection": "view_product_detail", "product_id": "9"}):
            profile.observe(document)
        checkout = profile.types["checkout_success"]
        stats = checkout.paths["order_id"]
        self.assertEqual(checkout.events, 4)
        self.assertEqual((stats.present, stats.null, stats.empty), (3, 1, 1))
        self.assertEqual(missing_count(checkout, "order_id"), 1)
        self.assertEqual(stats.types, {"string": 2, "null": 1})
        self.assertNotIn("order_id", profile.types["view_product_detail"].paths)

    def test_nested_array_paths_are_counted_against_their_elements(self):
        profile = SchemaProfile()
        profile.observe({"collection": "checkout_success", "cart_products": [
            {"product_id": 1, "price": "10.0", "option": [{"value_id": "5"}, {}]},
            {"product_id": 2},
            "not-an-object",
        ]})
        tp = profile.types["checkout_success"]
        self.assertEqual(container_count(tp, "cart_products[]"), 3)
        self.assertEqual(tp.paths["cart_products[]"].types, {"object": 2, "string": 1})
        self.assertEqual(container_count(tp, "cart_products[].price"), 2)
        self.assertEqual(missing_count(tp, "cart_products[].price"), 1)
        self.assertEqual(container_count(tp, "cart_products[].option[].value_id"), 2)
        self.assertEqual(missing_count(tp, "cart_products[].option[].value_id"), 1)
        self.assertEqual(tp.paths["cart_products[].option[]"].empty, 1)

    def test_missing_or_non_string_event_type_is_labelled(self):
        profile = SchemaProfile()
        for document in ({}, {"collection": None}, {"collection": 3}):
            profile.observe(document)
        self.assertEqual(profile.types[MISSING_EVENT_TYPE].events, 3)

    def test_bounds_are_reported(self):
        profile = SchemaProfile(max_array_items=2, max_paths_per_type=3, max_depth=2)
        profile.observe({"collection": "e", "a": [1, 2, 3], "b": {"c": {"d": 1}}, "x": 1, "y": 2})
        tp = profile.types["e"]
        self.assertEqual(tp.truncated_arrays, 1)
        self.assertEqual(tp.paths["a[]"].present, 2)
        self.assertGreater(tp.dropped_paths, 0)
        self.assertLessEqual(len(tp.paths), 3)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.profile = SchemaProfile()
        self.profile.observe({"collection": "a|b", "ip": "192.0.2.1", "email_address": "x@example.com"})
        self.profile.observe({"collection": "a|b"})

    def test_markdown_has_rates_and_no_values(self):
        text = render_markdown(self.profile, METADATA)
        self.assertIn("`a\\|b`", text)
        self.assertIn("| `ip` | 2 | 50.00% | 50.00% | 0.00% | 0.00% | string 1 |", text)
        self.assertNotIn("192.0.2.1", text)
        self.assertNotIn("example.com", text)

    def test_write_outputs_json_counts(self):
        with TemporaryDirectory() as tmp:
            md, js = Path(tmp) / "r.md", Path(tmp) / "nested/p.json"
            write_outputs(self.profile, METADATA, md, js)
            data = json.loads(js.read_text())
            self.assertEqual(data["documents"], 2)
            self.assertEqual(data["event_types"]["a|b"]["paths"]["ip"]["missing"], 1)
            self.assertNotIn("192.0.2.1", js.read_text())
            self.assertTrue(md.read_text().startswith("# Schema profile"))


class MongoSampleTests(unittest.TestCase):
    def test_random_cursor_threshold(self):
        self.assertTrue(uses_random_cursor(100_000, 41_432_473))
        self.assertFalse(uses_random_cursor(5, 100))

    def test_sample_pipeline_and_size_validation(self):
        collection = mock.MagicMock()
        collection.aggregate.return_value.__enter__.return_value = iter([{"_id": 1}])
        self.assertEqual(list(sample_documents(collection, 10)), [{"_id": 1}])
        collection.aggregate.assert_called_once_with([{"$sample": {"size": 10}}], batchSize=1_000)
        with self.assertRaises(ValueError):
            list(sample_documents(collection, 0))


if __name__ == "__main__":
    unittest.main()
