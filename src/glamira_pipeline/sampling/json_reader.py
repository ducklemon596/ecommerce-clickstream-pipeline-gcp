"""Stream document arrays from MongoDB Extended JSON without loading the file."""
from __future__ import annotations

from functools import partial
import json
from pathlib import Path
from typing import Any, Iterator

from bson import json_util

MAX_DOCUMENT_CHARACTERS = 64 * 1024 * 1024


def iter_json_documents(path: Path, chunk_size: int = 64 * 1024) -> Iterator[dict[str, Any]]:
    """Decode a JSON array one document at a time, restoring canonical BSON types.

    Args:
        path: Input JSON array file in UTF-8.
        chunk_size: Number of characters read at a time; must be positive.

    Yields:
        One decoded BSON-compatible event document at a time.

    Raises:
        ValueError: If the array is malformed, has non-object elements, or
            exceeds the per-document character cap. OSError: If reading fails.

    Use for bounded-memory assessment; only consumed input is validated.
    """
    if chunk_size < 1:
        raise ValueError("JSON chunk size must be positive")
    decoder = json.JSONDecoder(object_hook=partial(
        json_util.object_hook, json_options=json_util.CANONICAL_JSON_OPTIONS,
    ))
    with path.open("r", encoding="utf-8-sig") as stream:
        buffer = ""
        position = 0
        eof = False

        def refill() -> bool:
            """Read the next chunk, discarding consumed characters; return whether data arrived."""
            nonlocal buffer, position, eof
            if eof:
                return False
            fragment = stream.read(chunk_size)
            buffer = buffer[position:] + fragment
            position = 0
            if not fragment:
                eof = True
            return bool(fragment)

        def skip_space() -> None:
            """Advance past whitespace, refilling the buffer as needed; return no value."""
            nonlocal position
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
                if position < len(buffer) or not refill():
                    return

        skip_space()
        if position >= len(buffer) or buffer[position] != "[":
            raise ValueError("JSON sample must be an array of documents")
        position += 1
        skip_space()
        empty = position < len(buffer) and buffer[position] == "]"
        if empty:
            position += 1
        while not empty:
            while True:
                try:
                    document, end = decoder.raw_decode(buffer, position)
                    if end - position > MAX_DOCUMENT_CHARACTERS:
                        raise ValueError("JSON document exceeds the 64 MiB character cap")
                    position = end
                    break
                except json.JSONDecodeError as exc:
                    # A document may cross a chunk boundary, so retry until EOF.
                    if len(buffer) - position > MAX_DOCUMENT_CHARACTERS:
                        raise ValueError("JSON document exceeds the 64 MiB character cap") from exc
                    if not refill():
                        raise ValueError("Malformed or truncated JSON sample") from exc
            if not isinstance(document, dict):
                raise ValueError("Every JSON sample element must be a document object")
            yield document
            skip_space()
            if position >= len(buffer):
                raise ValueError("Truncated JSON array")
            separator = buffer[position]
            position += 1
            if separator == "]":
                break
            if separator != ",":
                raise ValueError("Expected a comma or closing bracket after JSON document")
            skip_space()
        skip_space()
        if position < len(buffer):
            raise ValueError("Unexpected trailing content after JSON sample array")
