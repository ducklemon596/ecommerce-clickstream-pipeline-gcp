# Runbook: first load of the raw layer into BigQuery

This runbook does the first load in four parts:
- **Setup:** create the GCS bucket, the BigQuery datasets and a least-privilege service account, then deploy the `bigquery-loader` Cloud Function.
- **Test:** load the 100K sample into `raw_sample`.
- **Full load:** load the full export into `raw`.
- **Repeats:** check that repeating any step changes nothing.

How the pieces work is in the [warehouse guide](../../src/glamira_pipeline/warehouse/README.md).

Run each block yourself and keep the output: the load report is written from it. Steps 1–3 are done once per project.

## 0. Variables

```bash
export PROJECT=<project-id>
export REGION=asia-southeast1
export BUCKET=glamira-raw-data-asia-southeast1
export SA=bq-loader@$PROJECT.iam.gserviceaccount.com
gcloud config set project $PROJECT
```

## 1. APIs, bucket and datasets

```bash
gcloud services enable cloudfunctions.googleapis.com run.googleapis.com eventarc.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com pubsub.googleapis.com

gcloud storage buckets create gs://$BUCKET --location $REGION --default-storage-class STANDARD \
  --uniform-bucket-level-access --public-access-prevention

bq mk --location $REGION --dataset --description "Raw layer, loaded from verified Avro exports" $PROJECT:raw
bq mk --location $REGION --dataset --description "Raw layer test loads (100K sample)" $PROJECT:raw_sample
```

**Why these settings.** The bucket and the datasets must be in the same region, because a load job cannot read a bucket in another location. Uniform access and public-access prevention keep the raw data private.

## 2. Service account for the loader

```bash
gcloud iam service-accounts create bq-loader --display-name "BigQuery raw loader (Cloud Function)"

gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/bigquery.jobUser
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$SA --role roles/eventarc.eventReceiver
for dataset in raw raw_sample; do
  bq add-iam-policy-binding --member serviceAccount:$SA --role roles/bigquery.dataEditor $PROJECT:$dataset
done
for role in roles/storage.objectViewer roles/storage.objectCreator; do
  gcloud storage buckets add-iam-policy-binding gs://$BUCKET --member serviceAccount:$SA --role $role
done

# Bucket events reach Eventarc through Pub/Sub, published by the Cloud Storage service agent.
GCS_AGENT=$(gcloud storage service-agent --project $PROJECT)
gcloud projects add-iam-policy-binding $PROJECT --member serviceAccount:$GCS_AGENT --role roles/pubsub.publisher
```

The loader can read objects and create new ones (`_LOADED.json`), but it cannot overwrite or delete objects, and it can write only the two datasets.

## 3. Deploy the function

```bash
PROJECT=$PROJECT BUCKET=$BUCKET SERVICE_ACCOUNT=$SA ALLOWED_DATASETS=raw,raw_sample \
  scripts/deploy_bigquery_loader.sh --dry-run          # check the command and the staged files
PROJECT=$PROJECT BUCKET=$BUCKET SERVICE_ACCOUNT=$SA ALLOWED_DATASETS=raw,raw_sample \
  scripts/deploy_bigquery_loader.sh
gcloud functions add-invoker-policy-binding bigquery-loader --region $REGION --member serviceAccount:$SA
```

If the deploy reports that the trigger's service agents are not ready, wait a few minutes and run it again. Eventarc sets up its agents on first use in a project.

## 4. Test load: the 100K sample

On the workstation, the sample export is `data/exports/sample-100k`. It holds `events` only, 100,000 rows from 2020-06-04, and already passed `verify-export`.

```bash
gcloud auth application-default login                       # once; credentials for publish-export and load-bigquery
uv run publish-export data/exports/sample-100k --bucket $BUCKET --prefix raw_sample --dataset raw_sample

gcloud functions logs read bigquery-loader --region $REGION --limit 20
gcloud storage cat gs://$BUCKET/raw_sample/events/export_id=sample-100k/_LOADED.json

for check in 01_tables 02_layout 03_events_by_day 04_events_shapes; do
  sed 's/{{dataset}}/raw_sample/g' sql/checks/$check.sql | bq query --use_legacy_sql=false --format=prettyjson
done
```

**Expected result:**
- `_LOADED.json` reports 100,000 rows.
- `02_layout`: `events` is partitioned by `time_stamp`, clustered by `collection`, and its REQUIRED columns are still REQUIRED.
- `03_events_by_day`: a single day, with 100,000 rows.
- `04_events_shapes`: listing events have `option_filter` set and an empty `option`. The NUMERIC columns live in `products`, so they are checked in step 5.

## 5. Full load

**1. Let the VM write to GCS.** Do this while the VM is stopped. It keeps every current scope and turns storage read-only into read-write.

```bash
gcloud compute instances set-service-account glamira-mongodb --zone ${REGION}-b \
  --service-account $(gcloud compute instances describe glamira-mongodb --zone ${REGION}-b \
      --format 'value(serviceAccounts[0].email)') \
  --scopes devstorage.read_write,logging.write,monitoring.write,service.management.readonly,servicecontrol,trace.append
gcloud compute instances start glamira-mongodb --zone ${REGION}-b
```

**2. Publish from the VM.** Get this branch onto the VM's checkout, either from a git bundle or by pulling it once it is pushed. Then run:

```bash
uv sync --frozen
uv run publish-export /data/mongodb/benchmark-work/export/full-2026-11-17-w3 --bucket <bucket> --dataset raw \
  2>&1 | tee publish_full.log
```

**3. Stop the VM** as soon as the publish has finished. The load runs in BigQuery and does not need the VM.

```bash
gcloud compute instances stop glamira-mongodb --zone ${REGION}-b
```

**4. Follow the load, then check the result.**

```bash
gcloud functions logs read bigquery-loader --region $REGION --limit 50
gcloud storage ls "gs://$BUCKET/raw/*/export_id=full-2026-11-17-w3/_LOADED.json"
for check in 01_tables 02_layout 03_events_by_day 04_events_shapes 05_numeric 06_join_coverage; do
  sed 's/{{dataset}}/raw/g' sql/checks/$check.sql | bq query --use_legacy_sql=false --format=prettyjson
done
```

**Expected result:**
- There are four `_LOADED.json` objects.
- The row counts are: events 41,432,473; ip_locations 3,239,627; products 19,557; product_option_values 923,294.
- In `03_events_by_day`, each day matches its chunk in the events `_manifest.json`, and 166 rows in total have a `time_stamp` on another day.

## 6. Repeat everything, expect no change

```bash
# Upload again: every object is skipped (uploaded 0).
uv run publish-export data/exports/sample-100k --bucket $BUCKET --prefix raw_sample --dataset raw_sample

# Load again past the marker: the job ID already exists (409), so the same job is reused and the count is unchanged.
uv run load-bigquery gs://$BUCKET/raw_sample/events/export_id=sample-100k/_load.json --ignore-marker
sed 's/{{dataset}}/raw_sample/g' sql/checks/01_tables.sql | bq query --use_legacy_sql=false
```

## 7. What to send back

1. The JSON printed by each `publish-export` run: uploaded and skipped counts, bytes, seconds.
2. The function log lines for each table (`loaded …`), and every `_LOADED.json`. They hold the job ID, the rows and the seconds.
3. The output of every check query.
4. Anything that failed, with its log line.

## Cost

| Item | Estimate |
| --- | --- |
| GCS | About 9.3 GB Standard: roughly $0.2 per month |
| BigQuery storage | About 30–40 GB logical: roughly $0.8 per month |
| Load jobs | Free |
| Check queries | A few GB, inside the free 1 TB per month |
| Function, Cloud Build, Artifact Registry | Within the free tiers; the image is about 0.2 GB |
| VM | Running only for the publish, about 10 minutes |
