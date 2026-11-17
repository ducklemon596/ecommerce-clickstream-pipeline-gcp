# Full Avro export: measured runs

All runs exported the four raw tables from `countly` on the project VM (e2-standard-4: 4 vCPU, 16 GB RAM), reading the local MongoDB 8.0 and writing to the data disk. The page cache was dropped before each run.

| Run | Date (UTC) | Commit | Command |
| --- | --- | --- | --- |
| **A**, one process, verification inside the export | 2026-11-17, 08:05–10:12 | `351a36a` | `export-avro --table all … --export-id full-2026-11-17` |
| **B**, three workers, separate verification | 2026-11-17, 11:04–11:58 | `a4ac6e2` | `export-avro --table all … --export-id full-2026-11-17-w3 --workers 3`, then `verify-export` |

## Result

| Check | Run A | Run B |
| --- | --- | --- |
| Exit code | 0 | 0, and 0 for `verify-export` |
| Rows | 45,614,951, equal to the source counts of all four collections | same |
| Contract violations | 0 (a violation stops the export) | 0 |
| Retries | none: every chunk committed on attempt 1 | none |
| Output | 9.30 GB in 71 parts | 9.30 GB in 71 parts. Each header differs by a few bytes (32 fewer per `events` part), because headers now embed the schema as declared (see the [decision record](../decisions/export_retry_idempotency.md)) |
| Peak memory | 112 MB | 102 MB in the parent; the workers were not measured |
| **Wall time** | **2 h 06 min 33 s** | **52 min 46 s** for the export, plus **53 s** for `verify-export` |

## Where the time goes

| Step | Run A | Run B |
| --- | --- | --- |
| Planning `events`: count the 65 day ranges, write the identity | about 30 s | about 17 s |
| Export `events` | 1 h 41 min (6,086 s) | **49 min (2,948 s)**, 3 workers |
| Verify `events` | about 20 min (re-hash and decode all 41.4 M rows) | not part of the export |
| `ip_locations` | 2 min 15 s | 2 min 16 s |
| `product_option_values` | 1 min 17 s | 1 min 16 s |
| `products` | 5 s | 5 s |
| Verify all tables | about 21 min in total | **53 s** with `verify-export` (inventory, sizes, SHA-256 of 9.30 GB, schemas; no decoding) |

The three small tables are one chunk each, so they run on one worker in both runs.

**`events` per stage**, summed over chunks. With three workers these are worker-seconds, not wall time.

| Stage | Run A | Run B |
| --- | --- | --- |
| Read from MongoDB | 836 s (14%) | 1,075 s (13%) |
| Convert (contract and HMAC) | 2,883 s (47%) | 4,254 s (50%) |
| Write (Avro encoding, deflate, file) | 2,367 s (39%) | 3,261 s (38%) |
| **Total** | 6,086 s; 6,808 rows/s | 8,590 worker-seconds; 4,823 rows/s per worker, **14,054 rows/s overall** |

## Findings

- **Three workers made `events` 2.06× faster, not 3×.**
  - Each worker processed rows about 30% slower than the single process did: 8,590 worker-seconds against 6,086 s.
  - The export ran at 262% CPU on a 4-vCPU VM shared with `mongod`, and e2 vCPUs are shared cores.
  - The earlier estimate of 35–40 min for `events` was optimistic; the measured time is 49 min.
- **Convert and write remain the bottleneck.** Reading from MongoDB is 13–14% of the work in both runs, so `_id`-range reads are not what limits the export.
- **Verification is now cheap.** Re-hashing 9.30 GB and checking the inventory takes 53 s. Decoding every row again took about 20 min. That decode is still available as `verify-export --full`, but was not timed on the full data.
- **The export is about 2.4× faster end to end:** 2 h 06 min → 53 min 39 s, including verification.
- **Output identity.**
  - Run B's `content_sha256` differs from run A's because the header fix changed every file; the table row counts are equal.
  - The parallel and single-process runs were compared for byte identity in the integration tests, not on the full data.

## Limitations

- **One run per configuration, not a benchmark series.** Timings vary with the shared CPU and the disk cache.
- **Worker count not swept.** Only 1 and 3 workers were measured; 2 or 4 were not.
- **No PII scan of the full output.** The check that decodes rows and looks for raw IPs, emails, device IDs and customer IDs was run on the 100K sample only.
- **Not loaded yet.** The files have not been uploaded to GCS or loaded into BigQuery.
- **Where the files are.** Both outputs stay on the VM data disk under `benchmark-work/export/`, about 8.7 GiB each. Only this report is in the repository.
