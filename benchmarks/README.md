# Why the raw layer ships as Avro: format benchmark

The raw layer reaches BigQuery as files in GCS (see the [raw layer contract](../docs/raw_layer_contract.md)). This page measures the candidate file formats on one week of the real events: 5,526,566 rows, 1.23 GB as Avro. It shows why **Avro (deflate)** was chosen over newline-delimited JSON (JSONL), the format most BigQuery pipelines start from.

Parquet was measured too, and it turns out to be the strongest alternative, so it gets a short section. CSV is ruled out at once: it cannot represent the nested `option`, `option_filter` and `cart_products` fields.

**Observed:** 2026-11-22.
- **Writes:** on the project VM (e2-standard-4, 4 vCPU, one Python process, fastavro 1.12.2, pyarrow 25.0.1).
- **Loads:** into BigQuery in `asia-southeast1`.

## Summary

| | Avro deflate | Avro, uncompressed | JSONL | JSONL gzip | Parquet (Snappy) |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Size in GCS** | 1.23 GB | 3.32 GB | 7.30 GB | 1.05 GB | **0.59 GB** |
| Size vs Avro deflate | 1.00× | 2.70× | **5.94×** | 0.86× | 0.48× |
| **Write time on the VM** | 377 s | 236 s | 243 s | 357 s | **102 s** |
| Peak memory of the writer | 57 MB | 56 MB | 56 MB | 57 MB | **327 MB** |
| Upload to GCS | 4.8 s | 10.9 s | 23.5 s | 4.2 s | 4.2 s |
| **BigQuery load time** (median of 3) | 16.5 s | 10.8 s | 8.4 s | **37.0 s** | 8.8 s |
| BigQuery slot time (median) | 349 s | 328 s | **549 s** | 547 s | 243 s |
| Rejects a type error at write | **yes** | **yes** | no | no | **yes** |
| Schema travels with the file | **yes** | **yes** | no | no | **yes** |

All five formats produced the same table: 5,526,566 rows and 3.23 GB in BigQuery. BigQuery stores data in its own columnar format whatever the input.

**Against JSONL, Avro wins on every axis that matters for a raw layer.**
- Plain JSONL takes 6× the storage, needs 1.6× the BigQuery compute to load, carries no types, and its autodetected schema broke on this data.
- Gzip fixes the size but makes the load 2.2× slower than Avro.

**Against Parquet, Avro loses on efficiency** but fits the exporter's streaming, commit-per-part design (section 4).

## 1. Method

Every format holds **the same rows**. [`file_formats.py`](file_formats.py) `convert` decodes the verified Avro export once and passes each decoded row to every writer in turn. It times each writer separately, so the shared decoding (223 s) is charged to no format.

**Check that the rows are the same:** the Avro deflate copy written by the benchmark has exactly the export's size, 1,228,682,549 bytes.

| Format | Writer | Notes |
| --- | --- | --- |
| `avro_deflate` | fastavro, deflate | The production format |
| `avro_null` | fastavro, no compression | Separates the format from its compression |
| `jsonl` | `json.dumps` per row | TIMESTAMP as `YYYY-MM-DD HH:MM:SS.ffffff UTC`, NUMERIC as a string |
| `jsonl_gzip` | same, gzip level 6 | How JSONL is usually shipped |
| `parquet` | pyarrow, Snappy, 50,000-row row groups | Schema derived from the BigQuery contract |

- **Data:** the 7 daily chunks from 2020-05-11 to 2020-05-17 of the full export, giving 7 files per format.
- **Peak memory:** measured with `/usr/bin/time -v` on one day per format, one writer at a time.
- **Loads:** each format was loaded 3 times into a table created exactly as in production: the contract schema, DAY partitions on `time_stamp`, clustering by `collection`, and `WRITE_TRUNCATE_DATA`. The reported time is the median *server* time (job start → end) from the job statistics, with the slot time beside it.
- **Raw numbers:** [`results/`](results/).

## 2. Storage efficiency

| Format | Bytes | Per row | vs Avro deflate | Full 45.6 M rows (scaled) |
| --- | ---: | ---: | ---: | ---: |
| Avro deflate | 1,228,682,549 | 222 B | 1.00× | 9.3 GB (measured) |
| Avro, uncompressed | 3,320,133,889 | 601 B | 2.70× | ~25 GB |
| JSONL | 7,299,814,656 | 1,321 B | 5.94× | ~55 GB |
| JSONL gzip | 1,054,734,241 | 191 B | 0.86× | ~8 GB |
| Parquet | 591,451,725 | 107 B | 0.48× | ~4.5 GB |

- **What makes JSONL big is the text, not JSON.** Every JSONL row repeats all 34 key names, and numbers and timestamps travel as text. Avro writes the schema once per file and encodes values in binary, so even uncompressed Avro is 2.2× smaller than JSONL.
- **Gzip removes the repetition but costs the load.** `jsonl_gzip` is 14% smaller than Avro deflate. A gzip file cannot be split, though, so BigQuery reads each one with a single worker (section 3). Avro compresses each block separately, so it stays splittable.
- **Parquet is the most compact**, at half the size of Avro deflate. This is what a columnar layout gives on a table where most of the 34 columns are sparse and repetitive per event type.

At this volume, storage is cheap in every format: about $0.20 per month for Avro and $1.10 for plain JSONL, across the full dataset. Byte count matters more for upload and read time than for the bill.

## 3. Time: writing on the VM, loading into BigQuery

### Write time

| Format | Write time | Rows/s | Upload | Peak memory |
| --- | ---: | ---: | ---: | ---: |
| Avro deflate | 377.2 s | 14,651 | 4.8 s | 57 MB |
| Avro, uncompressed | 236.0 s | 23,421 | 10.9 s | 56 MB |
| JSONL | 242.7 s | 22,767 | 23.5 s | 56 MB |
| JSONL gzip | 357.0 s | 15,480 | 4.2 s | 57 MB |
| Parquet | 101.5 s | 54,426 | 4.2 s | 327 MB |

- **Compression is the cost in Avro deflate's write time, not Avro itself.** Uncompressed Avro writes as fast as JSONL. Deflate adds 141 s and gzip 114 s on this machine.
- **Parquet wrote 3.7× faster than Avro deflate.** pyarrow converts a whole batch of 50,000 rows in C++, while fastavro and `json.dumps` work row by row through Python. The common rule that columnar formats are slow to write does not hold here as a matter of CPU.
- **What Parquet costs on the write side is memory and granularity.** A whole row group must be built in memory before it is written: 327 MB here, against 57 MB for any of the streaming writers. A Parquet file is only readable once its footer is written.
- **Upload time follows size.** The network moved about 300 MB/s within the region, so only plain JSONL's 7.3 GB is noticeable, at 23.5 s.

### Load time

| Format | Load runs (s) | Median | Slot time, median | Input files |
| --- | --- | ---: | ---: | ---: |
| Avro deflate | 17.6, 16.5, 14.4 | 16.5 s | 349 s | 7 |
| Avro, uncompressed | 11.1, 10.8, 9.8 | 10.8 s | 328 s | 7 |
| JSONL | 8.4, 8.4, 8.4 | 8.4 s | 549 s | 7 |
| JSONL gzip | 37.0, 42.6, 35.2 | 37.0 s | 547 s | 7 |
| Parquet | 9.3, 8.4, 8.8 | 8.8 s | 243 s | 7 |

- **Gzipped JSONL is the slow one: 2.2× slower than Avro deflate and 4.4× slower than plain JSONL.** BigQuery cannot split a gzip stream, so 7 files mean at most 7 readers. The other formats are split into many parallel reads.
- **JSONL is cheap in elapsed time but expensive in work.** Plain JSONL finished fastest because BigQuery spread its 7.3 GB over many workers. Parsing text took 1.6× the slot time of Avro, and 2.3× that of Parquet.
- **Avro's compression is what slows its load.** Uncompressed Avro loads 35% faster than deflate for the same slot time, so decompression is what makes the deflate load longer. Both are still far from gzip JSONL.
- **Load jobs are free on BigQuery's shared slot pool.** Slot time therefore measures how much shared capacity a load takes, not cost. In seconds per load, every splittable format here is fast.

## 4. Schema and contract

This is where the formats differ most.

**Where a broken row is caught.** Two realistic breaks were injected into a real row:

| Break | Avro | Parquet | JSONL |
| --- | --- | --- | --- |
| `"7"`, a string, in INT64 `recommendation_clicked_position` | Rejected when writing (`ValidationError`) | Rejected when writing (`ArrowInvalid`) | Written. **BigQuery then stores it as 7 without a warning** |
| `"not-a-time"` in TIMESTAMP `time_stamp` | Rejected when writing | Rejected when writing (`ArrowTypeError`) | Written. **The whole load fails in BigQuery** (`Could not parse 'not-a-time' as a timestamp`) |

A typed format stops at the row that broke the contract, on the machine that produced it. JSONL carries the error through the export and the upload, and then either fails the load or is coerced in silence. Coercion is the worse of the two, because nothing reports it.

**Loading with no schema given, so the files must describe themselves:**

| Format | Result |
| --- | --- |
| Avro | Loaded; the table schema built from the file has **0 differences** from the contract, including nesting and REQUIRED modes |
| JSONL with autodetect | **Failed.** Autodetect inferred `show_recommendation` as BOOLEAN from its `"true"` / `"false"` values. At row 521,586 it met `"true; _gcl_au=1.1.1490163851.1589180844"`, a malformed value the [data quality report](../docs/reports/data_quality_report.md) had already found, and gave up |

Avro is self-describing. JSONL leaves BigQuery to guess from a sample, and the guess breaks on the first value the sample did not foresee. With JSONL, the contract would live only in the BigQuery table definition, never in the files.

**One declaration, two outputs.** Each table is declared once in [`tables.py`](../src/glamira_pipeline/export/tables.py). The Avro schema written into every file and the BigQuery table schema are both generated from it, so the files and the table cannot drift apart. That is the point of a contract-first raw layer, and it needs a typed, self-describing file format.

## 5. Decision

**Avro over JSONL.** JSONL loses on every measurement this pipeline cares about:
- it has no types in the files;
- autodetect failed on this data;
- a quoted number is coerced silently;
- type errors appear only at load time;
- it takes 6× the storage uncompressed;
- it loads 2.2× slower when gzipped.

**Avro over Parquet.** This is a trade-off, not a sweep. Parquet measured better on size (0.48×), write CPU (3.7× faster), load time and slot time, and it also rejects type errors at write. Avro is kept for these reasons:

- **It fits the exporter.**
  - The exporter streams documents from a MongoDB cursor and writes and commits part files of up to 1 M rows.
  - Every part is complete and valid the moment it is closed. That property is what the resume protocol relies on ([retry and idempotency](../docs/decisions/export_retry_idempotency.md)).
  - Avro writes row by row in constant memory: 57 MB per process.
  - Parquet needs a row group in memory (327 MB per process at 50,000 rows), and each file is readable only after its footer.
- **BigQuery reads it natively.**
  - Avro logical types map directly to TIMESTAMP and NUMERIC.
  - Parquet's nested lists need `enable_list_inference` to load as REPEATED fields.
- **The gap is small at this scale.** The full export writes for about 50 min across 3 workers, and convert, meaning the contract checks and HMAC, takes half of that whatever the format. The full load takes 29 s, and 9.3 GB of storage costs about $0.20 per month.

**When to revisit:** if export time or storage become a real constraint. Parquet is the measured alternative: it would cut write time and storage by about half, at the price of buffering a row group per worker.

## 6. Reproduce

**On the VM.** Check out this branch and mount the export as for the export run:

```bash
cd ~/xp/glamira-pipeline && uv sync --frozen --group bench
mkdir -p ~/xp/out && sudo mount --bind /data/mongodb/benchmark-work ~/xp/out
sudo install -d -o $(id -un) -g $(id -gn) -m 700 ~/xp/out/bench
E=~/xp/out/export/full-2026-11-17-w3/events; B=~/xp/out/bench/formats

# 1. Write every format from the same rows (about 13.5 GB, 26 min).
.venv/bin/python benchmarks/file_formats.py convert $E --out $B \
  --chunks 2020-05-11 2020-05-12 2020-05-13 2020-05-14 2020-05-15 2020-05-16 2020-05-17

# 2. Peak memory of each writer alone, on one day.
for f in avro_deflate avro_null jsonl jsonl_gzip parquet; do
  /usr/bin/time -v .venv/bin/python benchmarks/file_formats.py convert $E --out ~/xp/out/bench/mem-$f \
    --chunks 2020-05-17 --formats $f 2>&1 >/dev/null | grep "Maximum resident"; rm -rf ~/xp/out/bench/mem-$f
done

# 3. Upload. The VM's storage scope must be read-write.
.venv/bin/python benchmarks/file_formats.py upload $B --bucket <bucket> --prefix bench/formats
sudo umount ~/xp/out   # then stop the VM
```

**On a workstation**, with Application Default Credentials:

```bash
bq mk --location asia-southeast1 --dataset <project>:glamira_bench
uv run --group bench python benchmarks/file_formats.py load --bucket <bucket> --results benchmarks/results/load_results.json
uv run --group bench python benchmarks/file_formats.py contract \
  data/exports/sample-100k/events/chunk=2020-06-04/part-00000.avro \
  --bucket <bucket> --results benchmarks/results/contract_results.json
```

**Limits of this measurement:**
- One week of events, and one run of each write. Loads were run 3 times each.
- One Python process on a shared-core VM.
- Load times depend on BigQuery's shared slot pool at the moment of the run.
- The benchmark data lives under `gs://<bucket>/bench/` and in dataset `glamira_bench`, and should be removed once these results are kept.
