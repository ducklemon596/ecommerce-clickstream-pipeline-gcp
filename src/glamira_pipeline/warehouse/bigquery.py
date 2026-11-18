"""Load one exported table into BigQuery, idempotently, from its load spec.

1. **Sources.** Every part in the spec must exist in GCS with the size the export recorded.
2. **Table.** Created from the contract schema on first use (partitioning and
   clustering included). An existing table must have the same schema and layout.
3. **Job.** Submitted with a deterministic job ID and ``WRITE_TRUNCATE_DATA``,
   which atomically replaces the rows and keeps the table's schema. A
   resubmission gets ``409 Conflict`` and waits for the job already running
   or done, so a retry never starts a second load. A job that failed with a
   transient reason is retried under ``<job id>_r<n>``.
4. **Check.** The table's row count must equal the spec.

``TransientLoadError`` means "retry later" (the Cloud Function lets Eventarc
redeliver the event); ``LoadError`` means a retry cannot help.
"""
from __future__ import annotations

from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
import logging
import time

from google.api_core.exceptions import Conflict, GoogleAPICallError, NotFound
from google.cloud import bigquery

from glamira_pipeline.warehouse.spec import LoadSpec

LOGGER = logging.getLogger(__name__)
TRANSIENT_REASONS = frozenset({"backendError", "internalError", "rateLimitExceeded"})
# Standard SQL names the API may return in place of the legacy names in the schema files.
_TYPE_ALIASES = {"INT64": "INTEGER", "BOOL": "BOOLEAN", "FLOAT64": "FLOAT", "STRUCT": "RECORD"}


class LoadError(RuntimeError):
    """The load cannot succeed as specified; a retry will not help."""


class TransientLoadError(RuntimeError):
    """The load is still running or failed transiently; retrying the same spec is safe."""


@dataclass(frozen=True)
class LoadResult:
    destination: str
    job_id: str
    rows: int
    created_table: bool
    seconds: float


def job_config() -> bigquery.LoadJobConfig:
    """Avro with logical types (TIMESTAMP, NUMERIC), replacing the table's rows atomically."""
    return bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.AVRO,
        use_avro_logical_types=True,
        decimal_target_types=["NUMERIC"],
        write_disposition="WRITE_TRUNCATE_DATA",
    )


def load(spec: LoadSpec, bq: bigquery.Client, gcs, *, wait_seconds: float | None = None,
         max_attempts: int = 3) -> LoadResult:
    """Load ``spec`` into ``<bq.project>.<spec.dataset>.<spec.table>``; see the module docstring."""
    started = time.monotonic()
    check_sources(spec, gcs)
    location = bq.get_dataset(spec.dataset).location
    created = ensure_table(spec, bq)
    destination = f"{bq.project}.{spec.destination}"
    uris = [source.uri for source in spec.sources]
    for attempt in range(1, max_attempts + 1):
        job_id = spec.job_id(attempt)
        try:
            job = bq.load_table_from_uri(uris, destination, job_id=job_id, location=location,
                                         job_config=job_config())
            LOGGER.info("%s: submitted load job %s (%d files)", spec.destination, job_id, len(uris))
        except Conflict:
            job = bq.get_job(job_id, location=location)
            LOGGER.info("%s: job %s already exists (%s); waiting for it", spec.destination, job_id, job.state)
        try:
            job.result(timeout=wait_seconds)
            break
        except FutureTimeout:
            raise TransientLoadError(f"{spec.destination}: job {job_id} is still running") from None
        except GoogleAPICallError as exc:
            reason = (job.error_result or {}).get("reason")
            if reason not in TRANSIENT_REASONS:
                raise LoadError(f"{spec.destination}: job {job_id} failed ({reason}): {exc}") from None
            LOGGER.warning("%s: job %s failed transiently (%s); attempt %d of %d", spec.destination, job_id,
                           reason, attempt, max_attempts)
    else:
        raise TransientLoadError(f"{spec.destination}: {max_attempts} jobs failed transiently")
    rows = bq.get_table(destination).num_rows
    if rows != spec.rows:
        raise LoadError(f"{spec.destination}: table holds {rows:,} rows after job {job_id}, "
                        f"the export has {spec.rows:,}")
    result = LoadResult(spec.destination, job_id, rows, created, round(time.monotonic() - started, 1))
    LOGGER.info("%s: loaded %s rows with job %s", spec.destination, f"{rows:,}", job_id)
    return result


def check_sources(spec: LoadSpec, gcs) -> None:
    """Raise LoadError unless every source object exists with its recorded size."""
    for source in spec.sources:
        bucket_name, _, name = source.uri.removeprefix("gs://").partition("/")
        blob = gcs.bucket(bucket_name).get_blob(name)
        if blob is None:
            raise LoadError(f"{spec.destination}: missing source {source.uri}")
        if blob.size != source.bytes:
            raise LoadError(f"{spec.destination}: {source.uri} is {blob.size} bytes, the export wrote {source.bytes}")


def ensure_table(spec: LoadSpec, bq: bigquery.Client) -> bool:
    """Create the destination table if needed; return True if it was created.

    An existing table must match the spec's schema (names, types, modes,
    nesting), partitioning and clustering, otherwise LoadError.
    """
    destination = f"{bq.project}.{spec.destination}"
    try:
        existing = bq.get_table(destination)
    except NotFound:
        table = bigquery.Table(destination, schema=[bigquery.SchemaField.from_api_repr(f) for f in spec.schema])
        if spec.partition_by:
            table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY,
                                                                field=spec.partition_by)
        table.clustering_fields = list(spec.cluster_by) or None
        try:
            bq.create_table(table)
            LOGGER.info("%s: created table", spec.destination)
            return True
        except Conflict:  # created concurrently by another delivery of the same event
            existing = bq.get_table(destination)
    differences = _layout_differences(spec, existing)
    if differences:
        raise LoadError(f"{spec.destination}: existing table differs from the export ({'; '.join(differences)}); "
                        "load into a new table or migrate it deliberately")
    return False


def _layout_differences(spec: LoadSpec, table: bigquery.Table) -> list[str]:
    differences = []
    if _shape([f.to_api_repr() for f in table.schema]) != _shape(spec.schema):
        differences.append("schema")
    partition = table.time_partitioning.field if table.time_partitioning else None
    if partition != spec.partition_by:
        differences.append(f"partitioned by {partition}, expected {spec.partition_by}")
    if list(table.clustering_fields or ()) != list(spec.cluster_by):
        differences.append(f"clustered by {table.clustering_fields}, expected {list(spec.cluster_by)}")
    return differences


def _shape(fields) -> tuple:
    """Schema identity for comparison: names, types, modes and nesting (descriptions may be edited later)."""
    return tuple((f["name"], _TYPE_ALIASES.get(f["type"].upper(), f["type"].upper()),
                  (f.get("mode") or "NULLABLE").upper(), _shape(f.get("fields") or ())) for f in fields)
