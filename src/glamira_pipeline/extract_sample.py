"""Stream a bounded BSON archive prefix into BSON and Extended JSON samples."""
from __future__ import annotations

import argparse
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO

from bson import BSON, json_util

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = PROJECT_ROOT / "glamira_ubl_oct2019_nov2019.tar.gz"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/summary_sample.bson"
MEMBER = "dump/countly/summary.bson"
MAX_DOCUMENTS = 100_000
MAX_BSON_SIZE = 16 * 1024 * 1024


def read_exact(stream: BinaryIO, size: int) -> bytes:
    """Read up to size bytes, handling streams that return short reads."""
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            break
        chunks.extend(chunk)
    return bytes(chunks)


def extract_sample(archive_path: Path, output: Path, limit: int) -> tuple[Path, Path, Path]:
    """Write matching sample files; publish them only after extraction succeeds."""
    if not 1 <= limit <= MAX_DOCUMENTS:
        raise ValueError(f"limit must be between 1 and {MAX_DOCUMENTS:,}")
    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if output.suffix.lower() != ".bson":
        raise ValueError("--output must end in .bson; the JSON path is derived from it")

    json_output = output.with_suffix(".json")
    metadata_output = output.with_suffix(".metadata.json")
    targets = (output, json_output, metadata_output)
    if archive_path.resolve() in {path.resolve() for path in targets}:
        raise ValueError("Sample outputs must differ from the source archive")
    output.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix=".sample-", dir=output.parent) as temporary_dir:
        temporary_paths = tuple(Path(temporary_dir) / path.name for path in targets)
        count = 0
        with tarfile.open(archive_path, mode="r|gz") as archive:
            for member in archive:
                if member.name == MEMBER and member.isfile():
                    member_file = archive.extractfile(member)
                    break
            else:
                raise ValueError(f"Could not find {MEMBER} in {archive_path}")
            if member_file is None:
                raise ValueError(f"Could not read {MEMBER}")

            with member_file, temporary_paths[0].open("wb") as bson_file, temporary_paths[1].open("w", encoding="utf-8") as json_file:
                json_file.write("[\n")
                while count < limit:
                    prefix = read_exact(member_file, 4)
                    if not prefix:
                        break
                    if len(prefix) != 4:
                        raise ValueError("Truncated BSON document length")
                    size = int.from_bytes(prefix, "little", signed=True)
                    if not 5 <= size <= MAX_BSON_SIZE:
                        raise ValueError(f"Invalid BSON document size: {size}")
                    body = read_exact(member_file, size - 4)
                    if len(body) != size - 4:
                        raise ValueError("Truncated BSON document")
                    raw = prefix + body
                    document = BSON(raw).decode()
                    encoded = json_util.dumps(
                        document, json_options=json_util.CANONICAL_JSON_OPTIONS,
                        ensure_ascii=False, indent=2,
                    )
                    if count:
                        json_file.write(",\n")
                    json_file.write(encoded)
                    bson_file.write(raw)
                    count += 1
                json_file.write("\n]\n")
        if count == 0:
            raise ValueError("Source BSON member contains no documents")

        metadata = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_archive": archive_path.name,
            "source_archive_bytes": archive_path.stat().st_size,
            "archive_member": MEMBER,
            "sampling_method": "sequential prefix (non-random)",
            "requested_documents": limit,
            "bson_documents_written": count,
            "json_documents_written": count,
            "json_encoding": "MongoDB Canonical Extended JSON array",
            "outputs": {path.name: temporary.stat().st_size for path, temporary in zip(targets[:2], temporary_paths[:2])},
        }
        temporary_paths[2].write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        for temporary, target in zip(temporary_paths, targets):
            temporary.replace(target)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--limit", type=int, default=10_000, help="Number of documents (1–100000)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="BSON output path; JSON and metadata use the same stem")
    args = parser.parse_args()
    try:
        outputs = extract_sample(args.archive, args.output, args.limit)
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(1, f"Extraction failed: {exc}\n")
    for path in outputs:
        print(f"Wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
