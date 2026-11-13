"""Distinct product identifiers referenced anywhere in the event collection.

One server-side aggregation scans the collection once and groups every product
reference by its string form. Only the grouped result (one row per distinct ID)
crosses the network, so client memory is bounded by catalogue size, not by the
41M source events. The collection is read only; no index is created.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from collections.abc import Iterable

from pymongo.collection import Collection

from glamira_pipeline.provenance import mongo_collection_identity

# Event fields that carry a product reference, with the BSON path to read.
REFERENCE_FIELDS = ("product_id", "viewing_product_id", "cart_products.product_id")
NUMERIC_ID = re.compile(r"[0-9]+")


def aggregation_pipeline() -> list[dict]:
    """Return the read-only pipeline that groups product references by ID.

    Each output row is ``{product_id, references, by_field, bson_types}``.
    ``references`` counts occurrences (a cart with two items of one product
    counts twice). Missing, null and empty-string references are excluded;
    values that cannot be converted to a string become ``null`` IDs and are
    reported instead of failing the scan.
    """
    cart_refs = {"$map": {
        "input": {"$cond": [{"$isArray": "$cart_products"}, "$cart_products", []]},
        "as": "item",
        "in": {"field": "cart_products.product_id", "value": "$$item.product_id"},
    }}
    return [
        {"$project": {"_id": 0, "refs": {"$concatArrays": [
            [{"field": "product_id", "value": "$product_id"}],
            [{"field": "viewing_product_id", "value": "$viewing_product_id"}],
            cart_refs,
        ]}}},
        {"$unwind": "$refs"},
        # `null` also matches a missing field, so absent references drop here.
        {"$match": {"refs.value": {"$nin": [None, ""]}}},
        {"$group": {
            "_id": {"id": {"$convert": {"input": "$refs.value", "to": "string",
                                        "onError": None, "onNull": None}},
                    "field": "$refs.field", "type": {"$type": "$refs.value"}},
            "n": {"$sum": 1},
        }},
        {"$group": {
            "_id": "$_id.id",
            "references": {"$sum": "$n"},
            "by_field": {"$push": {"k": "$_id.field", "v": "$n"}},
            "bson_types": {"$addToSet": "$_id.type"},
        }},
        {"$project": {"_id": 0, "product_id": "$_id", "references": 1, "bson_types": 1, "by_field": 1}},
        {"$sort": {"product_id": 1}},
    ]


def merge_field_counts(pairs: Iterable[dict]) -> dict[str, int]:
    """Sum ``[{k, v}]`` pairs per field; one field can repeat across BSON types."""
    counts: dict[str, int] = {}
    for pair in pairs:
        counts[pair["k"]] = counts.get(pair["k"], 0) + int(pair["v"])
    return dict(sorted(counts.items()))


def write_ids(rows: Iterable[dict], path: Path) -> dict:
    """Stream grouped rows to an atomically published JSONL file; return totals."""
    totals = {"distinct_ids": 0, "non_numeric_ids": 0, "unconvertible_groups": 0,
              "references": 0, "ids_by_field": {}, "references_by_field": {}, "bson_types": {}}
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            for row in rows:
                by_field = merge_field_counts(row["by_field"])
                record = {"product_id": row["product_id"], "references": row["references"],
                          "by_field": by_field, "bson_types": sorted(row["bson_types"])}
                totals["references"] += record["references"]
                if record["product_id"] is None:
                    totals["unconvertible_groups"] += 1
                else:
                    totals["distinct_ids"] += 1
                    totals["non_numeric_ids"] += NUMERIC_ID.fullmatch(record["product_id"]) is None
                for field, count in by_field.items():
                    totals["ids_by_field"][field] = totals["ids_by_field"].get(field, 0) + 1
                    totals["references_by_field"][field] = totals["references_by_field"].get(field, 0) + count
                for bson_type in record["bson_types"]:
                    totals["bson_types"][bson_type] = totals["bson_types"].get(bson_type, 0) + 1
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return totals


def run_distinct(collection: Collection, output_dir: Path, *, batch_size: int = 10_000) -> dict:
    """Run the aggregation, write ``product_ids.jsonl`` and ``summary.json``.

    Timing covers the full server scan plus streaming the grouped result.
    Rerunning is safe: outputs are replaced atomically and the source is read only.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    cursor = collection.aggregate(aggregation_pipeline(), allowDiskUse=True, batchSize=batch_size)
    try:
        totals = write_ids(cursor, output_dir / "product_ids.jsonl")
    finally:
        cursor.close()
    seconds = time.perf_counter() - started
    summary = {**totals, "query_seconds": round(seconds, 3), "started_at": started_at.isoformat(),
               "source": mongo_collection_identity(collection),
               "server_version": collection.database.client.server_info().get("version"),
               "reference_fields": list(REFERENCE_FIELDS),
               "notes": "references count occurrences; null/missing/empty references excluded"}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
