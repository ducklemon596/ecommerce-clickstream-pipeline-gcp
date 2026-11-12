"""Remove address literals from an existing private research capture and metrics."""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def address(value: str) -> bool:
    """Return whether a string is a literal IPv4/IPv6 address, not a number ID."""
    if "." not in value and ":" not in value:
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def clean_text(value: str) -> str:
    """Redact literal URL hosts and aggregate hostname keys, preserving metrics."""
    if value.startswith(("http://", "https://")):
        parsed = urlsplit(value)
        if parsed.hostname and address(parsed.hostname):
            return urlunsplit((parsed.scheme, "redacted-address.invalid", parsed.path, parsed.query, ""))
    if address(value):
        return "redacted-address.invalid"
    if " @ " in value and address(value.rsplit(" @ ", 1)[1]):
        return value.rsplit(" @ ", 1)[0] + " @ redacted-address.invalid"
    return value


def clean(value):
    """Redact JSON strings/keys recursively; merge colliding integer counters."""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            updated_key, updated = clean_text(key), clean(item)
            if updated_key in result and isinstance(updated, int) and isinstance(result[updated_key], int):
                result[updated_key] += updated
            else:
                result[updated_key] = updated
        return result
    return value


def redact_file(path: Path) -> bool:
    """Replace only changed generated JSON artifacts via a private temp file.

    Returns whether address redaction changed this file. Never prints addresses
    or retains a raw backup; incomplete temp output does not replace the input.
    """
    temporary = path.with_suffix(path.suffix + ".redacting")
    changed = False
    try:
        with path.open() as source, temporary.open("x") as target:
            temporary.chmod(0o600)
            if path.suffix == ".jsonl":
                for line in source:
                    original = json.loads(line)
                    updated = clean(original)
                    changed |= updated != original
                    target.write(json.dumps(updated, ensure_ascii=False) + "\n")
            else:
                original = json.load(source)
                updated = clean(original)
                changed = updated != original
                json.dump(updated, target, ensure_ascii=False, indent=2)
        if changed:
            os.replace(temporary, path)
        else:
            temporary.unlink()
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return changed


def main() -> None:
    """Redact generated artifacts in an explicitly selected private directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(path for path in args.directory.rglob("*") if path.suffix in {".json", ".jsonl"})
    changed = sum(redact_file(path) for path in paths)
    print(f"Address-host redaction updated {changed} of {len(paths)} private artifacts; no raw addresses printed")


if __name__ == "__main__":
    main()
