"""Assess IP address completeness and syntax without exposing addresses."""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from glamira_pipeline.quality.duplicates import classify_ip, ip_value


@dataclass
class IpCounts:
    """Accumulate completeness and syntax counters for observed IP fields."""
    field_names: Counter[str] = field(default_factory=Counter)
    missing: int = 0
    null: int = 0
    empty: int = 0
    invalid_type: int = 0
    invalid_format: int = 0
    ipv4: int = 0
    ipv6: int = 0

    def observe(self, document: dict[str, Any]) -> None:
        """Update counters from a decoded event document; return no value."""
        name, value = ip_value(document)
        self.field_names[name] += 1
        if name == "missing":
            self.missing += 1
        elif value is None:
            self.null += 1
        elif not isinstance(value, str):
            self.invalid_type += 1
        elif not value.strip():
            self.empty += 1
        else:
            version = classify_ip(value)
            if version == "invalid":
                self.invalid_format += 1
            elif version == "ipv4":
                self.ipv4 += 1
            else:
                self.ipv6 += 1
