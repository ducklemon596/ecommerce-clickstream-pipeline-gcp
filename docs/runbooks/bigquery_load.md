# Runbook: load an export into BigQuery

This runbook takes a verified export through to `glamira_raw.<table>` and checks the result. It assumes the one-time [GCP setup](gcp_setup.md) is done. How each step works is in the [warehouse guide](../../src/glamira_pipeline/warehouse/README.md).

A load has three steps:
1. **Publish.** Run `publish-export` where the export lives.
2. **Load.** The `bigquery-loader` function sees each table's `_load.json` and loads that table. Nothing needs to be run by hand.
3. **Verify.** Check the `_LOADED.json` markers and run the queries in `sql/checks/`.

Every step can be repeated safely. Publishing again uploads only objects that are missing. A repeated event, or a rerun of `load-bigquery`, reuses the same BigQuery job, so it never loads twice.

```bash
export REGION=asia-southeast1
export BUCKET=glamira-raw-datalake-asia-southeast1
```

## 1. Test load with the 100K sample (workstation)

`data/exports/sample-100k` is an `events` export of the 100K sample that has already passed `verify-export`.

```bash
uv run publish-export data/exports/sample-100k --bucket $BUCKET --prefix raw_sample --dataset glamira_raw_sample
gcloud storage cat gs://$BUCKET/raw_sample/events/export_id=sample-100k/_LOADED.json   # appears within a minute
for check in 01_tables 02_layout 03_events_by_day 04_events_shapes; do
  sed 's/{{dataset}}/glamira_raw_sample/g' sql/checks/$check.sql | bq query --use_legacy_sql=false
done
```

**Expected:** `_LOADED.json` shows 100,000 rows; `events` is partitioned by `time_stamp` and clustered by `collection`; and every count in `04` equals the conversion counts in the sample's `_manifest.json`.

## 2. Full load (on the VM)

```bash
gcloud compute instances start glamira-mongodb --zone ${REGION}-b
gcloud compute ssh glamira-mongodb --zone ${REGION}-b
```

On the VM, check out the commit to run, then:

```bash
uv sync --frozen
uv run publish-export <export dir> --bucket glamira-raw-datalake-asia-southeast1 --dataset glamira_raw --workers 8 \
  2>&1 | tee publish_full.log
```

Then stop the VM. The load runs in BigQuery and does not need it:

```bash
gcloud compute instances stop glamira-mongodb --zone ${REGION}-b
```

**Resource use measured on the full export:** about 71 s of wall time, of which the SHA-256 verification is about 51 s. Peak memory was 1.5 GB with `--workers 8`; resumable uploads buffer about 100 MiB per worker.

## 3. Verify

```bash
gcloud storage ls "gs://$BUCKET/raw/*/export_id=<export-id>/_LOADED.json"     # one per table
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="bigquery-loader" AND severity>=WARNING' --limit 20
for check in 01_tables 02_layout 03_events_by_day 04_events_shapes 05_numeric 06_join_coverage; do
  sed 's/{{dataset}}/glamira_raw/g' sql/checks/$check.sql | bq query --use_legacy_sql=false
done
```

| Query | Expected |
| --- | --- |
| `01_tables` | Each `row_count` equals the table's manifest rows |
| `02_layout` | Partitioning and clustering as declared; REQUIRED columns still REQUIRED |
| `03_events_by_day` | Each `_id` day equals its chunk in the events manifest |
| `04_events_shapes` | Equals the export's conversion counts (`object -> option_filter`, `'' -> []`) |
| `05_numeric` | Non-null counts equal to the source profiles |
| `06_join_coverage` | About 98.9% of events geolocated; about 1.5% of product references without attributes |

## When something goes wrong

| Symptom | Cause | Action |
| --- | --- | --- |
| `publish-export` exits 1: "exists with other content" | Another export already wrote this export ID | Publish under a new `--export-id`; never overwrite |
| No `_LOADED.json`; logs show *lacks run.routes.invoke* | `bq-loader` has no Cloud Run Invoker role | Grant it ([setup step 7](gcp_setup.md#7-let-the-trigger-call-the-function)). Eventarc retries by itself |
| A log line `load failed and will not be retried` | Permanent error: layout mismatch, missing part, row count | Fix the cause, then `uv run load-bigquery gs://…/_load.json` |
| Log warning `load not finished` | A job ran longer than 480 s, or a transient error | Nothing; Eventarc redelivers, and the redelivery waits on the same job |
| Two `loaded` log lines for one table | More than one trigger on the bucket | Delete the extra trigger. BigQuery still holds one job |
