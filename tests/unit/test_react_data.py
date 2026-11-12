"""react_data parsing, response classification and crawl resume/stop rules (offline)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import random
import unittest

from glamira_pipeline.products.crawl import CrawlStopped, crawl, export, open_checkpoint, select_ids
from glamira_pipeline.products.http_client import FetchResult, classify, react_data_url
from glamira_pipeline.products.react_data import parse_option_values, parse_product
from glamira_pipeline.products.stores import Store


def payload(product_id=100002, gender="women"):
    """Return a trimmed react_data payload shaped like the observed response."""
    return {
        "product_id": product_id, "name": "Engagement Ring Palmier", "sku": "PALMIER",
        "attribute_set_id": 55, "attribute_set": "diamonds", "type_id": "simple",
        "product_type": "ring", "product_type_value": "1", "collection": "halo",
        "collection_id": "4377", "gender": gender, "store_code": "glgb", "category": 0,
        "category_name": "", "price": "720.000000", "min_price": "245.000000",
        "max_price": "38075.000000", "min_price_format": "£245.00", "max_price_format": "£38,075.00",
        "product_price": {"currencyCode": "GBP", "price": "720.000000", "full_price": 1276,
                          "full_price_format": "£1,276", "sale_price": "1084.60",
                          "sale_price_format": "£1,085", "includeTax": True, "defaultTax": 20,
                          "currentTax": 20, "use_gold_price": True, "prices": {"basePrice": {"amount": 600}},
                          "tierPrices": []},
        "options": [
            {"option_id": "323853", "part_type": "stone1", "type": "stone", "title": "Centre Stone",
             "default_title": "Stone/Diamonds", "is_require": 1, "sort_order": "10",
             "values": [{"option_type_id": "2752176", "sku": "diamond-Brillant", "title": "Diamond",
                         "default_title": "Diamond", "store_title": "Diamond", "is_default": False,
                         "price": "2991.00", "price_type": "fixed"},
                        {"option_type_id": "2752180", "sku": "diamond-zirconia", "title": "Zirconia",
                         "default_title": "Zirkonia", "store_title": None, "is_default": True,
                         "price": "0.00", "price_type": "fixed"}]},
            {"option_id": "323860", "part_type": "engraving_field", "type": "field",
             "title": "Engraving", "default_title": "Gravur", "is_require": 0, "sort_order": "50"},
        ],
    }


async def no_sleep(seconds):
    return None


UK = Store("www.glamira.co.uk", "GBP", "glgb")
US = Store("www.glamira.com", "USD", "glus")


class ParseTests(unittest.TestCase):
    def test_product_keeps_source_types_and_all_price_fields(self):
        record = parse_product(payload(gender=False), host=UK.host, requested_currency="GBP")
        self.assertIs(record["gender"], False)
        self.assertEqual(record["product_id"], "100002")
        self.assertEqual((record["price"], record["sale_price"], record["full_price"]),
                         ("720.000000", "1084.60", 1276))
        self.assertEqual(record["currency"], "GBP")
        self.assertEqual(json.loads(record["prices_json"]), {"basePrice": {"amount": 600}})
        self.assertEqual(record["option_count"], 2)

    def test_missing_gender_is_null_not_false(self):
        data = payload()
        del data["gender"]
        self.assertIsNone(parse_product(data, host=UK.host, requested_currency="GBP")["gender"])

    def test_option_values_map_ids_to_tokens_and_keep_valueless_options(self):
        rows = parse_option_values(payload())
        self.assertEqual(len(rows), 3)
        self.assertEqual((rows[1]["value_id"], rows[1]["value_sku"], rows[1]["is_default"]),
                         ("2752180", "diamond-zirconia", True))
        self.assertEqual((rows[2]["part_type"], rows[2]["value_id"]), ("engraving_field", None))


class ClassifyTests(unittest.TestCase):
    def test_statuses(self):
        body = json.dumps(payload()).encode()
        self.assertEqual(classify(200, "application/json", body)[0], "ok")
        self.assertEqual(classify(404, "application/json", b'{"error":"Product not found"}')[0], "not_found")
        self.assertEqual(classify(403, "text/html", b"Access Denied")[0], "blocked")
        self.assertEqual(classify(429, "application/json", b"{}")[0], "blocked")
        self.assertEqual(classify(200, "text/html", b"<html>challenge</html>")[0], "blocked")
        self.assertEqual(classify(503, "text/html", b"")[0], "error")
        self.assertEqual(classify(200, "application/json", b"not json")[0], "error")

    def test_url_rejects_non_numeric_ids(self):
        with self.assertRaises(ValueError):
            react_data_url(UK.host, "1/../x", "GBP")


def fake_fetcher(responses):
    """Return a fetcher yielding scripted statuses per (host, id) and a call log."""
    calls = []

    def fetcher(url):
        host = url.split("/")[2]
        product_id = url.split("/id/")[1].split("/")[0]
        calls.append((host, product_id))
        status = responses.get((host, product_id), "ok")
        data = payload(int(product_id)) if status == "ok" else None
        return FetchResult(status, url, {"ok": 200, "not_found": 404, "blocked": 403}.get(status),
                           0.1, 10, payload=data, raw=json.dumps(data).encode() if data else None)
    return fetcher, calls


class CrawlTests(unittest.TestCase):
    def run_crawl(self, directory, ids, responses, **kwargs):
        fetcher, calls = fake_fetcher(responses)
        connection = open_checkpoint(Path(directory) / "crawl.sqlite3")
        try:
            metrics = crawl(connection, ids, stores=(US, UK), fetcher=fetcher, sleep=no_sleep,
                            clock=lambda: 0.0, rng=random.Random(1), **kwargs)
            return metrics, calls, export(connection, Path(directory))
        finally:
            connection.close()

    def test_falls_back_only_on_not_found_and_resume_skips_finished(self):
        with TemporaryDirectory() as directory:
            responses = {(US.host, "2"): "not_found", (US.host, "3"): "not_found", (UK.host, "3"): "not_found"}
            metrics, calls, counts = self.run_crawl(directory, ["1", "2", "3"], responses)
            self.assertEqual(calls, [(US.host, "1"), (US.host, "2"), (UK.host, "2"), (US.host, "3"), (UK.host, "3")])
            self.assertEqual((counts["products_rows"], counts["products_not_found"]), (2, 1))
            self.assertEqual(counts["option_values_rows"], 6)
            products = [json.loads(l) for l in (Path(directory) / "products.jsonl").read_text().splitlines()]
            self.assertEqual([p["host"] for p in products], [US.host, UK.host])
            metrics, calls, _ = self.run_crawl(directory, ["1", "2", "3"], responses)
            self.assertEqual((calls, metrics["skipped_finished"]), ([], 3))

    def test_block_stops_without_trying_other_stores(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(CrawlStopped) as stop:
                self.run_crawl(directory, ["1", "2", "3"], {(US.host, "2"): "blocked"})
            self.assertEqual(stop.exception.metrics["request_statuses"], {"ok": 1, "blocked": 1})
            # Rerun resumes at the blocked ID and does not repeat finished ones.
            _, calls, _ = self.run_crawl(directory, ["1", "2", "3"], {})
            self.assertEqual(calls, [(US.host, "2"), (US.host, "3")])

    def test_pacing_adds_jitter_between_requests(self):
        for concurrency in (1, 3):
            pauses = []

            async def record(seconds):
                pauses.append(seconds)
            fetcher, _ = fake_fetcher({})
            with TemporaryDirectory() as directory:
                connection = open_checkpoint(Path(directory) / "crawl.sqlite3")
                crawl(connection, ["1", "2", "3", "4"], stores=(UK,), fetcher=fetcher, sleep=record,
                      clock=lambda: 0.0, delay_s=2, jitter_s=1, concurrency=concurrency, rng=random.Random(1))
                connection.close()
            self.assertEqual(len(pauses), 3)
            self.assertTrue(all(2 <= p <= 3 for p in pauses))

    def test_concurrent_block_stops_new_requests(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(CrawlStopped):
                self.run_crawl(directory, [str(i) for i in range(1, 20)], {(US.host, "3"): "blocked"},
                               concurrency=3)
            connection = open_checkpoint(Path(directory) / "crawl.sqlite3")
            attempts = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            connection.close()
            self.assertLessEqual(attempts, 5)

    def test_seeded_sample_is_reproducible(self):
        ids = [str(i) for i in range(100)]
        self.assertEqual(select_ids(ids, sample=5, seed=7, limit=None), select_ids(ids, sample=5, seed=7, limit=None))
        self.assertEqual(len(select_ids(ids, sample=5, seed=7, limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
