"""Check timestamp coverage, range, format, and future values."""
from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any


@dataclass
class TimestampCounts:
    """Interpret numeric timestamps as Unix seconds and BSON dates as UTC."""

    now: datetime
    minimum: datetime | None = None
    maximum: datetime | None = None
    valid: int = 0
    missing: int = 0
    invalid: int = 0
    future: int = 0
    local_minimum: datetime | None = None
    local_maximum: datetime | None = None
    local_valid: int = 0
    local_missing: int = 0
    local_invalid: int = 0

    def observe(self, document: dict[str, Any]) -> None:
        """Update time range and validity counts from one event; return no value.

        Numeric `time_stamp` values are assumed to be Unix seconds. Invalid or
        out-of-range values are counted rather than raised.
        """
        self.observe_local(document.get("local_time"))
        value = document.get("time_stamp")
        if value is None:
            self.missing += 1
            return
        try:
            if isinstance(value, datetime):
                parsed = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                parsed = datetime.fromtimestamp(value, tz=timezone.utc)
            else:
                self.invalid += 1
                return
        except (ValueError, OverflowError, OSError):
            self.invalid += 1
            return
        self.valid += 1
        self.minimum = min(self.minimum, parsed) if self.minimum else parsed
        self.maximum = max(self.maximum, parsed) if self.maximum else parsed
        self.future += parsed > self.now

    def observe_local(self, value: Any) -> None:
        """Count and range-check a local_time value without assuming a timezone.

        Args:
            value: Local wall-clock string in YYYY-MM-DD H:MM:SS format, or null.
        Returns:
            None; invalid types and formats increment the invalid counter.
        """
        if value is None:
            self.local_missing += 1
            return
        try:
            if not isinstance(value, str):
                raise ValueError("local_time must be a string")
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.local_invalid += 1
            return
        self.local_valid += 1
        self.local_minimum = min(self.local_minimum, parsed) if self.local_minimum else parsed
        self.local_maximum = max(self.local_maximum, parsed) if self.local_maximum else parsed
