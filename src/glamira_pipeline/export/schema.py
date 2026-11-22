"""Schema model for the raw layer, and its two renderings: BigQuery JSON and the Parquet (Arrow) schema.

A table is declared once (see ``tables.py``). Each field carries its target
type and mode *and* the source key and conversion rule that fill it. The
BigQuery schema is rendered from the declaration, and the Parquet schema of
the files is derived from the BigQuery schema, so the files, the BigQuery
table and the row converter cannot drift apart.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import pyarrow as pa

REQUIRED, NULLABLE, REPEATED = "REQUIRED", "NULLABLE", "REPEATED"
STRING, INT64, BOOL, NUMERIC, TIMESTAMP = "STRING", "INT64", "BOOL", "NUMERIC", "TIMESTAMP"
SCALAR_TYPES = (STRING, INT64, BOOL, NUMERIC, TIMESTAMP)
# decimal(38, 9) is BigQuery NUMERIC exactly.
DECIMAL_PRECISION, DECIMAL_SCALE = 38, 9
# Names accepted in every BigQuery JSON schema file (bq CLI, client libraries, Terraform).
_BQ_TYPE = {STRING: "STRING", INT64: "INTEGER", BOOL: "BOOLEAN", NUMERIC: "NUMERIC", TIMESTAMP: "TIMESTAMP"}


@dataclass(frozen=True)
class Record:
    """A nested STRUCT; ``name`` labels the struct type in documentation."""

    name: str
    fields: tuple[Field, ...]


@dataclass(frozen=True)
class Field:
    """One output column.

    ``source`` is the key read from the MongoDB document (defaults to ``name``);
    ``rule`` names the conversion applied to it (see ``convert.py``).
    """

    name: str
    type: str | Record
    mode: str = NULLABLE
    description: str = ""
    source: str | None = None
    rule: str = "as_is"

    def __post_init__(self) -> None:
        if self.mode not in (REQUIRED, NULLABLE, REPEATED):
            raise ValueError(f"{self.name}: unknown mode {self.mode}")
        if not isinstance(self.type, Record) and self.type not in SCALAR_TYPES:
            raise ValueError(f"{self.name}: unknown type {self.type}")
        if self.source is None:
            object.__setattr__(self, "source", self.name)


@dataclass(frozen=True)
class Table:
    """A raw-layer table exported from one MongoDB collection.

    ``redundant_id`` names the fields the source ``_id`` duplicates; the
    converter checks the equality and drops ``_id``. ``sensitive_key`` keeps
    the source ``_id`` out of error messages (it is a raw IP for ``ip_locations``).
    ``partition_by`` (a REQUIRED TIMESTAMP column, partitioned by day) and
    ``cluster_by`` (up to four top-level scalar columns) shape the BigQuery table.
    """

    name: str
    source_collection: str
    description: str
    fields: tuple[Field, ...]
    redundant_id: tuple[str, ...] = ()
    sensitive_key: bool = False
    partition_by: str | None = None
    cluster_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        columns = {field.name: field for field in self.fields}
        if self.partition_by is not None:
            field = columns.get(self.partition_by)
            if field is None or field.type != TIMESTAMP or field.mode != REQUIRED:
                raise ValueError(f"{self.name}: partition_by must name a REQUIRED TIMESTAMP column")
        if len(self.cluster_by) > 4:
            raise ValueError(f"{self.name}: BigQuery allows at most four clustering columns")
        for name in self.cluster_by:
            field = columns.get(name)
            if field is None or isinstance(field.type, Record) or field.mode == REPEATED:
                raise ValueError(f"{self.name}: cluster_by column {name!r} must be a top-level scalar")


def bigquery_schema(table: Table) -> list[dict]:
    """Return the BigQuery JSON schema (the format of ``bq mk --schema``)."""
    return _bq_fields(table.fields)


def _bq_fields(fields: tuple[Field, ...]) -> list[dict]:
    out = []
    for field in fields:
        entry = {"name": field.name, "mode": field.mode}
        if isinstance(field.type, Record):
            entry["type"] = "RECORD"
            entry["fields"] = _bq_fields(field.type.fields)
        else:
            entry["type"] = _BQ_TYPE[field.type]
        if field.description:
            entry["description"] = field.description
        out.append(entry)
    return out


def schema_json(schema: dict | list) -> str:
    """Serialize a schema deterministically (the committed files use this exact form)."""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def schema_fingerprint(table: Table) -> str:
    """SHA-256 of the committed BigQuery schema text (``schemas/raw/<table>.bq.json``), recorded in manifests."""
    return hashlib.sha256(schema_json(bigquery_schema(table)).encode()).hexdigest()


def parquet_schema(bigquery_fields: list[dict]) -> pa.Schema:
    """The Arrow schema of the Parquet parts, derived from a BigQuery JSON schema.

    REQUIRED → not nullable, NULLABLE → nullable, REPEATED → a non-null list
    (loaded as REPEATED with ``enable_list_inference``), RECORD → struct,
    NUMERIC → decimal128(38, 9), TIMESTAMP → microseconds in UTC.
    """
    scalar = {"STRING": pa.string(), "INTEGER": pa.int64(), "BOOLEAN": pa.bool_(),
              "NUMERIC": pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), "TIMESTAMP": pa.timestamp("us", tz="UTC")}

    def field(spec: dict) -> pa.Field:
        kind = pa.struct([field(child) for child in spec["fields"]]) if spec["type"] == "RECORD" else scalar[spec["type"]]
        mode = spec.get("mode", NULLABLE)
        if mode == REPEATED:
            return pa.field(spec["name"], pa.list_(kind), nullable=False)
        return pa.field(spec["name"], kind, nullable=mode != REQUIRED)

    return pa.schema([field(spec) for spec in bigquery_fields])
