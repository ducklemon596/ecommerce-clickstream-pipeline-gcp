"""react_data documents, response classification and crawl checkpoint rules (offline)."""
from datetime import datetime, timezone
from decimal import Decimal
import asyncio
import json
import random
import unittest

from bson.decimal128 import Decimal128

from glamira_pipeline.products.crawl import CrawlStopped, crawl
from glamira_pipeline.products.http_client import FetchResult, classify, react_data_url
from glamira_pipeline.products.mongo_store import (FINAL_STATUSES, OPTION_SCHEMA, PRODUCT_SCHEMA,
                                                    MongoProductStore)
from glamira_pipeline.products.react_data import (DATA_FIELDS, option_value_documents, product_document,
                                                  to_decimal128)
from glamira_pipeline.products.stores import Store

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)
SOURCE = {"host": "www.glamira.com", "store_code": "glus", "url": "u", "requested_currency": "USD"}


def payload(product_id=100002, gender="women", price="720.000000"):
    """Return a trimmed react_data payload shaped like the observed response."""
    return {
        "product_id": product_id, "name": "Engagement Ring Palmier", "sku": "PALMIER",
        "attribute_set_id": 55, "attribute_set": "diamonds", "type_id": "simple",
        "product_type": "ring", "product_type_value": "1", "collection": "halo",
        "collection_id": "4377", "gender": gender, "category": 0, "category_name": "",
        "price": price, "min_price": "245.000000", "max_price": None,
        "min_price_format": "$245.00", "max_price_format": "$38,075.00",
        "product_price": {"currencyCode": "USD", "full_price": 1276, "full_price_format": "$1,276",
                          "sale_price": "1084.60", "sale_price_format": "$1,085", "includeTax": True,
                          "defaultTax": 20, "currentTax": 20, "use_gold_price": True,
                          "prices": {"basePrice": {"amount": 720}}, "tierPrices": []},
        "options": [
            {"option_id": "323853", "part_type": "stone1", "type": "stone", "title": "Centre Stone",
             "default_title": "Stone/Diamonds", "is_require": 1, "sort_order": "10",
             "values": [{"option_type_id": "2752176", "sku": "diamond-Brillant", "title": "Diamond",
                         "default_title": "Diamond", "store_title": "Diamond", "is_default": False,
                         "price": "2991.00", "price_type": "fixed"},
                        {"option_type_id": 2752180, "sku": "diamond-zirconia", "title": "Zirconia",
                         "default_title": "Zirkonia", "store_title": None, "is_default": 1,
                         "price": 0, "price_type": "fixed"}]},
            {"option_id": "323860", "part_type": None, "type": "field", "title": "Engraving",
             "default_title": "Gravur", "is_require": 0, "sort_order": "50"},
        ],
    }


def document(status="success", data=None, **changes):
    return product_document(product_id=changes.pop("product_id", "100002"), status=status,
                            status_code=changes.pop("status_code", 200), payload=data,
                            source=SOURCE, run_id="run1", crawled_at=NOW, **changes)


class DocumentTests(unittest.TestCase):
    def test_success_keeps_source_types_and_converts_prices(self):
        doc = document(data=payload(gender=False))
        self.assertIs(doc["gender"], False)
        self.assertEqual(doc["_id"], "100002")
        self.assertEqual(doc["price"], Decimal128(Decimal("720.000000")))
        self.assertEqual((doc["full_price"], doc["sale_price"]), (Decimal128("1276"), Decimal128("1084.60")))
        self.assertIsNone(doc["max_price"])
        self.assertEqual((doc["currency"], doc["option_count"], doc["category"]), ("USD", 2, 0))
        self.assertFalse({"prices", "prices_json", "tier_prices_json", "quality_flags"} & set(doc))

    def test_every_status_has_the_same_keys_and_null_data(self):
        success = document(data=payload())
        missing = document("not_found", status_code=404)
        self.assertEqual(set(success), set(missing))
        self.assertTrue(all(missing[field] is None for field in DATA_FIELDS))
        self.assertEqual((missing["status"], missing["status_code"]), ("not_found", 404))

    def test_missing_gender_is_null_not_false(self):
        data = payload()
        del data["gender"]
        self.assertIsNone(document(data=data)["gender"])

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            document(data=payload(price="n/a"))
        with self.assertRaises(ValueError):
            document(data=payload(product_id=1))
        with self.assertRaises(ValueError):
            document("weird")
        with self.assertRaises(ValueError):
            to_decimal128(True)

    def test_option_values_use_string_ids_and_keep_valueless_options(self):
        rows = option_value_documents(payload(), run_id="run1", crawled_at=NOW)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]["_id"], {"product_id": "100002", "option_id": "323853", "value_id": "2752180"})
        self.assertEqual((rows[1]["value_sku"], rows[1]["value_price"]), ("diamond-zirconia", Decimal128("0")))
        self.assertEqual((rows[2]["option_type"], rows[2]["value_id"]), ("field", None))

    def test_validators_require_every_document_key(self):
        doc = document(data=payload())
        required = set(PRODUCT_SCHEMA["$jsonSchema"]["required"])
        self.assertEqual(required, set(doc) | {"attempts"})
        option_keys = set(option_value_documents(payload(), run_id="r", crawled_at=NOW)[0])
        self.assertTrue(set(OPTION_SCHEMA["$jsonSchema"]["required"]) <= option_keys)
        self.assertTrue(set(OPTION_SCHEMA["$jsonSchema"]["properties"]) >= option_keys)


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
            react_data_url("www.glamira.com", "1/../x", "USD")


class MemoryStore:
    """In-memory stand-in for MongoProductStore with the same semantics."""

    def __init__(self, run_id="run1"):
        self.run_id, self.products, self.options, self.batches, self.heartbeats = run_id, {}, {}, [], 0

    def load_checkpoint(self, max_attempts):
        finished = {key for key, doc in self.products.items()
                    if doc["status"] in FINAL_STATUSES or (doc["status"] == "error" and doc["attempts"] >= max_attempts)}
        return finished, {key: doc["attempts"] for key, doc in self.products.items() if key not in finished}

    def write_batch(self, items):
        self.batches.append(len(items))
        for item in items:
            self.products[item.product["_id"]] = dict(item.product)
            for row in item.option_values:
                self.options[json.dumps(row["_id"], sort_keys=True)] = row

    def heartbeat(self, progress, metrics=None):
        self.heartbeats += 1


US = Store("www.glamira.com", "USD", "glus")
UK = Store("www.glamira.co.uk", "GBP", "glgb")


async def no_sleep(seconds):
    return None


def fake_fetcher(responses):
    """Return a fetcher yielding scripted statuses per (host, id) and a call log."""
    calls = []

    def fetcher(url):
        host = url.split("/")[2]
        product_id = url.split("/id/")[1].split("/")[0]
        calls.append((host, product_id))
        status = responses.get((host, product_id), "ok")
        data = payload(int(product_id)) if status == "ok" else None
        code = {"ok": 200, "not_found": 404, "blocked": 403, "error": None}[status]
        return FetchResult(status, url, code, 0.1, 10, payload=data,
                           raw=json.dumps(data).encode() if data else None,
                           error="TimeoutError" if status == "error" else None)
    return fetcher, calls


def run(store, ids, responses, **kwargs):
    fetcher, calls = fake_fetcher(responses)
    kwargs.setdefault("stores", (US, UK))
    report = crawl(store, ids, fetcher=fetcher, sleep=no_sleep, clock=lambda: 0.0,
                   rng=random.Random(1), **kwargs)
    return report, calls


class CrawlTests(unittest.TestCase):
    def test_fallback_on_not_found_and_resume_is_a_set_difference(self):
        store = MemoryStore()
        responses = {(US.host, "2"): "not_found", (US.host, "3"): "not_found", (UK.host, "3"): "not_found"}
        _, calls = run(store, ["1", "2", "3"], responses)
        self.assertEqual(calls, [(US.host, "1"), (US.host, "2"), (UK.host, "2"), (US.host, "3"), (UK.host, "3")])
        self.assertEqual({k: d["status"] for k, d in store.products.items()},
                         {"1": "success", "2": "success", "3": "not_found"})
        self.assertEqual(store.products["2"]["source"]["host"], UK.host)
        self.assertEqual(len(store.options), 6)
        # Different order and a new ID: only the new ID is requested.
        report, calls = run(store, ["3", "4", "1", "2"], {})
        self.assertEqual(calls, [(US.host, "4")])
        self.assertEqual(report["progress"]["already_finished"], 3)

    def test_limit_applies_before_skipping_finished(self):
        store = MemoryStore()
        run(store, [str(i) for i in range(1, 11)], {}, limit=3)
        _, calls = run(store, [str(i) for i in range(1, 11)], {}, limit=5)
        self.assertEqual([c[1] for c in calls], ["4", "5"])

    def test_errors_retry_until_max_attempts(self):
        store = MemoryStore()
        for _ in range(3):
            run(store, ["1"], {(US.host, "1"): "error"}, max_attempts=3)
        self.assertEqual((store.products["1"]["status"], store.products["1"]["attempts"]), ("error", 3))
        _, calls = run(store, ["1"], {}, max_attempts=3)
        self.assertEqual(calls, [])
        _, calls = run(store, ["1"], {}, max_attempts=4)
        self.assertEqual((calls, store.products["1"]["status"]), ([(US.host, "1")], "success"))

    def test_block_flushes_buffer_without_counting_an_attempt(self):
        store = MemoryStore()
        with self.assertRaises(CrawlStopped) as stop:
            run(store, ["1", "2", "3"], {(US.host, "2"): "blocked"}, batch_size=100)
        self.assertEqual(stop.exception.metrics["request_statuses"], {"ok": 1, "blocked": 1})
        self.assertEqual(store.products["1"]["status"], "success")
        self.assertEqual((store.products["2"]["status"], store.products["2"]["attempts"]), ("blocked", 0))
        self.assertNotIn("3", store.products)
        _, calls = run(store, ["1", "2", "3"], {})
        self.assertEqual(calls, [(US.host, "2"), (US.host, "3")])

    def test_concurrent_block_stops_new_requests(self):
        store = MemoryStore()
        with self.assertRaises(CrawlStopped):
            run(store, [str(i) for i in range(1, 20)], {(US.host, "3"): "blocked"}, concurrency=3)
        self.assertLessEqual(len(store.products), 5)

    def test_batches_flush_by_size(self):
        store = MemoryStore()
        run(store, [str(i) for i in range(1, 8)], {}, batch_size=3)
        self.assertEqual(store.batches, [3, 3, 1])
        self.assertEqual(store.heartbeats, 3)

    def test_batches_flush_by_time(self):
        store = MemoryStore()
        run(store, ["1", "2", "3"], {}, batch_size=100, flush_interval_s=0)
        self.assertEqual(store.batches, [1, 1, 1])

    def test_unparseable_payload_becomes_error(self):
        store = MemoryStore()
        fetcher, _ = fake_fetcher({})

        def bad(url):
            result = fetcher(url)
            result.payload["price"] = "n/a"
            return result
        crawl(store, ["1"], stores=(US,), fetcher=bad, sleep=no_sleep, clock=lambda: 0.0)
        self.assertEqual(store.products["1"]["status"], "error")
        self.assertIn("parse error", store.products["1"]["error"])

    def test_hangup_stops_gracefully_and_flushes(self):
        import os
        import signal
        store, base = MemoryStore(), fake_fetcher({})[0]

        def hangup_on_first(url):
            if not store.products and not getattr(hangup_on_first, "sent", False):
                hangup_on_first.sent = True
                os.kill(os.getpid(), signal.SIGHUP)  # e.g. the SSH session on the VM closed
            return base(url)
        with self.assertRaises(CrawlStopped) as stopped:
            crawl(store, [str(i) for i in range(1, 50)], stores=(US,), fetcher=hangup_on_first,
                  sleep=asyncio.sleep, rng=random.Random(1), delay_s=0.01)
        self.assertIn("SIGHUP", str(stopped.exception))
        self.assertGreaterEqual(len(store.products), 1)  # in-flight result was flushed
        self.assertLess(len(store.products), 49)

    def test_pacing_adds_jitter_between_request_starts(self):
        for concurrency in (1, 3):
            pauses = []

            async def record(seconds):
                pauses.append(seconds)
            fetcher, _ = fake_fetcher({})
            crawl(MemoryStore(), ["1", "2", "3", "4"], stores=(UK,), fetcher=fetcher, sleep=record,
                  clock=lambda: 0.0, delay_s=2, jitter_s=1, concurrency=concurrency, rng=random.Random(1))
            self.assertEqual(len(pauses), 3)
            self.assertTrue(all(2 <= p <= 3 for p in pauses))


class MongoStoreTests(unittest.TestCase):
    def test_write_batch_upserts_and_never_drops(self):
        calls = []

        class Collection:
            def __init__(self, name):
                self.name = name

            def __getattr__(self, method):
                return lambda *args, **kwargs: calls.append((self.name, method, args, kwargs))

        class Db(dict):
            def __missing__(self, name):
                return Collection(name)

        from glamira_pipeline.products.mongo_store import BatchItem
        item = BatchItem({**document(data=payload()), "attempts": 1},
                         option_value_documents(payload(), run_id="run1", crawled_at=NOW))
        MongoProductStore(Db(), "run1").write_batch([item])
        MongoProductStore(Db(), "run1").write_batch([item])  # replay after a partial failure
        methods = [(name, method) for name, method, _, _ in calls]
        self.assertEqual(methods, [("products", "bulk_write"), ("product_option_values", "bulk_write"),
                                   ("product_option_values", "delete_many")] * 2)
        self.assertEqual(calls[0][2][0][0]._doc, {"$set": item.product})  # no $inc: replay-safe
        self.assertEqual(calls[2][2][0], {"product_id": {"$in": ["100002"]}, "run_id": {"$ne": "run1"}})
        self.assertTrue(all(op._upsert for op in calls[0][2][0] + calls[1][2][0]))


    def test_recheck_not_found_reopens_only_not_found(self):
        rows = [{"_id": "1", "status": "success", "attempts": 1}, {"_id": "2", "status": "not_found", "attempts": 1},
                {"_id": "3", "status": "error", "attempts": 3}, {"_id": "4", "status": "blocked", "attempts": 0}]

        class Products:
            def find(self, *args):
                return [dict(row) for row in rows]
        db = {"products": Products()}
        self.assertEqual(MongoProductStore(db, "r").load_checkpoint(3), ({"1", "2", "3"}, {"4": 0}))
        self.assertEqual(MongoProductStore(db, "r", recheck_not_found=True).load_checkpoint(3),
                         ({"1", "3"}, {"2": 1, "4": 0}))


class BlockWaitTests(unittest.TestCase):
    def test_waits_double_from_the_first(self):
        from glamira_pipeline.products.cli import block_waits
        self.assertEqual(block_waits(300, 3), [300, 600, 1200])
        self.assertEqual(block_waits(300, 0), [])


if __name__ == "__main__":
    unittest.main()
