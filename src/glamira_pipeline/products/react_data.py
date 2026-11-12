"""Pure extraction of product and option-reference records from ``react_data``.

Values keep their source types: prices stay decimal strings as served, and
``gender`` keeps ``false`` when the site sends ``false``. A field is ``None``
only when it is missing or explicitly null in the payload.
"""
from __future__ import annotations

import json
from typing import Any

PRODUCT_FIELDS = ("name", "sku", "attribute_set_id", "attribute_set", "type_id", "product_type",
                  "product_type_value", "collection", "collection_id", "gender", "store_code",
                  "price", "min_price", "max_price", "min_price_format", "max_price_format")
PRICE_FIELDS = {"full_price": "full_price", "full_price_format": "full_price_format",
                "sale_price": "sale_price", "sale_price_format": "sale_price_format",
                "currency": "currencyCode", "include_tax": "includeTax",
                "default_tax": "defaultTax", "current_tax": "currentTax",
                "use_gold_price": "use_gold_price", "price_product_price": "price"}
OPTION_FIELDS = {"option_id": "option_id", "part_type": "part_type", "option_type": "type",
                 "option_title": "title", "option_default_title": "default_title",
                 "is_require": "is_require", "sort_order": "sort_order"}
VALUE_FIELDS = {"value_id": "option_type_id", "value_sku": "sku", "value_title": "title",
                "value_default_title": "default_title", "value_store_title": "store_title",
                "is_default": "is_default", "value_price": "price", "price_type": "price_type"}


def _json_or_none(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False, sort_keys=True)


def parse_product(payload: dict, *, host: str, requested_currency: str) -> dict:
    """Return one flat product record with provenance; raises on a missing ID."""
    product_id = payload.get("product_id")
    if product_id is None:
        raise ValueError("payload has no product_id")
    record: dict[str, Any] = {"product_id": str(product_id), "host": host,
                              "requested_currency": requested_currency}
    record.update({field: payload.get(field) for field in PRODUCT_FIELDS})
    product_price = payload.get("product_price") or {}
    record.update({target: product_price.get(source) for target, source in PRICE_FIELDS.items()})
    record["prices_json"] = _json_or_none(product_price.get("prices"))
    record["tier_prices_json"] = _json_or_none(product_price.get("tierPrices"))
    # Category fields are empty on observed stores; kept so a change is visible.
    record["category"] = payload.get("category")
    record["category_name"] = payload.get("category_name")
    record["option_count"] = len(payload.get("options") or [])
    return record


def parse_option_values(payload: dict) -> list[dict]:
    """Return one reference row per option value: ``value_id`` → token and labels.

    Options without values (for example free-text engraving) yield one row with
    ``value_id = None`` so every ``option_id`` remains resolvable.
    """
    product_id = str(payload["product_id"])
    rows = []
    for option in payload.get("options") or []:
        base = {"product_id": product_id, **{t: option.get(s) for t, s in OPTION_FIELDS.items()}}
        values = option.get("values") or []
        if not values:
            rows.append({**base, **{target: None for target in VALUE_FIELDS}})
        for value in values:
            rows.append({**base, **{t: value.get(s) for t, s in VALUE_FIELDS.items()}})
    return rows
