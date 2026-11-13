"""Coordinate one Counter scan, durable artifact, lookup, and verified publication."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import time
import uuid
from pymongo.collection import Collection
from glamira_pipeline.ip_location.counter import SCAN_BATCH, scan_in_memory, persist_counter
from glamira_pipeline.ip_location.lookup import bin_metadata
from glamira_pipeline.ip_location.output import lookup_and_upsert, verify_staging, publish_collection
from glamira_pipeline.ip_location.source import RUN_COLLECTION
from glamira_pipeline.provenance import file_sha256


def _bin_info(path: Path) -> dict:
    """Return actual BIN header metadata and streamed content identity for a run."""
    info = bin_metadata(path)
    info['sha256'] = file_sha256(path)
    info['database_id'] = info['sha256']
    return info


def _record_provenance(source: Collection, path: Path, info: dict) -> None:
    """Upsert BIN provenance before publishing documents that reference it."""
    source.database[RUN_COLLECTION].replace_one(
        {'_id': info['database_id']},
        {'_id': info['database_id'], 'database_id': info['database_id'],
         'source': path.name, 'database_date': info['date'],
         'database_edition': info['edition'], 'database_sha256': info['sha256'],
         'processed_at': datetime.now(timezone.utc)}, upsert=True)


def _lookup_summary(counter_path: Path, staging: Collection, bin_path: Path,
                    info: dict, expected: int) -> tuple[dict, float]:
    """Lookup a complete artifact and reject incomplete or inconsistent staging."""
    statuses, processed, seconds = lookup_and_upsert(counter_path, staging, bin_path, info)
    actual = verify_staging(staging, expected)
    if processed != expected or actual['status_unique_ips'] != statuses['status_unique_ips']:
        raise ValueError('staging status totals do not match lookup results')
    return statuses, seconds


def enrich_collection(source: Collection, target: str, bin_path: Path,
                      output_dir: Path, *, limit: int | None = None) -> dict:
    """Enrich source IPs into a new target and return aggregate metrics.

    Inputs: MongoDB source, target name in the same database, BIN and new private
    output directory; optional positive sample limit. Use for sample or full runs.
    Failures retain artifacts/staging; scans restart from zero. Existing targets
    are rejected. Keep the source immutable and use one writer for this target.
    """
    if not target or target in {source.name, RUN_COLLECTION, 'sample_metadata'} or '$' in target or '\x00' in target:
        raise ValueError('choose a separate valid result collection')
    if target in source.database.list_collection_names():
        raise ValueError('target collection already exists; choose a new target')
    info = _bin_info(bin_path)
    identity = next(source.database.list_collections(filter={'name': source.name}), None)
    if not identity or not identity.get('info', {}).get('uuid'):
        raise ValueError('source collection UUID is unavailable')
    source_uuid = bytes(identity['info']['uuid']).hex()
    output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    staging = source.database[f'{target}_staging_{uuid.uuid4().hex}']
    started = time.monotonic()
    scan = scan_in_memory(source, limit)
    scan_seconds = time.monotonic() - started
    persist_started = time.monotonic()
    artifact = output_dir / 'ip_counter.jsonl'
    manifest = persist_counter(scan, artifact, source.full_name, source_uuid, info)
    persistence_seconds = time.monotonic() - persist_started
    statuses, lookup_seconds = _lookup_summary(artifact, staging, bin_path, info, len(scan.addresses))
    resolved_events = statuses['status_events'].get('resolved', 0)
    resolved_ips = statuses['status_unique_ips'].get('resolved', 0)
    report = {
        'source': source.full_name, 'source_collection_uuid': source_uuid,
        'target': f'{source.database.name}.{target}', 'events': scan.events,
        'unique_valid_ips': len(scan.addresses), 'invalid_events': dict(scan.invalid),
        'lookup_statuses': statuses, 'bin': info, 'cursor_batch_size': SCAN_BATCH,
        'selection': 'unsorted non-random prefix' if limit else 'full collection',
        'event_coverage_percent': 100 * resolved_events / scan.events if scan.events else 0,
        'unique_ip_coverage_percent': 100 * resolved_ips / len(scan.addresses) if scan.addresses else 0,
        'coverage_target_percent': 80,
        'counter_sha256': manifest['counter_sha256'],
        'timings_seconds': {'cursor_read_and_decode': scan.cursor_seconds,
                           'normalize_and_counter': scan.normalize_seconds,
                           'scan_wall': scan_seconds, 'persistence': persistence_seconds,
                           'lookup_and_upsert': lookup_seconds},
    }
    _record_provenance(source, bin_path, info)
    # Rename refuses an existing target even if another process created it mid-run.
    publish_collection(staging, target, output_dir / 'ip_location_metrics.json', report)
    return report
