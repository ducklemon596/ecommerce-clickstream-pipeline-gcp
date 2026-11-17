"""Split a table export into deterministic chunks, the unit of commit and retry.

``events`` is split by UTC day of the ``_id`` ObjectId time: the tracker
generated the ObjectIds, so their time matches ``time_stamp`` to within a
second, and ``_id`` ranges use the default ``_id_`` index (no new index). The
enrichment tables are small and exported as one chunk, ``all``. A ``--limit``
sample is always one chunk: the first N documents by ``_id``.

Every chunk is read sorted by ``_id``, so a chunk's rows, and therefore its
Avro bytes, do not depend on the physical order of the collection.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from bson.objectid import ObjectId
from pymongo.collection import Collection

from glamira_pipeline.export.schema import Table

DAILY_TABLES = frozenset({"events"})
ALL = "all"
_MIN_OID, _MAX_OID = ObjectId("0" * 24), ObjectId("f" * 24)


class CoverageError(ValueError):
    """The chunk plan does not cover the collection exactly."""


@dataclass(frozen=True)
class Chunk:
    """A half-open ``_id`` range ``[lower, upper)``; no bounds means the whole collection."""

    id: str
    lower: ObjectId | None = None
    upper: ObjectId | None = None
    limit: int | None = None

    @property
    def query(self) -> dict[str, Any]:
        if self.lower is None:
            return {}
        return {"_id": {"$gte": self.lower, "$lt": self.upper}}

    @property
    def directory(self) -> str:
        return f"chunk={self.id}"

    def describe(self) -> dict:
        """JSON form recorded in the export identity."""
        if self.lower is None:
            return {"id": self.id, "range": "all", "limit": self.limit}
        return {"id": self.id, "range": [str(self.lower), str(self.upper)]}


def daily_chunks(first: datetime, last: datetime) -> list[Chunk]:
    """One chunk per UTC day from the day of ``first`` to the day of ``last``, contiguous and half-open."""
    day = datetime(first.year, first.month, first.day, tzinfo=timezone.utc)
    chunks = []
    while day <= last:
        following = day + timedelta(days=1)
        chunks.append(Chunk(day.strftime("%Y-%m-%d"), ObjectId.from_datetime(day),
                            ObjectId.from_datetime(following)))
        day = following
    return chunks


def check_coverage(counts: dict[str, int], total: int) -> None:
    """Raise CoverageError unless the chunk counts add up to the collection's document count.

    ObjectId ranges match only ObjectIds, so a document with another ``_id``
    type, or outside the planned days, makes the sum fall short.
    """
    covered = sum(counts.values())
    if covered != total:
        raise CoverageError(f"chunks cover {covered:,} documents but the collection holds {total:,}; "
                            "some _id values are not ObjectIds or lie outside the planned days")


def plan_chunks(table: Table, collection: Collection, limit: int | None = None) -> tuple[list[Chunk], dict[str, int]]:
    """Return the chunks of ``table`` and the expected document count of each.

    Counting uses ``COUNT_SCAN`` on ``_id_`` for daily chunks (about 21 s for
    the 65 days of the full ``summary``) and collection metadata otherwise.
    """
    total = collection.estimated_document_count()
    if limit is not None:
        return [Chunk(ALL, limit=limit)], {ALL: min(limit, total)}
    if table.name not in DAILY_TABLES:
        return [Chunk(ALL)], {ALL: total}
    bounds = {"_id": {"$gte": _MIN_OID, "$lte": _MAX_OID}}
    first = collection.find_one(bounds, {"_id": 1}, sort=[("_id", 1)])
    last = collection.find_one(bounds, {"_id": 1}, sort=[("_id", -1)])
    chunks = [] if first is None else daily_chunks(first["_id"].generation_time, last["_id"].generation_time)
    counts = {chunk.id: collection.count_documents(chunk.query) for chunk in chunks}
    check_coverage(counts, total)
    return chunks, counts
