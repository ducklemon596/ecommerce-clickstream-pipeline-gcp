"""Schema model for the raw layer, and its two renderings: Avro and BigQuery JSON.

A table is declared once (see ``tables.py``). Each field carries its target
type and mode *and* the source key and conversion rule that fill it, so the
Avro schema, the BigQuery schema and the row converter cannot drift apart.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

REQUIRED, NULLABLE, REPEATED = "REQUIRED", "NULLABLE", "REPEATED"
STRING, INT64, BOOL, NUMERIC, TIMESTAMP = "STRING", "INT64", "BOOL", "NUMERIC", "TIMESTAMP"
SCALAR_TYPES = (STRING, INT64, BOOL, NUMERIC, TIMESTAMP)
# decimal(38, 9) is the widest Avro decimal BigQuery loads as NUMERIC.
DECIMAL_PRECISION, DECIMAL_SCALE = 38, 9
AVRO_NAMESPACE = "glamira.raw"

_AVRO_SCALAR = {
    STRING: "string",
    INT64: "long",
    BOOL: "boolean",
    NUMERIC: {"type": "bytes", "logicalType": "decimal",
              "precision": DECIMAL_PRECISION, "scale": DECIMAL_SCALE},
    TIMESTAMP: {"type": "long", "logicalType": "timestamp-micros"},
}
# Names accepted in every BigQuery JSON schema file (bq CLI, client libraries, Terraform).
_BQ_TYPE = {STRING: "STRING", INT64: "INTEGER", BOOL: "BOOLEAN", NUMERIC: "NUMERIC", TIMESTAMP: "TIMESTAMP"}


@dataclass(frozen=True)
class Record:
    """A nested STRUCT; ``name`` is its Avro record name, unique within a table."""

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
    """

    name: str
    record_name: str
    source_collection: str
    description: str
    fields: tuple[Field, ...]
    redundant_id: tuple[str, ...] = ()
    sensitive_key: bool = False


def avro_schema(table: Table) -> dict:
    """Return the Avro record schema of a table (BigQuery-compatible names and types)."""
    return {"type": "record", "name": table.record_name, "namespace": AVRO_NAMESPACE,
            "doc": table.description, "fields": _avro_fields(table.fields, set())}


def _avro_fields(fields: tuple[Field, ...], defined: set[str]) -> list[dict]:
    out = []
    for field in fields:
        if isinstance(field.type, Record):
            if field.type.name in defined:
                base = field.type.name
            else:
                defined.add(field.type.name)
                base = {"type": "record", "name": field.type.name,
                        "fields": _avro_fields(field.type.fields, defined)}
        else:
            base = _AVRO_SCALAR[field.type]
        entry: dict = {"name": field.name}
        if field.description:
            entry["doc"] = field.description
        if field.mode == REPEATED:
            entry.update(type={"type": "array", "items": base}, default=[])
        elif field.mode == NULLABLE:
            entry.update(type=["null", base], default=None)
        else:
            entry["type"] = base
        out.append(entry)
    return out


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
    """SHA-256 of the Avro schema text, recorded in export manifests."""
    return hashlib.sha256(schema_json(avro_schema(table)).encode()).hexdigest()
