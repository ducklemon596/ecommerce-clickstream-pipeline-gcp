"""Pure conversion of ``react_data`` payloads into MongoDB documents.

Values keep their source meaning: ``gender`` stays ``false`` when the site
sends ``false``, and a field is ``None`` only when it is missing or null in the
payload (or when the crawl did not succeed). Prices become ``Decimal128`` so
they load into BigQuery ``NUMERIC`` without float rounding.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from bson.decimal128 import Decimal128

STATUSES = ("success", "not_found", "error", "blocked")
# Top-level payload fields copied as served.
TEXT_FIELDS = ("name", "sku", "attribute_set_id", "attribute_set", "type_id", "product_type",
               "product_type_value", "collection", "collection_id", "category", "category_name",
               "gender", "min_price_format", "max_price_format")
PRICE_FIELDS = ("price", "min_price", "max_price")
# Target field -> key inside ``product_price``.
PRODUCT_PRICE_FIELDS = {"full_price_format": "full_price_format", "sale_price_format": "sale_price_format",
                        "currency": "currencyCode", "include_tax": "includeTax",
                        "default_tax": "defaultTax", "current_tax": "currentTax",
                        "use_gold_price": "use_gold_price"}
PRODUCT_PRICE_DECIMALS = {"full_price": "full_price", "sale_price": "sale_price"}
DATA_FIELDS = (*TEXT_FIELDS, *PRICE_FIELDS, *PRODUCT_PRICE_DECIMALS, *PRODUCT_PRICE_FIELDS, "option_count")

OPTION_FIELDS = {"part_type": "part_type", "option_type": "type", "option_title": "title",
                 "option_default_title": "default_title", "is_require": "is_require",
                 "sort_order": "sort_order"}
VALUE_FIELDS = {"value_sku": "sku", "value_title": "title", "value_default_title": "default_title",
                "value_store_title": "store_title", "is_default": "is_default", "price_type": "price_type"}


def to_decimal128(value: Any) -> Decimal128 | None:
    """Convert a served price (string, int or float) exactly; raise ValueError if not numeric."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"price is boolean: {value!r}")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"price is not numeric: {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"price is not finite: {value!r}")
    return Decimal128(number)


def _id_text(value: Any) -> str | None:
    """Normalize option/value IDs to strings so ``_id`` keys compare equal across runs."""
    return None if value is None or value == "" else str(value)


def product_document(*, product_id: str, status: str, status_code: int | None, payload: dict | None,
                     source: dict, run_id: str, crawled_at: datetime, error: str | None = None) -> dict:
    """Return the full ``products`` document (without ``attempts``) for one outcome.

    Every outcome carries the same key set; data fields are ``None`` unless
    ``status == "success"``. Raises ValueError for an unknown status, a payload
    for another product, or a non-numeric price.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    document: dict[str, Any] = {"_id": product_id, "product_id": product_id, "status": status,
                                "status_code": status_code, "error": error}
    document.update(dict.fromkeys(DATA_FIELDS))
    if status == "success":
        if payload is None or str(payload.get("product_id")) != product_id:
            raise ValueError(f"payload does not describe product {product_id}")
        product_price = payload.get("product_price") or {}
        document.update({field: payload.get(field) for field in TEXT_FIELDS})
        document.update({field: to_decimal128(payload.get(field)) for field in PRICE_FIELDS})
        document.update({t: to_decimal128(product_price.get(s)) for t, s in PRODUCT_PRICE_DECIMALS.items()})
        document.update({t: product_price.get(s) for t, s in PRODUCT_PRICE_FIELDS.items()})
        document["option_count"] = len(payload.get("options") or [])
    document.update(source=source, run_id=run_id, crawled_at=crawled_at)
    return document


def option_value_documents(payload: dict, *, run_id: str, crawled_at: datetime) -> list[dict]:
    """Return one reference document per option value: ``value_id`` → token and labels.

    Options without values (for example free-text engraving) yield one document
    with ``value_id = None`` so every ``option_id`` stays resolvable. IDs are
    strings to match product-page events; cart events use ints and need a cast.
    """
    product_id = str(payload["product_id"])
    documents = []
    for option in payload.get("options") or []:
        option_id = _id_text(option.get("option_id"))
        if option_id is None:
            raise ValueError(f"product {product_id} has an option without option_id")
        base = {"product_id": product_id, "option_id": option_id,
                **{t: option.get(s) for t, s in OPTION_FIELDS.items()}}
        values = option.get("values") or [None]
        for value in values:
            value = value or {}
            value_id = _id_text(value.get("option_type_id"))
            documents.append({
                "_id": {"product_id": product_id, "option_id": option_id, "value_id": value_id},
                **base, "value_id": value_id,
                **{t: value.get(s) for t, s in VALUE_FIELDS.items()},
                "value_price": to_decimal128(value.get("price")),
                "run_id": run_id, "crawled_at": crawled_at})
    return documents
