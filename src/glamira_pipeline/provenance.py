"""Stable identities for pipeline inputs, recorded in run documents for provenance.

Identities never contain credentials: a file is identified by its content hash
and a MongoDB collection by namespace, server address and collection UUID.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from pymongo.collection import Collection


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file, read in 1 MiB blocks so memory stays bounded."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def mongo_collection_identity(collection: Collection) -> dict:
    """Return the namespace, server address and UUID of a collection.

    The UUID changes when a collection is dropped and recreated, so it
    distinguishes a re-restored source from the one a run actually read.
    """
    info = next(collection.database.list_collections(filter={"name": collection.name}), None)
    if not info or not info.get("info", {}).get("uuid"):
        raise ValueError("source collection UUID unavailable")
    return {"kind": "mongodb", "namespace": collection.full_name,
            "endpoint": list(collection.database.client.address),
            "uuid": bytes(info["info"]["uuid"]).hex()}


def git_sha() -> str | None:
    """Return the checked-out commit for run provenance, or None outside a git checkout."""
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, cwd=Path(__file__).parent).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
