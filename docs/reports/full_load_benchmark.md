# Full load of `summary.bson`: what was measured and why the loader looks the way it does

**Observed:** 2026-11-14 on the project VM. Every measurement used the **full** `summary.bson` member: **41,432,473 documents**, **33,530,129,089 bytes**.
**Outcome:** the production loader (`load-summary`) loads everything in **8 min 41 s**. It is resumable and idempotent, and the reconciliation check (`reconcile-summary`) proves the result: same total, same count for each of the 27 event types, and 1,000 / 1,000 sampled documents byte-identical.

How to run the loader is described in the [operations guide](../../src/glamira_pipeline/load/README.md). This report explains how the design was reached.

## 1. The problem

The source is one mongodump BSON file, `dump/countly/summary.bson`, inside a 5.5 GB `.tar.gz`. It has to end up as a MongoDB collection. The loader has to do three things at once:

| Requirement | Why it matters |
| --- | --- |
| **Fast** | A load that takes hours blocks every later step and keeps the VM running, which costs money |
| **Safe to retry** | A crash, an SSH drop or a reboot must not create duplicate documents or silently lose documents |
| **Verifiable** | "The process exited with 0" is not proof that the data is complete and unchanged |

Two existing tools each covered only part of this:

- **`mongorestore`** restored everything in about 15 minutes with 0 failures. It keeps no checkpoint of its own, though, and it says nothing about whether every document arrived intact.
- **The first in-house loader** cut the dump into 100,000-document chunks, gzipped each chunk, then decoded each document and upserted it one by one. It could resume, but a full load took about **2 hours**.

A second design was also tried and is now archived under the git tag `archive/chunked-restore`:

- It cut the dump into 256 MiB chunks and gzipped them with SHA-256 checksums.
- Each chunk went through `mongorestore --gzip` into a staging collection.
- Three `$lookup` passes followed (classify, merge, verify) before a `$merge` into the target.
- It was only ever tested on 2,000 synthetic documents. Extrapolated, it needed about 45 min to chunk and about 4 h to load, plus disk space for the chunks and the staging collections.

Both designs added work around the insert. Rather than guess which part was slow, each part was measured on its own.

## 2. Environment

| Item | Value |
| --- | --- |
| VM | `e2-standard-4`: 4 vCPU, 15 GiB RAM, no swap |
| Disks | Boot disk: 30 GB `pd-balanced`, holding a copy of the archive. Data disk: 80 GB `pd-balanced`, the MongoDB `dbPath` |
| Software | MongoDB 8.0.34, mongorestore 100.20.0, Python 3.12.3, pymongo 4.18.3, pigz (Ubuntu 24.04 package) |
| Source | `glamira_ubl_oct2019_nov2019.tar.gz`, 5,495,914,358 bytes, SHA-256 `30beabd5…a89a53aa8` |
| Isolation | Separate benchmark databases with one new collection per run, all dropped afterwards. `countly.summary` was not touched (still 41,432,473 documents) |
| Method | Runs one at a time. Before each run the page cache was dropped, `vmstat 5` was recorded, and `mongod` CPU was read from `/proc` before and after |

The boot disk had 11 GB free, and the data disk is reserved for `dbPath`. **The 33.5 GB BSON could not be extracted to a file.** Every measurement therefore streams the member out of the `.tar.gz`, which is also what the final loader does.

## 3. Measuring each component

### 3.1 Getting bytes and documents out of the archive (no MongoDB)

Every row reads the whole archive. Rows 2 and 3 only decompress: the output goes to `/dev/null` and is never split into documents. Rows 4 to 6 decompress with `pigz` **and** split into documents.

| # | Stage | Wall time | Throughput | CPU (user+sys) |
| --- | --- | ---: | ---: | ---: |
| 1 | Read the 5.5 GB `.tar.gz` from disk | 31 s | 180 MB/s | 5 s |
| 2 | Decompress with Python `tarfile` (`r\|gz`), no split | 174 s | 193 MB/s | 174 s |
| 3 | Decompress with `tar` + `pigz`, no split | 130 s | 259 MB/s | 265 s |
| 4 | `pigz` + cut into documents by the 4-byte length prefix | 254 s | 163K docs/s | 417 s |
| 5 | Row 4 + `bson.decode` of every document | 463 s | 90K docs/s | 622 s |
| 6 | Row 4 + `gzip -6` of every 100K-doc batch (what the first loader did) | 961 s | 43K docs/s | 1,104 s |

- **Decompression is cheap.** `pigz` is about 25 % faster than Python's gzip: it inflates in one thread and does reading, writing and checksums in others.
- **Splitting is cheap if documents are not decoded.** A BSON document starts with its own length, so cutting a stream into documents needs no parsing. That costs about 2 minutes (row 4 − row 3).
- **Decoding and re-compressing are expensive.** Decoding every document doubles the time (row 5). Re-gzipping batches adds 12 minutes (row 6 − row 4).

### 3.2 Writing to MongoDB

Each row below includes `pigz` decompression and splitting.

| Stage | Wall time | Docs/s | CPU busy |
| --- | ---: | ---: | ---: |
| `mongorestore`, 1 insertion worker | 12 min 7 s | 56,977 | 89 % |
| `mongorestore`, 4 insertion workers | 12 min 25 s | 55,598 | 89 % |
| `insert_many(RawBSONDocument, ordered=False)`, 1 thread | 12 min 6 s | 57,085 | 52 % |
| `insert_many(RawBSONDocument, ordered=False)`, **4 threads** | **8 min 49 s** | **78,379** | 69 % |
| `insert_many(RawBSONDocument, ordered=False)`, 8 threads | 8 min 59 s | 76,911 | 69 % |
| Decode + `ReplaceOne(upsert=True)`, 1 thread (first loader) | 56 min 57 s | 12,126 | 39 % |

- **Every row stored all 41,432,473 documents.**
- **Disk was never the limit.** I/O wait (`wa`) stayed at 1–2 %.
- **Throughput stayed flat.** It did not drop as the `_id` index grew.

## 4. What the measurements decided

| Option | Verdict | Reason |
| --- | --- | --- |
| Upsert each document | Rejected | 4.7× slower than a plain 4-thread insert. Retry safety does not need it: inserting the same source `_id` twice fails with a duplicate-key error, which is just as safe |
| Re-gzip chunks, then load them | Rejected | 12 extra minutes and extra disk, only to recompress data that is already compressed in the archive |
| Staging collections + `$lookup`/`$merge` | Rejected | Every document is written twice and joined three times. A duplicate-key error gives the same guarantee for free |
| Extract the `.bson` to disk first | Not possible, and not useful | No disk space outside `dbPath`. It would save at most the 2 minutes of decompression |
| `mongorestore` | Rejected as the main path | CPU-bound at 89 %, and more workers did not help. No checkpoint and no verification |
| **Raw-BSON `insert_many`, 4 threads** | **Chosen** | Fastest measured option. Documents are never decoded, and it can be made resumable and verifiable cheaply |

**Why raw-BSON inserts beat `mongorestore` here:**
- **No decoding.** `RawBSONDocument` hands the original bytes to the driver unchanged.
- **CPU headroom.** About 30 % of the CPU stayed free for `mongod`.
- **Server-side limit at 4 threads.** Going from 4 to 8 threads gained nothing.

## 5. The chosen design

```text
.tar.gz ──tar+pigz──▶ bytes ──length prefix──▶ batches of 1,000 docs ──▶ 4 insert threads ──▶ MongoDB
                                                       │                          │
                                                       └──── watermark ◀── batch done
                                                                │
                                                      load_runs (every 30 s, journaled)
```

| Safety need | Mechanism |
| --- | --- |
| No duplicates on retry | The source `_id` is the key. Inserts are `ordered=False`, so a batch with some existing documents still inserts the rest. Error 11000 is counted as `duplicates`; any other error stops the load |
| Resume without rescanning MongoDB | Batch boundaries are deterministic: the same archive and the same limits give the same batches. A **watermark** (the last batch before which every batch is done) is saved every 30 s. A restart skips those batches without sending them |
| Workers finishing out of order | The watermark only moves over a contiguous run of finished batches (min-heap). Batches finished after the watermark are re-sent and come back as duplicates |
| Wrong source or wrong target | A run's identity is the archive SHA-256, the member, the target and the batch limits. Resume also requires the same collection UUID. A non-empty target without a matching run is refused |
| Two loaders at once | A heartbeat lock (120 s). A run whose heartbeat has expired is marked `abandoned` |
| Ctrl+C, SSH drop | SIGINT, SIGTERM and SIGHUP finish the batches in flight, save the checkpoint and exit with code 130 |
| Malformed events | A lenient `$jsonSchema` validator requires `_id`, a string `collection` and a numeric `time_stamp`. With `validationAction: warn`, violations are logged by `mongod` but no source document is rejected |
| Proof of completeness | At the end, `docs_seen = skipped + inserted + duplicates` and the target count equals the source count. A separate `reconcile-summary` compares totals, the count per event type, and 1,000 sampled documents byte for byte |

## 6. Results of the production loader

Four runs, all into the disposable database `glamira_load_bench`, at git `72073d2`.

| Run | What it tests | Wall time | Result |
| --- | --- | ---: | --- |
| R1 | Full load, validator `warn` | **8 min 41 s** | 41,432,473 inserted, 0 duplicates, `completed` |
| R2 | Full load, validator `off` | 8 min 48 s | 41,432,473 inserted, `completed` |
| R3a → R3b | `SIGKILL` 270 s into a load, wait out the heartbeat, rerun the same command | 8 min 59 s for the resume | 15,045,000 skipped + 24,131,473 inserted + 2,256,000 duplicates = 41,432,473, `completed` |
| R3c | Worst case: checkpoint reset to 0 on a full collection, so every document is a duplicate | 41 min 9 s | 0 inserted, 41,432,473 duplicates, `completed`; collection count unchanged |
| R4 | `reconcile-summary` on R1 | 11 min 29 s | `ok`: totals equal, 27 / 27 event types equal, 1,000 / 1,000 byte-identical |

### 6.1 Where R1's time goes

The loader is a pipeline. One producer thread reads and splits the stream; four worker threads insert.

**Producer thread (the critical path, 521 s)**

| Component | Seconds | Meaning |
| --- | ---: | --- |
| `hash_s` | 31 | SHA-256 of the archive, used for run identity. Done before streaming starts |
| `source_wait_s` | 244 | Waiting for `pigz` to deliver decompressed bytes |
| `split_s` | 119 | Cutting documents and forming batches |
| `slot_wait_s` | 117 | Waiting because all 4 workers were busy |
| `checkpoint_s` | 0.6 | Journaled checkpoint writes, every 30 s |
| Other | about 10 | Collecting results, final count |

**Insert workers**

- 1,135 s of insert wall time summed across the four threads, about 284 s each, so each worker was busy about 58 % of the time.
- 242 s of client CPU: the driver framing raw bytes into messages.

**Finding:** the producer, not MongoDB, sets the pace. Half its time is spent waiting for decompression: `pigz` cannot parallelize inflate, and it competes for CPU with `mongod`. Adding workers would not help.

**CPU (R1)**

| Process | CPU seconds | Share |
| --- | ---: | ---: |
| `mongod` | 647 | 51 % |
| Loader (Python: split, driver, hash) | 403 (334 user + 69 sys) | 31 % |
| `pigz` | 229 | 18 % |
| **Total** | **1,279** | about 2.5 of 4 vCPU on average |

- **vmstat:** 52 % user, 11 % system, 34 % idle, 3 % I/O wait.
- **Memory:** peak loader RSS was **106 MB**. The stream is never held in memory.
- **Throughput:** steady between 79K and 88K docs/s for every million documents. The first million shows 24K docs/s only because its window includes the 31 s hash.

### 6.2 What the other runs show

- **The validator is almost free.**
  - R1 (`warn`) and R2 (`off`) differ by 7 s of wall time, in the opposite direction, which is within noise.
  - `mongod` used 30 s more CPU with the validator (+5 %).
  - It stays on by default.
- **A crash costs little.**
  - The last checkpoint before the kill covered 15,045 batches. The roughly 2.26 M documents written after it came back as duplicates on resume, which matches 30 s × about 80K docs/s.
  - Nothing was lost or doubled.
  - The resume took as long as a full load (8 min 59 s), for two reasons:
    - skipped batches are still decompressed and split, they are just not sent;
    - duplicates are expensive (next point).
- **Duplicates are about 5× more expensive than inserts.**
  - Replaying all 41.4 M documents onto a full collection ran at 16.8K docs/s.
  - `mongod` used **6,929 CPU seconds**, 10.7× a normal load, and the client used 1,639 s building error reports.
  - That is why the checkpoint interval is short, and why a rerun after `completed` returns immediately instead of replaying.
- **Reconciliation takes about 11.5 min.**

  | Component | Seconds | What it does |
  | --- | ---: | --- |
  | Hash | 33 | SHA-256 of the archive |
  | Source scan | 479 | Decodes every document to read `collection` |
  | Target `$group` | 175 | Counts per event type on the server |
  | Sample fetch and compare | 1 | 1,000 documents by `_id` |

### 6.3 Side by side

| Approach | Full load | Resumable | Verified |
| --- | ---: | --- | --- |
| First loader (gzip chunks + upsert) | about 2 h (observed) | Yes | Counts only |
| Chunked `mongorestore` + staging + `$merge` (archived) | about 4 h 45 min (estimated) | Yes | Yes |
| `mongorestore` from the stream | 12 min 7 s | No | No |
| **`load-summary`** | **8 min 41 s** | **Yes, 30 s granularity** | **Yes, with `reconcile-summary` (+11.5 min)** |

## 7. Limitations

- **One run per configuration.** Run-to-run variance was not measured. R1 and R2 suggest it is at least ±10 s.
- **Idle VM, cold page cache, empty target, only the `_id` index.** Secondary indexes created before the load would slow it down; create them afterwards.
- **No mongod log check.** The validator's `warn` messages in the `mongod` log were not reviewed for this run. The schema was derived from the 100K-document sample, and `reconcile-summary` confirms that every document is present and that a 1,000-document sample is byte-identical.
- **The resume skips batches but still decompresses them.** Seeking inside a gzip stream is not possible without an index. On this data the cost is about 2 minutes.
- **The old-loader numbers come from the earlier observation (2 h) and an extrapolation (archived design).** Neither was rerun at full size. Their slow parts were measured separately in §3.
- **Byte-level comparison is sampled.** 1,000 documents out of 41.4 M are compared byte for byte. Totals and per-type counts cover every document.
