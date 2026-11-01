"""Orchestrate one bounded streaming pass over the local JSON sample."""
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glamira_pipeline.config import MAX_DOCUMENTS
from glamira_pipeline.quality.duplicates import DuplicateCounts
from glamira_pipeline.quality.ip_addresses import IpCounts
from glamira_pipeline.quality.nulls import NullCounts
from glamira_pipeline.quality.timestamps import TimestampCounts
from glamira_pipeline.quality.transactions import TransactionCounts
from glamira_pipeline.sampling.json_reader import iter_json_documents


@dataclass
class Assessment:
    """Aggregate counters for a bounded sample; no full records or raw IPs are retained."""

    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rows: int = 0
    truncated: bool = False
    nulls: NullCounts = field(default_factory=NullCounts)
    duplicates: DuplicateCounts = field(default_factory=DuplicateCounts)
    ips: IpCounts = field(default_factory=IpCounts)
    transactions: TransactionCounts = field(default_factory=TransactionCounts)
    timestamps: TimestampCounts = field(init=False)

    def __post_init__(self) -> None:
        """Initialize timestamp counters with the assessment's UTC reference time."""
        self.timestamps = TimestampCounts(now=self.now)

    def observe(self, document: dict[str, Any]) -> None:
        """Pass one decoded event document to each check and update row count."""
        self.rows += 1
        self.nulls.observe(document)
        self.duplicates.observe(document)
        self.timestamps.observe(document)
        self.transactions.observe(document)
        self.ips.observe(document)


def assess_sample(path: Path, limit: int = MAX_DOCUMENTS) -> Assessment:
    """Assess a JSON sample and return aggregate counters.

    Args:
        path: Path to a JSON array of BSON-encoded event documents.
        limit: Maximum number of documents to assess, from 1 to 100,000.

    Returns:
        Assessment containing counts and whether the sample exceeded the limit.

    Raises:
        ValueError: If the limit, JSON, or sample contents are invalid or empty.
        OSError: If the sample cannot be read.
    """
    if not 1 <= limit <= MAX_DOCUMENTS:
        raise ValueError(f"limit must be between 1 and {MAX_DOCUMENTS:,}")
    assessment = Assessment()
    with closing(iter_json_documents(path)) as documents:
        while assessment.rows < limit:
            try:
                document = next(documents)
            except StopIteration:
                break
            assessment.observe(document)
        if assessment.rows == limit:
            # Peek one document to distinguish a capped result from a complete file.
            try:
                next(documents)
            except StopIteration:
                pass
            else:
                assessment.truncated = True
    if not assessment.rows:
        raise ValueError("The JSON sample contains no documents")
    return assessment
