"""Process one ``_load.json``: the shared path of the Cloud Function and ``load-bigquery``.

After a successful load, ``_LOADED.json`` is written next to the spec
(create-only) with the job ID and row count. A later delivery of the same
event sees it and does nothing, without calling BigQuery.
"""
from __future__ import annotations

from collections.abc import Collection
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json

from google.api_core.exceptions import PreconditionFailed

from glamira_pipeline.warehouse.bigquery import LoadError, LoadResult, load
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LOADED, LoadSpec


@dataclass(frozen=True)
class Outcome:
    status: str  # "loaded", "already_loaded" or "ignored"
    spec: str
    detail: dict


def process_load_spec(gcs, bq, bucket_name: str, name: str, *, allowed_datasets: Collection[str] | None = None,
                      wait_seconds: float | None = None, ignore_marker: bool = False) -> Outcome:
    """Load the table described by ``gs://<bucket_name>/<name>``.

    Raises LoadSpecError or LoadError when retrying cannot help, and
    TransientLoadError when it can.
    """
    uri = f"gs://{bucket_name}/{name}"
    if not name.endswith(f"/{LOAD_SPEC}"):
        return Outcome("ignored", uri, {})
    bucket = gcs.bucket(bucket_name)
    marker = bucket.blob(name[: -len(LOAD_SPEC)] + LOADED)
    if not ignore_marker and marker.exists():
        return Outcome("already_loaded", uri, json.loads(marker.download_as_text()))
    spec = LoadSpec.from_json(bucket.blob(name).download_as_text())
    if allowed_datasets is not None and spec.dataset not in allowed_datasets:
        raise LoadError(f"{uri}: dataset {spec.dataset!r} is not in the allowed datasets {sorted(allowed_datasets)}")
    result = load(spec, bq, gcs, wait_seconds=wait_seconds)
    detail = _record(marker, spec, result)
    return Outcome("loaded", uri, detail)


def _record(marker, spec: LoadSpec, result: LoadResult) -> dict:
    detail = {**asdict(result), "export_id": spec.export_id, "content_sha256": spec.content_sha256,
              "loaded_at": datetime.now(timezone.utc).isoformat()}
    try:
        marker.upload_from_string(json.dumps(detail, indent=2) + "\n", content_type="application/json",
                                  if_generation_match=0)
    except PreconditionFailed:
        pass  # another delivery recorded the same load first
    return detail
