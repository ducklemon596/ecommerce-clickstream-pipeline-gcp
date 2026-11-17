#!/usr/bin/env bash
# Deploy the bigquery-loader Cloud Function (gen2) with a GCS trigger on the export bucket.
#
# Required environment: PROJECT, BUCKET, SERVICE_ACCOUNT (the loader's own service account email).
# Optional: REGION (default asia-southeast1), ALLOWED_DATASETS (default raw), FUNCTION (default bigquery-loader).
# Usage: scripts/deploy_bigquery_loader.sh [--dry-run]
set -euo pipefail

: "${PROJECT:?set PROJECT}" "${BUCKET:?set BUCKET}" "${SERVICE_ACCOUNT:?set SERVICE_ACCOUNT}"
REGION="${REGION:-asia-southeast1}"
ALLOWED_DATASETS="${ALLOWED_DATASETS:-raw}"
FUNCTION="${FUNCTION:-bigquery-loader}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Stage only what the function imports: main.py, requirements.txt and the warehouse modules
# that depend on the Google Cloud clients alone (not publish/cli, which need the export package).
SOURCE="$(mktemp -d)"
trap 'rm -rf "$SOURCE"' EXIT
cp "$ROOT/functions/bigquery_loader/main.py" "$ROOT/functions/bigquery_loader/requirements.txt" "$SOURCE/"
mkdir -p "$SOURCE/glamira_pipeline/warehouse"
cp "$ROOT/src/glamira_pipeline/__init__.py" "$SOURCE/glamira_pipeline/"
for module in __init__ spec bigquery runner function; do
  cp "$ROOT/src/glamira_pipeline/warehouse/$module.py" "$SOURCE/glamira_pipeline/warehouse/"
done

COMMAND=(gcloud functions deploy "$FUNCTION"
  --project "$PROJECT" --region "$REGION" --gen2 --runtime python312
  --source "$SOURCE" --entry-point on_object_finalized
  --trigger-bucket "$BUCKET" --retry
  --service-account "$SERVICE_ACCOUNT" --trigger-service-account "$SERVICE_ACCOUNT"
  --timeout 540s --memory 512Mi --max-instances 5
  --set-env-vars "ALLOWED_DATASETS=$ALLOWED_DATASETS")

if [[ "${1:-}" == "--dry-run" ]]; then
  printf '%q ' "${COMMAND[@]}"; echo
  find "$SOURCE" -type f | sed "s|$SOURCE/||" | sort
else
  "${COMMAND[@]}"
fi
