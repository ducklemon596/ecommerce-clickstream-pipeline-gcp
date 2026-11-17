"""Convert decoded MongoDB documents into Avro rows of a raw-layer table.

Raw keeps values and changes only representations (ObjectId → hex, int →
decimal string, ``false`` → ``"false"``, 0/1 → bool, PII → HMAC). Anything the
contract does not plan for raises ``SchemaViolation``: an unknown key, a type
outside the field's rule, a missing REQUIRED value, a non-integral ID or a
decimal finer than the target scale. Nothing is dropped or coerced silently;
every non-identity conversion is counted in ``Converter.stats`` ("path: conversion" -> count).
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from bson.decimal128 import Decimal128
from bson.objectid import ObjectId

from glamira_pipeline.export.pii import PiiHasher
from glamira_pipeline.export.schema import (BOOL, DECIMAL_SCALE, INT64, NUMERIC, REPEATED, REQUIRED, STRING,
                                            TIMESTAMP, Field, Record, Table)

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class SchemaViolation(ValueError):
    """A document does not fit the table contract; the message names the path."""


class Converter:
    """Row converter for one table; holds the PII hasher and the conversion counters."""

    def __init__(self, table: Table, hasher: PiiHasher) -> None:
        self.table = table
        self.hasher = hasher
        self.stats: Counter[str] = Counter()
        self._sources: dict[int, frozenset[str]] = {}

    def convert(self, document: Mapping[str, Any]) -> dict:
        """Return the Avro row for one source document; raise SchemaViolation if it does not fit."""
        allowed: frozenset[str] = frozenset()
        if self.table.redundant_id:
            self._check_redundant_id(document)
            allowed = frozenset({"_id"})
        return self._record(document, self.table.fields, "", allowed)

    def _check_redundant_id(self, document: Mapping[str, Any]) -> None:
        keys = self.table.redundant_id
        expected = document.get(keys[0]) if len(keys) == 1 else {k: document.get(k) for k in keys}
        if document.get("_id") != expected:
            raise SchemaViolation(f"_id does not equal {', '.join(keys)}")

    def _record(self, document: Any, fields: tuple[Field, ...], path: str,
                allowed: frozenset[str] = frozenset()) -> dict:
        label = path.rstrip(".") or "<document>"
        if not isinstance(document, Mapping):
            raise SchemaViolation(f"{label}: expected an object, got {type(document).__name__}")
        sources = self._sources.get(id(fields))
        if sources is None:
            sources = self._sources[id(fields)] = frozenset(f.source for f in fields)
        unknown = document.keys() - sources - allowed
        if unknown:
            raise SchemaViolation(f"{label}: unknown keys {sorted(unknown)}")
        row = {}
        for field in fields:
            where = f"{path}{field.source}"
            value = document.get(field.source)
            if isinstance(field.type, Record):
                value = self._nested(field, value, where)
            else:
                value = None if value is None else _SCALAR_RULES[field.rule](self, field, value, where)
            if value is None and field.mode == REQUIRED:
                raise SchemaViolation(f"{where}: REQUIRED value is missing or null")
            row[field.name] = value
        return row

    # -- nested records ---------------------------------------------------------------------

    def _nested(self, field: Field, value: Any, where: str) -> Any:
        record: Record = field.type  # type: ignore[assignment]
        rule = field.rule
        if rule == "empty_string_as_empty_array" and value == "":
            self.stats[f"{where}: '' -> []"] += 1
            return []
        if rule == "array_form" and isinstance(value, Mapping):
            return []  # the object form goes to its own column
        if rule == "object_form":
            if isinstance(value, list):
                return None  # the array form goes to its own column
            if isinstance(value, Mapping):
                self.stats[f"{where}: object -> {field.name}"] += 1
        if field.mode == REPEATED:
            if value is None:
                return []
            if not isinstance(value, list):
                raise SchemaViolation(f"{where}: expected an array, got {type(value).__name__}")
            return [self._record(item, record.fields, f"{where}[].") for item in value]
        return None if value is None else self._record(value, record.fields, f"{where}.")

    # -- scalar rules (value is never None here) --------------------------------------------

    def _as_is(self, field: Field, value: Any, where: str) -> Any:
        if field.type == STRING and isinstance(value, str):
            return value
        if field.type == INT64 and isinstance(value, int) and not isinstance(value, bool):
            return value
        if field.type == BOOL and isinstance(value, bool):
            return value
        if field.type == NUMERIC and isinstance(value, (Decimal128, Decimal)):
            return _decimal(value, where)
        if field.type == TIMESTAMP and isinstance(value, datetime):
            return _micros(value)
        raise SchemaViolation(f"{where}: expected {field.type}, got {type(value).__name__}")

    def _objectid_hex(self, field: Field, value: Any, where: str) -> str:
        if not isinstance(value, ObjectId):
            raise SchemaViolation(f"{where}: expected ObjectId, got {type(value).__name__}")
        return str(value)

    def _unix_seconds(self, field: Field, value: Any, where: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaViolation(f"{where}: expected int Unix seconds, got {type(value).__name__}")
        return value * 1_000_000

    def _integer_as_string(self, field: Field, value: Any, where: str) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            raise SchemaViolation(f"{where}: bool where an integer or string was expected")
        if isinstance(value, float):
            if not value.is_integer():
                raise SchemaViolation(f"{where}: non-integral number {value!r}")
            self.stats[f"{where}: double -> string"] += 1
            return str(int(value))
        if isinstance(value, int):
            self.stats[f"{where}: int -> string"] += 1
            return str(value)
        raise SchemaViolation(f"{where}: expected an integer or string, got {type(value).__name__}")

    def _bool_as_string(self, field: Field, value: Any, where: str) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            self.stats[f"{where}: bool -> string"] += 1
            return "true" if value else "false"
        raise SchemaViolation(f"{where}: expected a string or bool, got {type(value).__name__}")

    def _int_as_bool(self, field: Field, value: Any, where: str) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            self.stats[f"{where}: int -> bool"] += 1
            return bool(value)
        raise SchemaViolation(f"{where}: expected a bool or 0/1, got {value!r}")

    def _number_as_decimal(self, field: Field, value: Any, where: str) -> Decimal:
        if isinstance(value, (Decimal128, Decimal)):
            return _decimal(value, where)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SchemaViolation(f"{where}: expected a number, got {type(value).__name__}")
        self.stats[f"{where}: {type(value).__name__} -> decimal"] += 1
        return _decimal(Decimal(str(value)), where)

    def _hmac(self, field: Field, value: Any, where: str) -> str:
        return self._count_hash(where, self.hasher.text(_string(value, where)))

    def _hmac_email(self, field: Field, value: Any, where: str) -> str:
        return self._count_hash(where, self.hasher.email(_string(value, where)))

    def _hmac_ip(self, field: Field, value: Any, where: str) -> str:
        digest, valid = self.hasher.ip(_string(value, where))
        if not valid:
            self.stats[f"{where}: invalid IP hashed as stored"] += 1
        return self._count_hash(where, digest)

    def _count_hash(self, where: str, digest: str) -> str:
        self.stats[f"{where}: hmac" if digest else f"{where}: '' kept"] += 1
        return digest


_SCALAR_RULES: dict[str, Callable[[Converter, Field, Any, str], Any]] = {
    "as_is": Converter._as_is,
    "objectid_hex": Converter._objectid_hex,
    "unix_seconds": Converter._unix_seconds,
    "integer_as_string": Converter._integer_as_string,
    "bool_as_string": Converter._bool_as_string,
    "int_as_bool": Converter._int_as_bool,
    "number_as_decimal": Converter._number_as_decimal,
    "hmac": Converter._hmac,
    "hmac_email": Converter._hmac_email,
    "hmac_ip": Converter._hmac_ip,
}
RECORD_RULES = ("as_is", "array_form", "object_form", "empty_string_as_empty_array")


def _string(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise SchemaViolation(f"{where}: expected a string, got {type(value).__name__}")
    return value


def _decimal(value: Decimal128 | Decimal, where: str) -> Decimal:
    number = value.to_decimal() if isinstance(value, Decimal128) else value
    if not number.is_finite():
        raise SchemaViolation(f"{where}: non-finite decimal")
    exponent = number.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -DECIMAL_SCALE:
        raise SchemaViolation(f"{where}: more than {DECIMAL_SCALE} decimal places")
    return number


def _micros(value: datetime) -> int:
    """Microseconds since the epoch; naive datetimes are UTC, as PyMongo returns them."""
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    delta = aware - _EPOCH
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def check_rules(table: Table) -> None:
    """Raise ValueError if a field names a rule the converter does not implement."""
    def walk(fields: tuple[Field, ...]) -> None:
        for field in fields:
            if isinstance(field.type, Record):
                if field.rule not in RECORD_RULES:
                    raise ValueError(f"{table.name}.{field.name}: unknown record rule {field.rule!r}")
                walk(field.type.fields)
            elif field.rule not in _SCALAR_RULES:
                raise ValueError(f"{table.name}.{field.name}: unknown rule {field.rule!r}")
    walk(table.fields)
