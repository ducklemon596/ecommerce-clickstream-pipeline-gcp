"""Distinct product-ID aggregation shape and result accounting (no MongoDB)."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from glamira_pipeline.products.catalog_ids import aggregation_pipeline, merge_field_counts, write_ids


class AggregationPipelineTests(unittest.TestCase):
    def test_reads_all_reference_fields_and_excludes_empty_values(self):
        pipeline = aggregation_pipeline()
        refs = pipeline[0]["$project"]["refs"]["$concatArrays"]
        fields = [refs[0][0]["field"], refs[1][0]["field"], refs[2]["$map"]["in"]["field"]]
        self.assertEqual(fields, ["product_id", "viewing_product_id", "cart_products.product_id"])
        self.assertEqual(pipeline[2], {"$match": {"refs.value": {"$nin": [None, ""]}}})

    def test_pipeline_never_writes(self):
        stages = {next(iter(stage)) for stage in aggregation_pipeline()}
        self.assertFalse(stages & {"$out", "$merge"})


class WriteIdsTests(unittest.TestCase):
    def test_merges_types_and_counts_ids_per_field(self):
        rows = [
            # int32 cart references and string event references for one product.
            {"product_id": "100002", "references": 6, "bson_types": ["string", "int"],
             "by_field": [{"k": "product_id", "v": 3}, {"k": "cart_products.product_id", "v": 2},
                          {"k": "product_id", "v": 1}]},
            {"product_id": "abc", "references": 1, "bson_types": ["string"],
             "by_field": [{"k": "viewing_product_id", "v": 1}]},
            {"product_id": None, "references": 2, "bson_types": ["object"],
             "by_field": [{"k": "product_id", "v": 2}]},
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ids.jsonl"
            totals = write_ids(rows, path)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(records[0]["by_field"], {"cart_products.product_id": 2, "product_id": 4})
        self.assertEqual(records[0]["bson_types"], ["int", "string"])
        self.assertEqual(totals["distinct_ids"], 2)
        self.assertEqual(totals["non_numeric_ids"], 1)
        self.assertEqual(totals["unconvertible_groups"], 1)
        self.assertEqual(totals["references"], 9)
        self.assertEqual(totals["ids_by_field"]["product_id"], 2)

    def test_failed_stream_leaves_no_partial_output(self):
        def broken():
            yield {"product_id": "1", "references": 1, "bson_types": ["string"],
                   "by_field": [{"k": "product_id", "v": 1}]}
            raise RuntimeError("cursor lost")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ids.jsonl"
            with self.assertRaises(RuntimeError):
                write_ids(broken(), path)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_merge_field_counts(self):
        self.assertEqual(merge_field_counts([{"k": "b", "v": 1}, {"k": "a", "v": 2}, {"k": "b", "v": 3}]),
                         {"a": 2, "b": 4})


if __name__ == "__main__":
    unittest.main()
