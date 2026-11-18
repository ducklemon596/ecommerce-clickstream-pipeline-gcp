"""Cloud Function body: a GCS object was finalized; load it into BigQuery if it is a ``_load.json``.

Deployed as ``functions/bigquery_loader/main.py`` with an Eventarc trigger on
the export bucket and retries enabled. Eventarc delivers at least once:

- an object that is not a load spec returns at once, without any client;
- a spec whose ``_LOADED.json`` exists returns without calling BigQuery;
- ``TransientLoadError`` (a job still running or failing transiently) and
  unexpected API errors are raised, so Eventarc redelivers. The redelivery
  meets the same job ID (409) and waits for that job: retries poll, they never
  load twice;
- ``LoadError`` and ``LoadSpecError`` are logged as ERROR and swallowed,
  because a retry cannot fix them. Fix the cause, then run ``load-bigquery``.

Configuration: ``ALLOWED_DATASETS``, a comma-separated list of datasets the
function may write (required).
"""
from __future__ import annotations

from collections.abc import Mapping
import json
import os
import sys

from glamira_pipeline.warehouse.bigquery import LoadError, TransientLoadError
from glamira_pipeline.warehouse.runner import Outcome, process_load_spec
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LoadSpecError

WAIT_SECONDS = 480  # below the function timeout (540 s), so a slow job ends as a retry, not a kill
_CLIENTS: tuple | None = None


def handle(data: Mapping, *, env: Mapping[str, str] = os.environ, clients: tuple | None = None) -> Outcome | None:
    """Process one ``storage.object.v1.finalized`` event payload."""
    bucket, name = data["bucket"], data["name"]
    if not name.endswith(f"/{LOAD_SPEC}"):
        return Outcome("ignored", f"gs://{bucket}/{name}", {})
    allowed = {d.strip() for d in env.get("ALLOWED_DATASETS", "").split(",") if d.strip()}
    if not allowed:
        log("ERROR", "ALLOWED_DATASETS is not set; nothing is loaded", spec=f"gs://{bucket}/{name}")
        return None
    gcs, bq = clients or _default_clients()
    try:
        outcome = process_load_spec(gcs, bq, bucket, name, allowed_datasets=allowed, wait_seconds=WAIT_SECONDS)
    except TransientLoadError as exc:
        log("WARNING", f"load not finished; the event will be redelivered: {exc}", spec=f"gs://{bucket}/{name}")
        raise
    except (LoadError, LoadSpecError) as exc:
        log("ERROR", f"load failed and will not be retried: {exc}", spec=f"gs://{bucket}/{name}",
            error=type(exc).__name__)
        return None
    log("INFO", f"{outcome.status}: {outcome.spec}", **outcome.detail)
    return outcome


def log(severity: str, message: str, **fields) -> None:
    """One JSON line on stdout; Cloud Logging reads ``severity`` and ``message`` from it."""
    print(json.dumps({"severity": severity, "message": message, **fields}, default=str), file=sys.stdout,
          flush=True)


def _default_clients() -> tuple:
    global _CLIENTS
    if _CLIENTS is None:  # reused across invocations of a warm instance
        from google.cloud import bigquery, storage

        _CLIENTS = (storage.Client(), bigquery.Client())
    return _CLIENTS
