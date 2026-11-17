# Full Avro export: measured run

**Run:** 2026-11-17, 08:05–10:12 UTC, export ID `full-2026-11-17`, commit `351a36a`.
**Command:** `uv run export-avro --table all --output-dir … --export-id full-2026-11-17` (defaults: 1,000,000 rows per file, verification on).
**Machine:** the project VM (e2-standard-4: 4 vCPU, 16 GB RAM), reading the local MongoDB 8.0 and writing to the data disk. The page cache was dropped before the run.

## Result

| Check | Result |
| --- | --- |
| Exit code | 0, all four tables complete |
| Rows | 45,614,951 in total, equal to the source counts of all four collections |
| Contract | 0 violations. The export stops at the first violation, so a complete run means every document fits |
| Retries | None needed: every chunk committed on attempt 1 |
| Verification | Every part re-read: SHA-256, writer schema and row count match the manifests |
| Output | 9.30 GB of deflate-compressed Avro in 71 parts |
| Peak memory | 112 MB resident |

## Timings

| Table | Rows | Avro size | Read | Convert | Write | Export total | Rows/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `events` | 41,432,473 | 9.13 GB, 65 parts | 836 s | 2,883 s | 2,367 s | **6,086 s (1 h 41 min)** | 6,808 |
| `ip_locations` | 3,239,627 | 145 MB, 4 parts | 16 s | 79 s | 40 s | 135 s | 23,945 |
| `product_option_values` | 923,294 | 20.7 MB, 1 part | 12 s | 37 s | 28 s | 77 s | 12,006 |
| `products` | 19,557 | 1.5 MB, 1 part | 1 s | 2 s | 2 s | 5 s | 4,074 |

How to read the stages:
- **Read** is the time spent waiting for the MongoDB cursor (`find(range).sort("_id")`).
- **Convert** applies the contract: type rules, HMAC hashing and the checks.
- **Write** is Avro encoding plus deflate compression and the file write.

The `events` time splits into convert 47%, write 39% and read 14%. The rest of the 2 h 06 min 33 s wall time is:

| Step | Time |
| --- | --- |
| Planning `events`: counting the 65 day ranges and writing the identity | about 30 s |
| **Verifying `events`**: re-hashing 9.13 GB and decoding all 41.4 M rows | **about 20 min** (09:48:12 → 10:07:59) |
| Verifying the three smaller tables | about 40 s together |

## Findings

- **Convert and write are the bottleneck, not MongoDB.**
  - Reading by `_id` range, which costs about 3× more on the server than a collection scan, is only 14% of the `events` time.
  - The export uses one of the four vCPUs. Chunks are independent, so running them in parallel processes is the lever if the time matters.
- **The VM is about 2.2× slower per row than the workstation.** The 100K sample ran at about 15,000 rows/s locally, against 6,808 rows/s on the VM.
  - The earlier estimate of 45–55 minutes extrapolated the workstation rate and was wrong.
  - Estimates for the VM should use the rates measured here.
- **Verification costs about 16% of the run.**
  - Almost all of it is decoding every row again, which repeats what the SHA-256 and the per-chunk counts already prove.
  - Counting rows from the Avro block headers instead would make it much cheaper; not changed yet.
- **Chunk times scale with rows.**
  - The largest day, 2020-05-17 with 893,200 rows, took 140 s (read 20, convert 66, write 55).
  - The smallest, 2020-06-04 with 205,032 rows, took 30 s.
  - A crash therefore costs at most about 2.5 minutes of redone work.

## Limitations

- **One run, not a benchmark series.** Timings vary with the VM's shared CPU and the disk cache.
- **No PII scan of the full output.** The check that decodes rows and looks for raw IPs, emails, device IDs and customer IDs was run on the 100K sample only.
- **Not loaded yet.** The files have not been uploaded to GCS or loaded into BigQuery.
- **Where the files are.** The output, 8.7 GiB on disk, stays on the VM data disk under `benchmark-work/export/full-2026-11-17`. Only this report is in the repository.
