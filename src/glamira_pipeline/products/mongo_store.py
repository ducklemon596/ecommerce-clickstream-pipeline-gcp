"""MongoDB collections, schema validation and batch writes for the product crawl.

The data is the checkpoint: a product is finished when its document has a
final status, so resuming is a set difference over ``products._id``. Every
write is an upsert on a deterministic ``_id``, making replays idempotent.
Only the new collections below are created; source collections are never
modified and nothing is dropped.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import uuid

from pymongo import ReplaceOne, UpdateOne
from pymongo.database import Database

from glamira_pipeline.products.react_data import DATA_FIELDS, STATUSES

LOGGER = logging.getLogger(__name__)
PRODUCTS = "products"
OPTION_VALUES = "product_option_values"
RUNS = "enrichment_runs"  # shared with IP enrichment provenance documents
RUN_TYPE = "product_crawl"
FINAL_STATUSES = ("success", "not_found")
LOCK_TIMEOUT = timedelta(seconds=120)

STRING = ["string", "null"]
DECIMAL = ["decimal", "null"]
NUMBER = ["int", "long", "double", "decimal", "null"]
PRODUCT_TYPES = {
    **dict.fromkeys(DATA_FIELDS, STRING),
    "attribute_set_id": ["int", "long", "string", "null"],
    "category": ["int", "long", "string", "null"],
    "gender": ["string", "bool", "null"],
    "price": DECIMAL, "min_price": DECIMAL, "max_price": DECIMAL,
    "full_price": DECIMAL, "sale_price": DECIMAL,
    "include_tax": ["bool", "null"], "use_gold_price": ["bool", "null"],
    "default_tax": NUMBER, "current_tax": NUMBER, "option_count": ["int", "null"],
}
PRODUCT_SCHEMA = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "product_id", "status", "status_code", "attempts", "error",
                 *DATA_FIELDS, "source", "run_id", "crawled_at"],
    "properties": {
        "_id": {"bsonType": "string"}, "product_id": {"bsonType": "string"},
        "status": {"enum": list(STATUSES)}, "status_code": {"bsonType": ["int", "null"]},
        "attempts": {"bsonType": ["int", "long"], "minimum": 0}, "error": {"bsonType": STRING},
        **{name: {"bsonType": types} for name, types in PRODUCT_TYPES.items()},
        "source": {"bsonType": "object", "required": ["host", "store_code", "url", "requested_currency"]},
        "run_id": {"bsonType": "string"}, "crawled_at": {"bsonType": "date"},
    },
}}
OPTION_SCHEMA = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "product_id", "option_id", "value_id", "run_id", "crawled_at"],
    "properties": {
        "_id": {"bsonType": "object", "required": ["product_id", "option_id", "value_id"]},
        "product_id": {"bsonType": "string"}, "option_id": {"bsonType": "string"},
        "value_id": {"bsonType": STRING}, "part_type": {"bsonType": STRING},
        "option_type": {"bsonType": STRING}, "option_title": {"bsonType": STRING},
        "option_default_title": {"bsonType": STRING}, "is_require": {"bsonType": ["int", "bool", "null"]},
        "sort_order": {"bsonType": ["string", "int", "null"]}, "value_sku": {"bsonType": STRING},
        "value_title": {"bsonType": STRING}, "value_default_title": {"bsonType": STRING},
        "value_store_title": {"bsonType": STRING}, "is_default": {"bsonType": ["bool", "int", "null"]},
        "value_price": {"bsonType": DECIMAL}, "price_type": {"bsonType": STRING},
        "run_id": {"bsonType": "string"}, "crawled_at": {"bsonType": "date"},
    },
}}
VALIDATORS = {PRODUCTS: PRODUCT_SCHEMA, OPTION_VALUES: OPTION_SCHEMA}
INDEXES = {PRODUCTS: [("status", 1)], OPTION_VALUES: [("product_id", 1)]}


def ensure_collections(db: Database) -> list[str]:
    """Create or update the product collections, validators and indexes; return actions.

    Idempotent: reruns reapply the same validator and keep existing indexes.
    """
    actions = []
    existing = set(db.list_collection_names())
    for name, validator in VALIDATORS.items():
        options = {"validator": validator, "validationLevel": "strict", "validationAction": "error"}
        if name in existing:
            db.command("collMod", name, **options)
            actions.append(f"updated validator {name}")
        else:
            db.create_collection(name, **options)
            actions.append(f"created {name}")
        index = db[name].create_index(INDEXES[name])
        actions.append(f"index {name}.{index}")
    return actions


def has_validators(db: Database) -> bool:
    """Return whether both product collections carry the current validator."""
    found = {info["name"]: info.get("options", {}).get("validator")
             for info in db.list_collections(filter={"name": {"$in": list(VALIDATORS)}})}
    return all(found.get(name) == validator for name, validator in VALIDATORS.items())


@dataclass
class BatchItem:
    """One product outcome ready to write; ``product`` already holds its ``attempts``."""

    product: dict
    option_values: list[dict] = field(default_factory=list)


class MongoProductStore:
    """Checkpoint and sink backed by ``products`` and ``product_option_values``."""

    def __init__(self, db: Database, run_id: str, *, recheck_not_found: bool = False) -> None:
        """``recheck_not_found`` treats ``not_found`` as unfinished, so those IDs are crawled again."""
        self.db, self.run_id = db, run_id
        self.final_statuses = ("success",) if recheck_not_found else FINAL_STATUSES

    def load_checkpoint(self, max_attempts: int) -> tuple[set[str], dict[str, int]]:
        """Return finished IDs and the ``attempts`` of every other existing document.

        Finished means a final status (see ``final_statuses``), or an error
        after ``max_attempts`` attempts.
        """
        finished, attempts = set(), {}
        for document in self.db[PRODUCTS].find({}, {"status": 1, "attempts": 1}):
            count = document.get("attempts", 0)
            if document["status"] in self.final_statuses or (document["status"] == "error" and count >= max_attempts):
                finished.add(document["_id"])
            else:
                attempts[document["_id"]] = count
        return finished, attempts

    def write_batch(self, items: Sequence[BatchItem]) -> None:
        """Upsert products and option values, then drop options no longer served.

        Order matters for recovery: a product is only considered finished after
        its document is written, and option rows are written before stale ones
        are removed, so a crash at any point is repaired by recrawling.
        """
        if not items:
            return
        # ``attempts`` is computed by the crawler and set (not $inc), so replaying a
        # batch after a partial failure leaves identical documents.
        product_ops = [UpdateOne({"_id": item.product["_id"]}, {"$set": item.product}, upsert=True)
                       for item in items]
        self.db[PRODUCTS].bulk_write(product_ops, ordered=False)
        option_ops = [ReplaceOne({"_id": row["_id"]}, row, upsert=True)
                      for item in items for row in item.option_values]
        if option_ops:
            self.db[OPTION_VALUES].bulk_write(option_ops, ordered=False)
        succeeded = [item.product["_id"] for item in items if item.product["status"] == "success"]
        if succeeded:
            self.db[OPTION_VALUES].delete_many({"product_id": {"$in": succeeded}, "run_id": {"$ne": self.run_id}})

    def heartbeat(self, progress: dict, metrics: dict | None = None) -> None:
        """Refresh the run's lock heartbeat and record progress after each batch."""
        update = {"heartbeat_at": _now(), "progress": progress}
        if metrics is not None:
            update["metrics"] = metrics
        self.db[RUNS].update_one({"_id": self.run_id, "type": RUN_TYPE}, {"$set": update})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def start_run(db: Database, *, params: dict, input_info: dict, git_sha: str | None) -> str:
    """Register a running crawl; refuse while another run has a fresh heartbeat.

    A ``running`` run whose heartbeat is older than ``LOCK_TIMEOUT`` is marked
    ``abandoned``. Returns the new ``run_id``.
    """
    now = _now()
    for run in db[RUNS].find({"type": RUN_TYPE, "status": "running"}):
        heartbeat = run.get("heartbeat_at") or run.get("started_at")
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=timezone.utc)
        if now - heartbeat < LOCK_TIMEOUT:
            raise RuntimeError(f"crawl run {run['_id']} is still running (heartbeat {heartbeat.isoformat()})")
        db[RUNS].update_one({"_id": run["_id"]}, {"$set": {"status": "abandoned", "finished_at": now}})
        LOGGER.warning("marked stale run %s as abandoned", run["_id"])
    run_id = uuid.uuid4().hex
    db[RUNS].insert_one({"_id": run_id, "type": RUN_TYPE, "status": "running", "started_at": now,
                         "heartbeat_at": now, "finished_at": None, "params": params,
                         "input": input_info, "git_sha": git_sha, "progress": None,
                         "metrics": None, "stop_reason": None})
    return run_id


def finish_run(db: Database, run_id: str, *, status: str, metrics: dict | None,
               progress: dict | None, stop_reason: str | None) -> None:
    """Record a run's final status (``completed``, ``stopped`` or ``failed``) and release the lock."""
    db[RUNS].update_one({"_id": run_id, "type": RUN_TYPE}, {"$set": {
        "status": status, "finished_at": _now(), "heartbeat_at": _now(), "metrics": metrics,
        "progress": progress, "stop_reason": stop_reason}})
