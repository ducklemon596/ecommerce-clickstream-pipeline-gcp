# Decision record: file format of the raw layer (Parquet)

**Status:** accepted on 2026-11-22. This record replaces the earlier choice of Avro, which was in force from 2026-11-17 to 2026-11-22.
**Scope:** the files `export-raw` writes and BigQuery loads (see the [raw layer contract](../raw_layer_contract.md)).

## Context

The raw layer travels from MongoDB to BigQuery as files in GCS. The format must meet four requirements:

| Requirement | Why |
| --- | --- |
| **Typed** | A wrong type should stop the export at the row that caused it, not surface later in BigQuery |
| **Self-describing** | Its schema should travel with the file and match the BigQuery table exactly |
| **Splittable and compact** | BigQuery should read the files in parallel, and GCS storage and upload should stay small |
| **Deterministic** | The same rows must give the same bytes in any process. Resume and the BigQuery job ID rely on this ([retry and idempotency](export_retry_idempotency.md)) |

CSV was ruled out at once: it cannot hold the nested `option`, `option_filter` and `cart_products` fields.

## Evidence

The candidates were measured on 2026-11-22 on one week of real events: 2020-05-11 → 2020-05-17, 5,526,566 rows.
- Every format held the same decoded rows, and each writer was timed separately on the project VM.
- Each format was then loaded three times into a table built like production.

| | Avro, deflate | JSONL | JSONL, gzip | **Parquet, Snappy** |
| --- | ---: | ---: | ---: | ---: |
| Size | 1.23 GB | 7.30 GB | 1.05 GB | **0.59 GB** |
| Write time on the VM | 377 s | 243 s | 357 s | **102 s** |
| Writer peak memory | **57 MB** | 56 MB | 57 MB | 327 MB |
| BigQuery load time (median of 3) | 16.5 s | 8.4 s | 37.0 s | 8.8 s |
| BigQuery slot time (median) | 349 s | 549 s | 547 s | **243 s** |
| Rejects a type error when writing | yes | no | no | **yes** |
| Schema travels with the file | yes | no | no | **yes** |

All formats produced the same 3.23 GB table in BigQuery.

**What JSONL does with errors:**
- A quoted number written to an INT64 column was coerced silently.
- A text value in a TIMESTAMP column failed the whole load.
- Loaded without a schema, autodetect guessed `show_recommendation` as BOOLEAN, then failed at row 521,586 on the malformed value `"true; _gcl_au=…"`.

**What Avro and Parquet do:** both rejected both broken rows as they wrote them.

## Decision

**Parquet**, with Snappy compression, 50,000-row row groups, and parts of at most 1,000,000 rows.
- The Parquet (Arrow) schema is derived from the committed BigQuery schema (`schemas/raw/<table>.bq.json`), so the contract is a single file.
- BigQuery loads the parts with `PARQUET` and `enable_list_inference`, which maps lists to REPEATED fields, into tables created from that schema.

**Why not JSONL:**
- The files carry no types: errors appear only at load time, or not at all.
- Autodetect failed on this data.
- It takes 6× the storage uncompressed, and loads 4.2× slower than Parquet when gzipped, because gzip files cannot be split.

**Why Parquet replaced Avro.** Both are typed and self-describing. Parquet won on every efficiency measurement: half the size, 3.7× faster to write, 1.9× faster to load, 30% fewer slots. The arguments that first kept Avro did not hold:

| Argument for Avro | Finding |
| --- | --- |
| A Parquet file is valid only once its footer is written | The exporter already writes each part as `.tmp` and renames it after `fsync`, so footers change nothing for the commit protocol |
| Parquet buffers a row group in memory | About 330 MB per worker, or 1 GB for three workers on a 16 GB VM |
| Avro's logical types load natively | Parquet needs one load option, list inference. Tables are created from the contract, so no schema is inferred from the files |
| Determinism | It holds for Parquet: the footer contains only the writer version and the Arrow schema. One SHA-256 under four hash seeds, and a 2-worker export equals a single-process export byte for byte |

## Consequences

**Measured on the full data** ([export report](../reports/full_export.md), [load report](../reports/bigquery_load.md)):

| | Avro (2026-11-17/18) | Parquet (2026-11-22) |
| --- | ---: | ---: |
| Export, 3 workers | 52 min 46 s | **42 min 39 s** |
| Files | 9.30 GB | **4.69 GB** |
| Write stage of `events` (worker-seconds) | 3,261 s | **1,172 s** |
| `verify-export` | 53 s | **30 s** |
| `events` load job | 29.1 s | **14.3 s** |

- Every BigQuery check matched between the two loads: row counts, the 65 daily counts, the nested conversions, NUMERIC and join coverage.
- **Memory.** Writer memory rises to about 360 MB per process.
- **Library version.** The pyarrow version is part of the export identity, because byte identity depends on it.
- **Function dependencies.** The Cloud Function does not need pyarrow: BigQuery reads the files server side.
- **The bottleneck has moved.** Convert, meaning the contract checks and HMAC in Python, is now 62% of the export work, so a faster format would no longer help.
