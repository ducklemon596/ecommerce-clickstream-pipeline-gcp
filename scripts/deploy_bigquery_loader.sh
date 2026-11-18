#!/usr/bin/env bash
# Deploy the bigquery-loader Cloud Function (gen2) with a GCS trigger on the export bucket.
#
# Usage:
#   scripts/deploy_bigquery_loader.sh --zip <file.zip>   build the source ZIP for a Console deploy (no gcloud call)
#   scripts/deploy_bigquery_loader.sh --dry-run          print the gcloud deploy command and the staged files
#   scripts/deploy_bigquery_loader.sh                    deploy with gcloud
# Deploying needs PROJECT, BUCKET and SERVICE_ACCOUNT (the loader's own service account email).
# Optional: REGION (default asia-southeast1), ALLOWED_DATASETS (default glamira_raw), FUNCTION (default bigquery-loader).
set -euo pipefail
REGION="${REGION:-asia-southeast1}"
ALLOWED_DATASETS="${ALLOWED_DATASETS:-glamira_raw}"
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

if [[ "${1:-}" == "--zip" ]]; then
  ZIP="$(realpath -m "${2:?usage: --zip <file.zip>}")"
  rm -f "$ZIP"
  (cd "$SOURCE" && python3 -m zipfile -c "$ZIP" main.py requirements.txt glamira_pipeline)
  python3 -m zipfile -l "$ZIP"
  exit 0
fi

: "${PROJECT:?set PROJECT}" "${BUCKET:?set BUCKET}" "${SERVICE_ACCOUNT:?set SERVICE_ACCOUNT}"
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
