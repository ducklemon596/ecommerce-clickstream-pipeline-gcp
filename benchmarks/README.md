# Why the raw layer ships as Avro: format benchmark

The raw layer moves from MongoDB to BigQuery as files in GCS (see the [raw layer contract](../docs/raw_layer_contract.md)). This page measures the candidate file formats on the real events data and explains why **Avro (deflate)** was chosen over newline-delimited JSON (JSONL), the format BigQuery tutorials usually start from. Parquet is measured too and discussed briefly; CSV is ruled out at once because it cannot represent the nested `option`, `option_filter` and `cart_products` fields.

The comparison covers three questions:

1. **Storage:** how many bytes the same rows take in GCS.
2. **Time:** how long it takes to write the files on the VM, and to load them into BigQuery.
3. **Schema and contract:** where a type error is caught, and what BigQuery does when the files must speak for themselves.

> **Status:** the local run on the 100K sample is complete (below). The VM and BigQuery run on one week of events is pending; its results will replace the "pending" cells.

## 1. Method

Every format holds **the same rows**. `benchmarks/file_formats.py convert` decodes the verified Avro export once and hands each decoded row to every writer in turn. Each writer's time is measured separately, so the shared decoding is not charged to any format.

| Format | Writer | Notes |
| --- | --- | --- |
| `avro_deflate` | fastavro, deflate | The production format |
| `avro_null` | fastavro, no compression | Separates the format from its compression |
| `jsonl` | `json.dumps` per row | TIMESTAMP as `YYYY-MM-DD HH:MM:SS.ffffff UTC`, NUMERIC as a string |
| `jsonl_gzip` | same, gzip level 6 | The usual way JSONL is shipped |
| `parquet` | pyarrow, Snappy, 50,000-row row groups | Schema derived from the BigQuery contract |

**Loads** (`load`) go into tables created exactly like production: contract schema, DAY partitions on `time_stamp`, clustering by `collection`, `WRITE_TRUNCATE_DATA`. Each format is loaded 3 times. The reported time is the median server time (job start → end) and the median slot time, both taken from the job statistics.

**Contract checks** (`contract`) do two things:
- Write two realistic breaks with each writer: a quoted number in an INT64 column, and text in a TIMESTAMP column.
- Load the files twice: with the contract schema, and with no schema at all (Avro's embedded schema against JSONL autodetect).

## 2. Results

### 2.1 Storage and write time

**Local, 100K-event sample** (2020-06-04, laptop, Python 3.10, fastavro 1.12.2, pyarrow 25.0.1):

| Format | Size | vs Avro deflate | Write time | Rows/s | Peak memory, writer alone |
| --- | ---: | ---: | ---: | ---: | ---: |
| `avro_deflate` | 22.4 MB | 1.00× | 2.8 s | 35,271 | 58 MB |
| `avro_null` | 59.3 MB | 2.65× | 1.8 s | 55,454 | — |
| `jsonl` | 131.1 MB | 5.86× | 2.0 s | 48,803 | — |
| `jsonl_gzip` | 19.1 MB | 0.85× | 3.2 s | 31,716 | — |
| `parquet` | 11.0 MB | 0.49× | 0.9 s | 114,606 | 325 MB |

**VM, one week of events** (2020-05-11 → 2020-05-17, 5,526,566 rows): *pending.*

### 2.2 Load time into BigQuery

*Pending: one week of events, 3 loads per format.*

### 2.3 Schema and contract

**Where a broken row is caught** (measured locally):

| Break | Avro | JSONL |
| --- | --- | --- |
| `"7"` (a string) in INT64 `recommendation_clicked_position` | **Rejected when writing** (`ValidationError`) | Written; the problem travels on |
| `"not-a-time"` in TIMESTAMP `time_stamp` | **Rejected when writing** | Written; the problem travels on |

**What BigQuery does with those JSONL rows, and without a contract:** *pending* (the BigQuery part of `contract`).

## 3. Findings

### Storage efficiency

- **The JSON text is the cost, not JSON itself.** Uncompressed, JSONL takes 5.9× the bytes of Avro deflate and 2.2× those of uncompressed Avro. Every row repeats every key name, and numbers and timestamps travel as text. Avro writes the schema once per file and encodes values in binary.
- **Gzip closes the gap, but at a price.** `jsonl_gzip` is 15% smaller than Avro deflate, because gzip removes the repeated keys. A gzip file, however, cannot be split. BigQuery reads each one with a single worker, and it caps compressed JSON files at 4 GB, while Avro's deflate is applied per block and stays splittable. The load measurement shows what that costs.
- **Parquet is the most compact**, at half of Avro deflate, as expected of a columnar format on a table with 34 mostly sparse columns.

### Write time

- On already-decoded rows, **Parquet wrote fastest** in this measurement. pyarrow converts a whole 50,000-row batch in C++, while fastavro and `json.dumps` work row by row in Python. The common rule that "columnar formats are slow to write" does not hold here as a matter of CPU.
- What Parquet costs on the write side is **memory and granularity**. A row group must be held in memory before it is written: 325 MB peak against 58 MB for streaming Avro. A file is only valid once its footer is written. The exporter's design relies on the opposite properties: it streams rows straight from a MongoDB cursor, bounds memory per worker, and commits parts that are complete the moment they are closed ([retry and idempotency](../docs/decisions/export_retry_idempotency.md)).
- For the raw layer, writing is a small share of the export. Convert, meaning the contract checks and HMAC, takes about half of the work ([export report](../docs/reports/full_export_avro.md)), whatever format follows it.

### Loading time

*Pending the BigQuery run.* Avro files are read in parallel by block, even when compressed. Gzip JSON is read whole, file by file. BigQuery stores every loaded table in its own columnar format (Capacitor) whatever the input, so Parquet's columnar layout brings no advantage after the load.

### Schema and contract

- **An Avro file carries its schema**, and the writer validates every row against it. A type error stops the export at the row that caused it: in our exporter that means at the MongoDB document, with its `_id` and field path in the message. A JSONL file carries no types at all. The same error is only discovered when BigQuery loads the file, after the export and the upload have finished. At that point it is either a failed job or, worse, a value BigQuery coerces quietly (pending: what the quoted number becomes).
- **Without a contract, JSONL depends on guessing.** Autodetect samples rows and infers types. Avro's embedded schema rebuilds the contract exactly (pending: the list of differences autodetect produces on this data).
- **One schema, generated twice.** The project declares each table once in [`tables.py`](../src/glamira_pipeline/export/tables.py). The Avro schema written into every file and the BigQuery table schema are both generated from that declaration, so the files and the table cannot drift apart. JSONL would leave only the BigQuery side typed.

## 4. Decision

*To be finalised with the BigQuery results.* On the evidence so far, Avro wins on the properties the raw layer depends on:
- a typed contract checked when each file is written;
- a self-describing file;
- streaming writes with bounded memory;
- splittable compressed files.

It does so at a storage cost that is small in absolute terms (22 MB per 100K events, about 9.3 GB for all 45.6 M rows). Parquet would be the better choice for files that are read for analysis directly from GCS. Those files are never read that way here: BigQuery is the reader.

## 5. Reproduce

**On the VM.** Start it, check out this branch, and mount the export as for the export run:

```bash
cd ~/xp/glamira-pipeline && uv sync --frozen --group bench
mkdir -p ~/xp/out && sudo mount --bind /data/mongodb/benchmark-work ~/xp/out
E=~/xp/out/export/full-2026-11-17-w3/events
B=~/xp/out/bench-formats

# 1. Write every format from the same rows (about 13 GB on the data disk).
/usr/bin/time -v uv run --group bench python benchmarks/file_formats.py convert $E --out $B \
  --chunks 2020-05-11 2020-05-12 2020-05-13 2020-05-14 2020-05-15 2020-05-16 2020-05-17 \
  2> $B.convert.log

# 2. Peak memory of each writer alone, on one day.
for f in avro_deflate jsonl jsonl_gzip parquet; do
  /usr/bin/time -v uv run --group bench python benchmarks/file_formats.py convert $E --out /tmp/mem-$f \
    --chunks 2020-05-17 --formats $f 2>&1 | grep -E "Maximum resident" | sed "s/^/$f /"
  rm -rf /tmp/mem-$f
done | tee $B.memory.txt

# 3. Upload (the VM's storage scope must be read-write).
uv run --group bench python benchmarks/file_formats.py upload $B --bucket glamira-raw-datalake-asia-southeast1

sudo umount ~/xp/out   # then stop the VM
```

**On a workstation**, with Application Default Credentials:

```bash
bq mk --location asia-southeast1 --dataset --description "Format benchmark (temporary)" <project>:glamira_bench
uv run --group bench python benchmarks/file_formats.py load --bucket glamira-raw-datalake-asia-southeast1 \
  --results benchmarks/results/load_results.json
uv run --group bench python benchmarks/file_formats.py contract \
  data/exports/sample-100k/events/chunk=2020-06-04/part-00000.avro \
  --bucket glamira-raw-datalake-asia-southeast1 --results benchmarks/results/contract_results.json
```

Copy `convert_results.json`, `upload_results.json` and the memory file from the VM into `benchmarks/results/`.

**Cost.**
- Writing and loading: load jobs are free.
- Storage while the benchmark data is kept: about 13 GB in GCS (≈ $0.25 per month) and seven BigQuery tables of about 3.3 GB logical each (≈ $0.45 per month).
- Remove `gs://…/bench/` and `glamira_bench` once the results are recorded.
