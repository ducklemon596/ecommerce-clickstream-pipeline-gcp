"""Top-level missing-key and explicit BSON-null counts."""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NullCounts:
    """Count present and explicit-null keys; derive missing counts at report time."""

    present: Counter[str] = field(default_factory=Counter)
    explicit_null: Counter[str] = field(default_factory=Counter)

    def observe(self, document: dict[str, Any]) -> None:
        """Count present and explicit-null top-level keys in one event document."""
        for key, value in document.items():
            self.present[key] += 1
            if value is None:
                self.explicit_null[key] += 1
