# dbt project: `glamira`

dbt models on top of the BigQuery raw layer (`glamira_raw`), which the [warehouse load](../src/glamira_pipeline/warehouse/README.md) fills. dbt only reads `glamira_raw` and writes its own models to a separate dataset.

## Setup

```bash
uv sync --group dbt                                  # dbt-core and dbt-bigquery
gcloud auth application-default login                # credentials for BigQuery
cp dbt/profiles.yml.example dbt/profiles.yml         # git-ignored
export GCP_PROJECT=<project-id>
cd dbt && uv run --group dbt dbt debug --profiles-dir .
```

## Targets

| Target | Reads | Writes | Bytes billed cap |
| --- | --- | --- | --- |
| `sample` (default) | `glamira_raw_sample` | `glamira_dbt_sample` | 1 GB |
| `prod` | `glamira_raw` | `glamira_dbt` | 50 GB |

Every query is capped by `maximum_bytes_billed`: a query that would scan more fails instead of being billed. Develop on `sample`, and dry-run a new query (`bq query --dry_run`) before running it on `prod`.
