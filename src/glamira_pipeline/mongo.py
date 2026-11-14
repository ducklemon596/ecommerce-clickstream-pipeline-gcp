"""MongoDB connections shared by every pipeline command.

MongoDB on the VM is bound to loopback and reached directly on the VM or
through an SSH tunnel, so only ``localhost``/``127.0.0.1``/``::1`` hosts are
accepted. The URI comes from ``MONGODB_URI`` and is never logged.
"""
from __future__ import annotations

from collections.abc import Mapping
import os

from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

URI_ENV = "MONGODB_URI"
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def loopback_hosts(uri: str) -> list[list]:
    """Return the URI's host/port pairs; raise ValueError for SRV or non-loopback hosts."""
    if not uri.startswith("mongodb://"):
        raise ValueError("only mongodb:// URIs to a loopback host are supported")
    parsed = parse_uri(uri, warn=False)
    if any(host.lower() not in LOOPBACK_HOSTS for host, _ in parsed["nodelist"]):
        raise ValueError("MongoDB host must be loopback (on the VM or through an SSH tunnel)")
    return [[host.lower(), port] for host, port in parsed["nodelist"]]


def connect(uri: str, *, timeout_ms: int = 10_000) -> MongoClient:
    """Create a client for a loopback URI.

    ``directConnection`` stops replica-set discovery from redirecting the
    client to hosts named in the server's configuration.
    """
    loopback_hosts(uri)
    return MongoClient(uri, directConnection=True, appname="glamira-pipeline",
                       serverSelectionTimeoutMS=timeout_ms, connectTimeoutMS=timeout_ms)


def client_from_env(env: Mapping[str, str] = os.environ) -> MongoClient:
    """Connect using ``MONGODB_URI``; raise ValueError when it is unset or not loopback."""
    uri = env.get(URI_ENV)
    if not uri:
        raise ValueError(f"set {URI_ENV} in the environment (see .env.example)")
    return connect(uri)
