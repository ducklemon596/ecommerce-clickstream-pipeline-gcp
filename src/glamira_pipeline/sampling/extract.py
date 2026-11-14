"""Stream a bounded BSON dump prefix into Extended JSON and metadata."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory

from bson import BSON, json_util
from bson.errors import InvalidBSON

from glamira_pipeline.config import DEFAULT_ARCHIVE, DEFAULT_SAMPLE, MAX_DOCUMENTS
from glamira_pipeline.load.bson_stream import DEFAULT_MEMBER, iter_documents, open_member

MEMBER = DEFAULT_MEMBER


def extract_sample(archive_path: Path, output: Path, limit: int) -> tuple[Path, Path]:
    """Extract a sequential BSON prefix as JSON and metadata.

    Args:
        archive_path: Compressed tar containing `dump/countly/summary.bson`.
        output: Destination JSON path; metadata uses the same filename stem.
        limit: Maximum number of BSON documents to extract, from 1 to 100,000.

    Returns:
        Paths to the generated JSON file and metadata file, respectively.

    Raises:
        ValueError: If options, the BSON stream, or the archive member are invalid.
        OSError, tarfile.TarError, InvalidBSON: If reading or writing fails.
    """
    if not 1 <= limit <= MAX_DOCUMENTS:
        raise ValueError(f"limit must be between 1 and {MAX_DOCUMENTS:,}")
    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if output.suffix.lower() != ".json":
        raise ValueError("--output must end in .json")
    metadata_output = output.with_suffix(".metadata.json")
    targets = (output, metadata_output)
    if archive_path.resolve() in {path.resolve() for path in targets}:
        raise ValueError("Sample outputs must differ from the source archive")
    output.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix=".sample-", dir=output.parent) as temporary_dir:
        temporary_paths = tuple(Path(temporary_dir) / path.name for path in targets)
        count = 0
        with open_member(archive_path, MEMBER) as member_file, \
                temporary_paths[0].open("w", encoding="utf-8") as json_file:
            json_file.write("[\n")
            for raw in iter_documents(member_file):
                document = BSON(raw).decode()
                encoded = json_util.dumps(document, json_options=json_util.CANONICAL_JSON_OPTIONS,
                                          ensure_ascii=False, indent=2)
                if count:
                    json_file.write(",\n")
                json_file.write(encoded)
                count += 1
                if count >= limit:
                    break
            json_file.write("\n]\n")
        if not count:
            raise ValueError("Source BSON member contains no documents")
        metadata = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_archive": archive_path.name,
            "source_archive_bytes": archive_path.stat().st_size,
            "archive_member": MEMBER,
            "sampling_method": "sequential prefix (non-random)",
            "requested_documents": limit,
            "source_documents_read": count,
            "json_documents_written": count,
            "json_encoding": "MongoDB Canonical Extended JSON array",
            "outputs": {output.name: temporary_paths[0].stat().st_size},
        }
        temporary_paths[1].write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        for temporary, target in zip(temporary_paths, targets):
            temporary.replace(target)
    return targets


def main() -> None:
    """Parse extraction CLI arguments and write the sample; exit on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--limit", type=int, default=10_000, help="Number of documents (1–100000)")
    parser.add_argument("--output", type=Path, default=DEFAULT_SAMPLE, help="JSON output path; metadata uses the same stem")
    args = parser.parse_args()
    try:
        outputs = extract_sample(args.archive, args.output, args.limit)
    except (OSError, ValueError, RuntimeError, tarfile.TarError, InvalidBSON) as exc:
        parser.exit(1, f"Extraction failed: {exc}\n")
    for path in outputs:
        print(f"Wrote {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
