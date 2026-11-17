"""Unit tests for the Avro export: schema rendering, PII hashing, row conversion and part files."""
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from bson.decimal128 import Decimal128
from bson.objectid import ObjectId
import fastavro

from glamira_pipeline.export.avro_files import AvroPartWriter
from glamira_pipeline.export.cli import SCHEMA_DIR
from glamira_pipeline.export.convert import Converter, SchemaViolation, check_rules
from glamira_pipeline.export.pii import PiiHasher, hasher_from_env
from glamira_pipeline.export.schema import Field, Record, Table, avro_schema, bigquery_schema, schema_json
from glamira_pipeline.export.tables import EVENTS, IP_LOCATIONS, PRODUCT_OPTION_VALUES, PRODUCTS, TABLES

KEY = bytes(range(32))
HASHER = PiiHasher(KEY)
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
OID = ObjectId("5ed8cb2bc671fc36b74653ad")


def event(**overrides):
    """A view_product_detail-like event with every REQUIRED field."""
    doc = {"_id": OID, "collection": "view_product_detail", "time_stamp": 1591266092,
           "api_version": "1.0", "store_id": "6", "current_url": "https://www.glamira.de/x.html",
           "referrer_url": "", "ip": "203.0.113.7", "device_id": "dev-1", "user_id_db": "",
           "user_agent": "Mozilla/5.0", "email_address": "", "local_time": "2020-06-04 12:21:27"}
    doc.update(overrides)
    return doc


def roundtrip(table, rows):
    """Write rows with fastavro's validator and read them back."""
    buffer = io.BytesIO()
    fastavro.writer(buffer, fastavro.parse_schema(avro_schema(table)), rows, validator=True)
    buffer.seek(0)
    return list(fastavro.reader(buffer))


class SchemaTests(unittest.TestCase):
    def test_every_table_parses_and_uses_known_rules(self):
        for table in TABLES.values():
            fastavro.parse_schema(avro_schema(table))
            check_rules(table)

    def test_names_are_valid_for_avro_and_bigquery(self):
        def walk(fields):
            for field in fields:
                self.assertRegex(field.name, NAME)
                if isinstance(field.type, Record):
                    walk(field.type.fields)
        for table in TABLES.values():
            walk(table.fields)

    def test_modes_render_as_bigquery_expects(self):
        avro = {f["name"]: f for f in avro_schema(EVENTS)["fields"]}
        bq = {f["name"]: f for f in bigquery_schema(EVENTS)}
        self.assertEqual(avro["_id"]["type"], "string")
        self.assertEqual(avro["email_hash"]["type"], ["null", "string"])
        self.assertEqual(avro["option"]["type"]["type"], "array")
        self.assertEqual(avro["time_stamp"]["type"]["logicalType"], "timestamp-micros")
        self.assertEqual((bq["_id"]["mode"], bq["option"]["mode"], bq["option"]["type"]),
                         ("REQUIRED", "REPEATED", "RECORD"))
        price = next(f for f in avro_schema(PRODUCTS)["fields"] if f["name"] == "price")["type"][1]
        self.assertEqual((price["logicalType"], price["precision"], price["scale"]), ("decimal", 38, 9))

    def test_committed_schema_files_match_the_contract(self):
        for table in TABLES.values():
            self.assertEqual((SCHEMA_DIR / f"{table.name}.avsc").read_text(encoding="utf-8"),
                             schema_json(avro_schema(table)), f"run: uv run write-raw-schemas ({table.name})")
            self.assertEqual((SCHEMA_DIR / f"{table.name}.bq.json").read_text(encoding="utf-8"),
                             schema_json(bigquery_schema(table)), f"run: uv run write-raw-schemas ({table.name})")


    def test_contract_document_lists_every_column(self):
        text = (SCHEMA_DIR.parents[1] / "docs" / "raw_layer_contract.md").read_text(encoding="utf-8")

        def walk(fields, prefix):
            for field in fields:
                path = f"{prefix}{field.name}"
                self.assertIn(f"| `{path}` |", text, f"{path} missing from docs/raw_layer_contract.md")
                if isinstance(field.type, Record):
                    walk(field.type.fields, f"{path}{'[]' if field.mode == 'REPEATED' else ''}.")
        for table in TABLES.values():
            walk(table.fields, "")


    def test_bigquery_layout_is_declared_and_validated(self):
        self.assertEqual((EVENTS.partition_by, EVENTS.cluster_by), ("time_stamp", ("collection",)))
        fields = (Field("t", "TIMESTAMP", "NULLABLE"), Field("s", "STRING"))
        with self.assertRaisesRegex(ValueError, "REQUIRED TIMESTAMP"):
            Table("x", "X", "x", "", fields, partition_by="t")
        with self.assertRaisesRegex(ValueError, "top-level scalar"):
            Table("x", "X", "x", "", fields, cluster_by=("missing",))


class PiiTests(unittest.TestCase):
    def test_hash_is_keyed_and_deterministic(self):
        self.assertEqual(HASHER.text("dev-1"), HASHER.text("dev-1"))
        self.assertNotEqual(HASHER.text("dev-1"), PiiHasher(bytes(32)).text("dev-1"))
        self.assertRegex(HASHER.text("dev-1"), r"^[0-9a-f]{64}$")

    def test_email_is_trimmed_and_lower_cased(self):
        self.assertEqual(HASHER.email(" A@Example.com "), HASHER.email("a@example.com"))

    def test_empty_and_null_are_kept(self):
        self.assertEqual((HASHER.text(""), HASHER.email(None), HASHER.ip("")), ("", None, ("", True)))

    def test_ip_is_hashed_in_canonical_form(self):
        self.assertEqual(HASHER.ip("2001:DB8:0::1"), HASHER.ip("2001:db8::1"))
        digest, valid = HASHER.ip("not-an-ip")
        self.assertFalse(valid)
        self.assertEqual(digest, HASHER.digest("not-an-ip"))

    def test_key_validation(self):
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            PiiHasher(b"short")
        with self.assertRaisesRegex(ValueError, "set GLAMIRA_PII_HASH_KEY"):
            hasher_from_env({})
        with self.assertRaisesRegex(ValueError, "hexadecimal"):
            hasher_from_env({"GLAMIRA_PII_HASH_KEY": "zz"})
        self.assertEqual(hasher_from_env({"GLAMIRA_PII_HASH_KEY": KEY.hex()}).fingerprint(), HASHER.fingerprint())


class EventConversionTests(unittest.TestCase):
    def setUp(self):
        self.converter = Converter(EVENTS, HASHER)

    def test_required_fields_and_pii(self):
        row = self.converter.convert(event(email_address=" A@x.com ", user_id_db="4711"))
        self.assertEqual(row["_id"], "5ed8cb2bc671fc36b74653ad")
        self.assertEqual(row["time_stamp"], 1591266092 * 1_000_000)
        self.assertEqual(row["ip_hash"], HASHER.ip("203.0.113.7")[0])
        self.assertEqual(row["email_hash"], HASHER.email("a@x.com"))
        self.assertEqual(row["device_id_hash"], HASHER.text("dev-1"))
        self.assertEqual(row["user_id_hash"], HASHER.text("4711"))
        self.assertEqual(self.converter.convert(event())["user_id_hash"], "")
        self.assertNotIn("203.0.113.7", json.dumps(row))
        self.assertEqual((row["option"], row["option_filter"], row["cart_products"]), ([], None, []))
        self.assertEqual(roundtrip(EVENTS, [row])[0]["_id"], row["_id"])

    def test_option_array_and_object_go_to_separate_columns(self):
        items = [{"option_label": "alloy", "option_id": "332084", "value_label": "", "value_id": "3279318"}]
        row = self.converter.convert(event(option=items))
        self.assertEqual(row["option"][0]["value_id"], "3279318")
        self.assertIsNone(row["option"][0]["quality"])
        self.assertIsNone(row["option_filter"])
        row = self.converter.convert(event(collection="view_all_recommend",
                                           option={"alloy": "", "Kollektion": "x", "category id": "7"}))
        self.assertEqual(row["option"], [])
        self.assertEqual((row["option_filter"]["kollektion"], row["option_filter"]["category_id"]), ("x", "7"))
        self.assertIsNone(row["option_filter"]["diamond"])
        self.assertEqual(len(roundtrip(EVENTS, [row])), 1)

    def test_cart_products_ids_become_strings_and_empty_option_string_becomes_empty_array(self):
        cart = [{"product_id": 97507, "amount": 1, "price": "55,00", "currency": "€", "option": ""},
                {"product_id": 97471, "option": [{"option_label": "diamond", "option_id": 250775,
                                                  "value_label": "White Sapphire", "value_id": 2085213}]}]
        row = self.converter.convert(event(collection="checkout_success", cart_products=cart, order_id=3571009023.0))
        self.assertEqual(row["order_id"], "3571009023")
        self.assertEqual(row["cart_products"][0]["option"], [])
        self.assertEqual(row["cart_products"][1]["product_id"], "97471")
        self.assertEqual(row["cart_products"][1]["option"][0]["value_id"], "2085213")
        self.assertIsNone(row["cart_products"][1]["amount"])
        self.assertEqual(self.converter.stats["cart_products[].option: '' -> []"], 1)
        self.assertEqual(len(roundtrip(EVENTS, [row])), 1)

    def test_mixed_scalars_follow_their_rules(self):
        row = self.converter.convert(event(utm_source=False, utm_medium="retargeting",
                                           recommendation_product_position=3, order_id=""))
        self.assertEqual((row["utm_source"], row["utm_medium"]), ("false", "retargeting"))
        self.assertEqual((row["recommendation_product_position"], row["order_id"]), ("3", ""))

    def test_unplanned_input_is_rejected(self):
        cases = {
            "unknown keys \\['new_field'\\]": event(new_field=1),
            "option: unknown keys": event(option={"color": "red"}),
            "non-integral": event(order_id=1.5),
            "bool where": event(order_id=True),
            "time_stamp: expected int": event(time_stamp="1591266092"),
            "REQUIRED value": event(store_id=None),
            "expected an array": event(cart_products="x"),
            "utm_source: expected a string or bool": event(utm_source=1),
        }
        for message, doc in cases.items():
            with self.subTest(message), self.assertRaisesRegex(SchemaViolation, message):
                self.converter.convert(doc)
        incomplete = event()
        del incomplete["user_agent"]
        with self.assertRaisesRegex(SchemaViolation, "user_agent: REQUIRED"):
            self.converter.convert(incomplete)


class EnrichmentConversionTests(unittest.TestCase):
    CRAWLED = datetime(2026, 11, 12, 17, 49, 1, 691000)  # naive UTC, as PyMongo returns it

    def product(self, **overrides):
        doc = {"_id": "100000", "product_id": "100000", "status": "success", "status_code": 200,
               "attempts": 1, "error": None, "attribute_set_id": 55, "category": 0, "gender": False,
               "price": Decimal128("1417.000000"), "sale_price": Decimal128("2588.25"), "default_tax": 0,
               "include_tax": False, "source": {"host": "www.glamira.com", "store_code": "glus",
                                                "url": "https://www.glamira.com/x", "requested_currency": "USD"},
               "run_id": "r1", "crawled_at": self.CRAWLED}
        doc.update(overrides)
        return doc

    def test_products(self):
        converter = Converter(PRODUCTS, HASHER)
        row = converter.convert(self.product())
        self.assertNotIn("_id", row)
        self.assertEqual((row["attribute_set_id"], row["category"], row["gender"]), ("55", "0", "false"))
        self.assertEqual((row["price"], row["default_tax"]), (Decimal("1417.000000"), Decimal("0")))
        self.assertEqual(row["crawled_at"],
                         int(self.CRAWLED.replace(tzinfo=timezone.utc).timestamp()) * 1_000_000 + 691000)
        back = roundtrip(PRODUCTS, [row])[0]
        self.assertEqual(back["sale_price"], Decimal("2588.25"))
        self.assertEqual(back["crawled_at"], self.CRAWLED.replace(tzinfo=timezone.utc))

    def test_products_reject_redundant_id_mismatch_and_excess_scale(self):
        converter = Converter(PRODUCTS, HASHER)
        with self.assertRaisesRegex(SchemaViolation, "_id does not equal product_id"):
            converter.convert(self.product(_id="1"))
        with self.assertRaisesRegex(SchemaViolation, "more than 9 decimal places"):
            converter.convert(self.product(price=Decimal128("1.0000000001")))
        with self.assertRaisesRegex(SchemaViolation, "source.store_code: REQUIRED"):
            converter.convert(self.product(source={"host": "h", "url": "u", "requested_currency": "USD"}))

    def test_option_values(self):
        converter = Converter(PRODUCT_OPTION_VALUES, HASHER)
        doc = {"_id": {"product_id": "1", "option_id": "2", "value_id": None}, "product_id": "1",
               "option_id": "2", "value_id": None, "is_require": 1, "is_default": 0, "sort_order": "10",
               "value_price": None, "run_id": "r1", "crawled_at": self.CRAWLED}
        row = converter.convert(doc)
        self.assertEqual((row["is_require"], row["is_default"], row["value_id"]), (True, False, None))
        self.assertEqual(len(roundtrip(PRODUCT_OPTION_VALUES, [row])), 1)
        with self.assertRaisesRegex(SchemaViolation, "expected a bool or 0/1"):
            converter.convert({**doc, "is_default": 2})

    def test_ip_location_hash_joins_event_hash(self):
        row = Converter(IP_LOCATIONS, HASHER).convert(
            {"_id": "2001:db8::1", "ip_version": 6, "status": "unsupported_ipv6", "country_code": None,
             "country_name": None, "region": None, "city": None, "database_id": "abc"})
        event_row = Converter(EVENTS, HASHER).convert(event(ip="2001:DB8:0::1"))
        self.assertEqual(row["ip_hash"], event_row["ip_hash"])
        self.assertEqual(len(roundtrip(IP_LOCATIONS, [row])), 1)


class PartWriterTests(unittest.TestCase):
    SCHEMA = {"type": "record", "name": "T", "fields": [{"name": "a", "type": "long"}]}

    def test_parts_rotate_and_are_complete(self):
        with TemporaryDirectory() as tmp:
            writer = AvroPartWriter(Path(tmp), self.SCHEMA, rows_per_file=3)
            for i in range(7):
                writer.write({"a": i})
            parts = writer.close()
            self.assertEqual([p.rows for p in parts], [3, 3, 1])
            values = []
            for part in parts:
                with (Path(tmp) / part.name).open("rb") as stream:
                    values += [r["a"] for r in fastavro.reader(stream)]
            self.assertEqual(values, list(range(7)))
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()),
                             ["part-00000.avro", "part-00001.avro", "part-00002.avro"])

    def test_abort_removes_the_open_part_only(self):
        with TemporaryDirectory() as tmp:
            writer = AvroPartWriter(Path(tmp), self.SCHEMA, rows_per_file=2)
            for i in range(3):
                writer.write({"a": i})
            writer.abort()
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["part-00000.avro"])


if __name__ == "__main__":
    unittest.main()
