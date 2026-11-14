"""Random document samples from a MongoDB collection with ``$sample``.

When the sample is under 5% of the collection and ``$sample`` is the first
stage, WiredTiger returns documents through a pseudo-random cursor instead of
scanning and sorting the whole collection. ``$sample`` has no seed, so two runs
return different documents: record the size and time, not a seed.
"""
from __future__ import annotations

from collections.abc import Iterator

from pymongo.collection import Collection

MAX_SAMPLE = 1_000_000
RANDOM_CURSOR_FRACTION = 0.05


def uses_random_cursor(sample_size: int, collection_count: int) -> bool:
    """True when ``$sample`` can avoid a full collection scan and in-memory sort."""
    return sample_size < collection_count * RANDOM_CURSOR_FRACTION


def sample_documents(collection: Collection, size: int, *, batch_size: int = 1_000) -> Iterator[dict]:
    """Stream ``size`` random documents (duplicates are possible with the random cursor).

    Documents are yielded one at a time from the server cursor, so client
    memory is bounded by ``batch_size`` rather than ``size``.
    """
    if not 1 <= size <= MAX_SAMPLE:
        raise ValueError(f"sample size must be between 1 and {MAX_SAMPLE:,}")
    with collection.aggregate([{"$sample": {"size": size}}], batchSize=batch_size) as cursor:
        yield from cursor
