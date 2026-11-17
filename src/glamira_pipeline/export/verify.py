"""Verify a finished export before it is uploaded or loaded, e.g. after it was moved or kept for a while.

The default check never decodes rows. It proves that the directory holds
exactly the bytes the export committed:

1. **Inventory, both ways.** Every part listed in ``_manifest.json`` exists,
   and nothing else does: no extra part, ``.tmp`` file or unknown ``chunk=`` directory.
2. **Content.** Each part's size and SHA-256 match the manifest, and
   ``content_sha256`` matches the listed parts.
3. **Contract.** The manifest's ``avro_schema_sha256`` equals the SHA-256 of
   the schema committed in the repository (``schemas/raw/<table>.avsc``) and of
   the schema copy in the export.

Row counts and writer schemas are not re-read: the SHA-256 covers every byte
that was counted and checked when the parts were written. ``full=True`` also
decodes every record, to test the Avro library itself (e.g. after an upgrade).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path

from fastavro import reader as avro_reader

from glamira_pipeline.export.exporter import MANIFEST, content_sha256
from glamira_pipeline.export.state import IDENTITY, LOCK, SUCCESS
from glamira_pipeline.provenance import file_sha256

LOGGER = logging.getLogger(__name__)


class VerificationError(RuntimeError):
    """The export directory does not match its manifest or the committed contract."""


@dataclass(frozen=True)
class VerifyResult:
    table: str
    files: int
    rows: int
    bytes: int
    decoded: bool


def table_directories(directory: Path) -> list[Path]:
    """``directory`` itself if it holds a manifest, else its table subdirectories that do."""
    if (directory / MANIFEST).exists():
        return [directory]
    tables = sorted(path.parent for path in directory.glob(f"*/{MANIFEST}"))
    if not tables:
        raise VerificationError(f"{directory}: no {MANIFEST} here or in its subdirectories")
    return tables


def verify_table(directory: Path, schema_dir: Path, *, full: bool = False) -> VerifyResult:
    """Verify one table export directory; raise VerificationError on the first difference."""
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    table = manifest["table"]
    if manifest.get("status") != "complete":
        raise VerificationError(f"{table}: manifest status is {manifest.get('status')!r}")
    _check_inventory(directory, manifest)
    _check_schema(directory, schema_dir, manifest)
    for part in manifest["files"]:
        path = directory / part["name"]
        if path.stat().st_size != part["bytes"]:
            raise VerificationError(f"{part['name']}: {path.stat().st_size} bytes, manifest says {part['bytes']}")
        if file_sha256(path) != part["sha256"]:
            raise VerificationError(f"{part['name']}: SHA-256 differs from the manifest")
    if content_sha256(manifest["files"]) != manifest["content_sha256"]:
        raise VerificationError(f"{table}: content_sha256 does not match the listed parts")
    if full:
        _decode_all(directory, manifest)
    LOGGER.info("%s: %d parts verified%s", table, len(manifest["files"]), " and decoded" if full else "")
    return VerifyResult(table, len(manifest["files"]), manifest["rows"], manifest["bytes"], full)


def _check_inventory(directory: Path, manifest: dict) -> None:
    table = manifest["table"]
    chunks = {f"chunk={chunk['id']}" for chunk in manifest["chunks"]}
    expected = {part["name"] for part in manifest["files"]}
    expected |= {f"{chunk}/{SUCCESS}" for chunk in chunks}
    expected |= {MANIFEST, IDENTITY, f"{table}.avsc", f"{table}.bq.json"}
    present = set()
    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        if path.is_dir():
            if relative not in chunks:
                present.add(relative + "/")
        elif relative != LOCK:
            present.add(relative)
    missing, extra = sorted(expected - present), sorted(present - expected)
    if missing or extra:
        raise VerificationError(f"{table}: directory differs from the manifest; "
                                f"missing {missing or 'nothing'}, unexpected {extra or 'nothing'}")


def _check_schema(directory: Path, schema_dir: Path, manifest: dict) -> None:
    table, recorded = manifest["table"], manifest["avro_schema_sha256"]
    committed = schema_dir / f"{table}.avsc"
    if not committed.exists():
        raise VerificationError(f"{table}: no committed schema at {committed}")
    if file_sha256(committed) != recorded:
        raise VerificationError(f"{table}: exported with Avro schema {recorded[:12]}, "
                                f"but the committed {committed.name} is {file_sha256(committed)[:12]}")
    if file_sha256(directory / f"{table}.avsc") != recorded:
        raise VerificationError(f"{table}: the schema copy in the export differs from the manifest")


def _decode_all(directory: Path, manifest: dict) -> None:
    schema = json.loads((directory / f"{manifest['table']}.avsc").read_text(encoding="utf-8"))
    names = {schema["name"], f"{schema['namespace']}.{schema['name']}"}
    for part in manifest["files"]:
        with (directory / part["name"]).open("rb") as stream:
            records = avro_reader(stream)
            if records.writer_schema.get("name") not in names:
                raise VerificationError(f"{part['name']}: unexpected writer schema")
            count = sum(1 for _ in records)
        if count != part["rows"]:
            raise VerificationError(f"{part['name']}: decoded {count} rows, manifest says {part['rows']}")
