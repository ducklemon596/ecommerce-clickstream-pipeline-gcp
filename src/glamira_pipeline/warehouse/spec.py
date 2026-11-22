"""The load spec: everything a BigQuery load of one exported table needs, as ``_load.json``.

``publish-export`` writes it last, next to the uploaded parts, so its arrival
in GCS means the table export is complete in the bucket; it is what triggers
the Cloud Function. The spec is deterministic (no timestamps), so publishing
the same export twice produces the same object.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re

LOAD_SPEC = "_load.json"
LOADED = "_LOADED.json"
_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,1023}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_JOB_UNSAFE = re.compile(r"[^A-Za-z0-9_-]")


class LoadSpecError(ValueError):
    """A ``_load.json`` is missing fields or holds invalid values."""


@dataclass(frozen=True)
class Source:
    """One Parquet part to load: its ``gs://`` URI and its size from the export manifest."""

    uri: str
    bytes: int


@dataclass(frozen=True)
class LoadSpec:
    export_id: str
    table: str
    dataset: str
    rows: int
    content_sha256: str
    sources: tuple[Source, ...]
    schema: tuple[dict, ...]
    partition_by: str | None = None
    cluster_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, value in (("table", self.table), ("dataset", self.dataset)):
            if not _NAME.match(value):
                raise LoadSpecError(f"invalid {label} name {value!r}")
        if not self.export_id:
            raise LoadSpecError("export_id is empty")
        if self.rows < 0:
            raise LoadSpecError("rows is negative")
        if not _SHA256.match(self.content_sha256):
            raise LoadSpecError("content_sha256 is not a SHA-256 hex digest")
        if not self.sources:
            raise LoadSpecError("no sources")
        for source in self.sources:
            if not source.uri.startswith("gs://") or source.bytes < 0:
                raise LoadSpecError(f"invalid source {source.uri!r}")
        if not self.schema:
            raise LoadSpecError("empty schema")
        columns = {field.get("name") for field in self.schema}
        for column in (self.partition_by, *self.cluster_by):
            if column is not None and column not in columns:
                raise LoadSpecError(f"{column!r} is not a column of {self.table}")

    @property
    def destination(self) -> str:
        return f"{self.dataset}.{self.table}"

    def job_id(self, attempt: int = 1) -> str:
        """Deterministic BigQuery job ID; resubmitting the same load gets 409 instead of a second job."""
        base = _JOB_UNSAFE.sub("_", f"load_{self.dataset}_{self.table}_{self.export_id}_{self.content_sha256[:12]}")
        return base if attempt == 1 else f"{base}_r{attempt}"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> LoadSpec:
        try:
            data = json.loads(text)
            return cls(
                export_id=str(data["export_id"]),
                table=data["table"],
                dataset=data["dataset"],
                rows=int(data["rows"]),
                content_sha256=data["content_sha256"],
                sources=tuple(Source(str(s["uri"]), int(s["bytes"])) for s in data["sources"]),
                schema=tuple(data["schema"]),
                partition_by=data.get("partition_by"),
                cluster_by=tuple(data.get("cluster_by") or ()),
            )
        except LoadSpecError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise LoadSpecError(f"malformed load spec: {type(exc).__name__}: {exc}") from None
