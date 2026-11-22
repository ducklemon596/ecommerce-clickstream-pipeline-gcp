"""On-disk state of a resumable export: identity, chunk commit markers, lock.

The state is derived from files, never from logs. The only atomic primitive
used is ``os.replace`` within one filesystem, after ``fsync`` of the file and
followed by ``fsync`` of its directory:

- ``_export.json`` fixes the inputs of an export; a rerun with other inputs is refused.
- ``chunk=<id>/_SUCCESS.json`` is the commit point of a chunk. It is written only
  after every part of the chunk is durable, and lists each part's SHA-256.
- A chunk without a marker is uncommitted: its files are deleted and it is redone.
- A committed chunk is skipped only after its parts re-hash to the marker.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re

from glamira_pipeline.export.parquet_files import PartFile
from glamira_pipeline.provenance import file_sha256

IDENTITY = "_export.json"
SUCCESS = "_SUCCESS.json"
LOCK = ".lock"
_UNCOMMITTED = re.compile(r"^(part-\d{5}\.parquet(\.tmp)?|_SUCCESS\.json\.tmp)$")


class StateError(RuntimeError):
    """The on-disk state is inconsistent with this run; an operator must look."""


@contextmanager
def exclusive_lock(directory: Path) -> Iterator[None]:
    """Hold an exclusive, non-blocking lock on ``directory`` so two runs never write it at once."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / LOCK).open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StateError(f"{directory} is locked by another export run") from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def write_json_atomic(path: Path, payload: dict) -> None:
    """Write JSON as ``<name>.tmp``, fsync, rename over ``path`` and fsync the directory."""
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, default=str)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fsync_directory(path.parent)


def fsync_directory(directory: Path) -> None:
    """Make renames inside ``directory`` durable."""
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_json(path: Path) -> dict | None:
    """Return the JSON object at ``path``, or None if the file does not exist."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def claim_identity(directory: Path, identity: dict, recorded: dict) -> dict:
    """Write the export identity on the first run; on a rerun, require the same identity.

    ``identity`` holds the inputs that decide the output bytes; ``recorded``
    holds context (start time, git SHA, server address) kept but not compared.
    Returns the stored document.
    """
    path = directory / IDENTITY
    stored = read_json(path)
    if stored is None:
        stored = {"identity": identity, "recorded": recorded}
        write_json_atomic(path, stored)
        return stored
    differences = sorted(key for key in identity.keys() | stored["identity"].keys()
                         if identity.get(key) != stored["identity"].get(key))
    if differences:
        raise StateError(f"{path} was written with other inputs ({', '.join(differences)}); "
                         "use a new --export-id")
    return stored


def committed_chunk(directory: Path) -> dict | None:
    """Return the verified marker of a committed chunk, or None if the chunk is not committed.

    Raises StateError when a marker exists but a part is missing, changed, or
    joined by an unlisted part: committed data must never be silently redone.
    """
    marker = read_json(directory / SUCCESS)
    if marker is None:
        return None
    listed = {part["name"] for part in marker["files"]}
    present = {path.name for path in directory.glob("part-*.parquet")}
    if present != listed:
        raise StateError(f"{directory}: parts on disk {sorted(present)} differ from the marker {sorted(listed)}")
    for part in (PartFile(**p) for p in marker["files"]):
        if file_sha256(directory / part.name) != part.sha256:
            raise StateError(f"{directory / part.name}: SHA-256 differs from the committed marker")
    return marker


def reset_chunk(directory: Path) -> int:
    """Delete the files of an uncommitted chunk; return how many were removed.

    Only names the exporter writes are removed. Anything else in the directory
    raises StateError rather than being deleted.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / SUCCESS).exists():
        raise StateError(f"{directory} is committed; refusing to reset it")
    entries = list(directory.iterdir())
    foreign = sorted(path.name for path in entries if not _UNCOMMITTED.match(path.name))
    if foreign:
        raise StateError(f"{directory}: unexpected files {foreign}")
    for path in entries:
        path.unlink()
    if entries:
        fsync_directory(directory)
    return len(entries)


def commit_chunk(directory: Path, marker: dict) -> None:
    """Make the chunk's parts durable, then write its marker: the commit point."""
    fsync_directory(directory)
    write_json_atomic(directory / SUCCESS, marker)
