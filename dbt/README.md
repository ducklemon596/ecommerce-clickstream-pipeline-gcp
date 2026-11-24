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

## Profiling the raw layer

`models/profiling/` profiles every raw table with [dbt_profiler](https://hub.getdbt.com/data-mie/dbt_profiler/latest/) and writes one table per source to `<target dataset>_profiling`:
- `profile_<table>`: per column, the not-null and distinct proportions, distinct count, uniqueness, and min/max/avg/median for numbers and times;
- `profile_events_arrays`: the ARRAY columns `option` and `cart_products`, which dbt_profiler cannot profile: array lengths, then null and distinct counts per element field.

```bash
cd dbt
uv run --group dbt dbt deps --profiles-dir .
uv run --group dbt dbt build -s profiling --profiles-dir .                 # sample: events only
uv run --group dbt dbt build -s profiling --target prod --profiles-dir .   # all four tables
```

The profiles also appear in `dbt docs`: each source's description ends with a docs block from `models/profiling/docs/<table>.md`. These files are a committed snapshot of the prod profile. Regenerate them after rebuilding the profiles; this reads only the small profile tables:

```bash
for t in events ip_locations products product_option_values; do
  uv run --group dbt dbt -q run-operation print_profile_doc --args "{table: $t}" --target prod --profiles-dir . > models/profiling/docs/$t.md
done
uv run --group dbt dbt docs generate --target prod --profiles-dir . && uv run --group dbt dbt docs serve --profiles-dir .
```
