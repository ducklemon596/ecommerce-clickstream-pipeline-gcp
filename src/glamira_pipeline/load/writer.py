"""Insert one batch of raw BSON documents, treating already-present ``_id`` values as done."""
from __future__ import annotations

from collections.abc import Sequence

from bson.raw_bson import RawBSONDocument
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

DUPLICATE_KEY = 11000


def insert_batch(collection: Collection, docs: Sequence[bytes]) -> tuple[int, int]:
    """Insert ``docs`` unordered and return ``(inserted, duplicates)``.

    Documents are sent as their original bytes (``RawBSONDocument``), so nothing
    is decoded or re-encoded client-side. The source ``_id`` is the idempotency
    key: on a replay, documents that are already present fail with duplicate-key
    error 11000 and are counted, while the rest of the batch is still inserted.
    Any other write error, or a write-concern error, is re-raised.
    """
    try:
        collection.insert_many([RawBSONDocument(doc) for doc in docs], ordered=False)
    except BulkWriteError as exc:
        details = exc.details
        errors = details.get("writeErrors", [])
        if details.get("writeConcernErrors") or any(e.get("code") != DUPLICATE_KEY for e in errors):
            raise
        return details.get("nInserted", 0), len(errors)
    return len(docs), 0
