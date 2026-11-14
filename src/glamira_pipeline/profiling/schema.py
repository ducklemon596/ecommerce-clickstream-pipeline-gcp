"""Field presence, null and BSON-type statistics per event type, including nested paths.

Paths use dots for object keys and ``[]`` for array elements, e.g.
``cart_products[].option[].value_id``. Every path is counted against its
*container*: a top-level field against the events of its type, a field inside
``cart_products[]`` against the cart items that are objects. That keeps
"missing" meaningful at every depth.

The module is pure: it receives documents and returns counts, so it can be
fed by a MongoDB cursor or a file and tested with small synthetic fixtures.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from bson import Binary, Decimal128, Int64, ObjectId, Regex, Timestamp

EVENT_TYPE_FIELD = "collection"
# Same label as reconcile-summary, which maps missing and null with $ifNull.
MISSING_EVENT_TYPE = "<missing>"
ROOT = ""
ARRAY = "[]"

# Bounds that keep memory flat whatever a single document contains.
MAX_DEPTH = 6
MAX_ARRAY_ITEMS = 100
MAX_PATHS_PER_TYPE = 1_000


def bson_type(value: Any) -> str:
    """Return the BSON type name of a decoded value (``bool`` is checked before ``int``)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, Int64):
        return "long"
    if isinstance(value, int):
        return "int" if -2**31 <= value < 2**31 else "long"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    for kind, name in ((ObjectId, "objectId"), (Decimal128, "decimal"), (datetime, "date"),
                       (Binary, "binData"), (bytes, "binData"), (Timestamp, "timestamp"),
                       (Regex, "regex")):
        if isinstance(value, kind):
            return name
    return type(value).__name__


def is_empty(value: Any) -> bool:
    """True for an empty or whitespace-only string, an empty array or an empty object."""
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, Mapping)):
        return len(value) == 0
    return False


@dataclass
class PathStats:
    """Counts for one path within one event type."""

    present: int = 0
    null: int = 0
    empty: int = 0
    types: Counter[str] = field(default_factory=Counter)


@dataclass
class TypeProfile:
    """Statistics for every path observed in one event type."""

    events: int = 0
    containers: Counter[str] = field(default_factory=Counter)  # objects observed at each path
    elements: Counter[str] = field(default_factory=Counter)  # array elements observed at each path
    paths: dict[str, PathStats] = field(default_factory=dict)
    dropped_paths: int = 0
    truncated_arrays: int = 0
    depth_limited: int = 0


def parent_path(path: str) -> str:
    """Return the container of a path: ``a[].b`` → ``a[]``, ``a.b`` → ``a``, ``a`` → root."""
    cut = path.rfind(".")
    return ROOT if cut < 0 else path[:cut]


def _join(prefix: str, key: str) -> str:
    return key if prefix == ROOT else f"{prefix}.{key}"


@dataclass
class SchemaProfile:
    """Accumulate per-event-type path statistics from a stream of documents."""

    max_depth: int = MAX_DEPTH
    max_array_items: int = MAX_ARRAY_ITEMS
    max_paths_per_type: int = MAX_PATHS_PER_TYPE
    types: dict[str, TypeProfile] = field(default_factory=dict)

    @property
    def documents(self) -> int:
        return sum(profile.events for profile in self.types.values())

    def observe(self, document: Mapping[str, Any]) -> None:
        """Add one event document to the profile of its event type."""
        event_type = document.get(EVENT_TYPE_FIELD)
        label = event_type if isinstance(event_type, str) else MISSING_EVENT_TYPE
        profile = self.types.setdefault(label, TypeProfile())
        profile.events += 1
        self._observe_object(profile, document, ROOT, 0)

    def _observe_object(self, profile: TypeProfile, obj: Mapping[str, Any], prefix: str, depth: int) -> None:
        profile.containers[prefix] += 1
        for key, value in obj.items():
            self._observe_value(profile, _join(prefix, str(key)), value, depth + 1)

    def _observe_value(self, profile: TypeProfile, path: str, value: Any, depth: int) -> None:
        stats = profile.paths.get(path)
        if stats is None:
            if len(profile.paths) >= self.max_paths_per_type:
                profile.dropped_paths += 1
                return
            stats = profile.paths[path] = PathStats()
        stats.present += 1
        stats.types[bson_type(value)] += 1
        if value is None:
            stats.null += 1
        elif is_empty(value):
            stats.empty += 1

        if isinstance(value, Mapping):  # empty objects still count as containers
            if depth >= self.max_depth:
                profile.depth_limited += 1
            else:
                self._observe_object(profile, value, path, depth)
        elif isinstance(value, (list, tuple)) and value:
            if depth >= self.max_depth:
                profile.depth_limited += 1
                return
            if len(value) > self.max_array_items:
                profile.truncated_arrays += 1
            element_path = f"{path}{ARRAY}"
            for element in value[: self.max_array_items]:
                profile.elements[path] += 1
                self._observe_value(profile, element_path, element, depth)


def container_count(profile: TypeProfile, path: str) -> int:
    """Number of places the path could have appeared.

    For ``a[]`` that is the number of array elements observed under ``a``;
    for ``a[].b`` it is the number of object elements in ``a[]``; for a
    top-level field it is the number of events of the type.
    """
    if path.endswith(ARRAY):
        return profile.elements[path[: -len(ARRAY)]]
    return profile.containers[parent_path(path)]


def missing_count(profile: TypeProfile, path: str) -> int:
    """Containers in which the path was absent (array element paths are never 'missing')."""
    if path.endswith(ARRAY):
        return 0
    return container_count(profile, path) - profile.paths[path].present
