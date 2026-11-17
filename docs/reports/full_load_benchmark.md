# Full load of `summary.bson`: measured result

**Observed:** 2026-11-14 on the project VM, using the **full** `summary.bson` member: **41,432,473 documents**, **33,530,129,089 bytes**.

**Outcome:** `load-summary` loads every document in **8 min 41 s**, and a rerun resumes after a crash. `reconcile-summary` then confirms three things:
- the same total;
- the same count for each of the 27 event types;
- 1,000 / 1,000 sampled documents byte-identical.

How to run the loader is in the [operations guide](../../src/glamira_pipeline/load/README.md).

## 1. Requirements

The source is one mongodump BSON file, `dump/countly/summary.bson`, inside a 5.5 GB `.tar.gz`. It must become a MongoDB collection under three requirements:

| Requirement | Why it matters |
| --- | --- |
| **Fast** | A slow load blocks every later step and keeps the VM running, which costs money |
| **Safe to retry** | A crash, an SSH drop or a reboot must not duplicate or silently lose documents |
| **Verifiable** | A zero exit code is not proof that the data is complete and unchanged |

There is a constraint as well. The boot disk had 11 GB free, and the data disk is reserved for `dbPath`, so **the 33.5 GB BSON cannot be extracted to a file**. The loader streams the member straight out of the `.tar.gz`.

## 2. How the loader works

```text
.tar.gz ──tar+pigz──▶ bytes ──length prefix──▶ batches of 1,000 docs ──▶ 4 insert threads ──▶ MongoDB
                                                       │                          │
                                                       └──── watermark ◀── batch done
                                                                │
                                                      load_runs (every 30 s, journaled)
```

1. **Stream.** `tar` with `pigz` decompresses the member into a pipe; there is no temporary file.
2. **Split.** Each BSON document starts with its 4-byte length, so the stream is cut into documents without decoding them. They are grouped into batches of at most 1,000 documents and 16 MB. The boundaries are deterministic: the same archive gives the same batches.
3. **Insert.** Four threads send `insert_many(RawBSONDocument, ordered=False)`. The original bytes reach MongoDB unchanged, and the source `_id` is the key.
4. **Checkpoint.** A watermark is saved to `load_runs` every 30 s. It is the last batch before which every batch is done.
5. **Finish.** The run must satisfy `docs_seen = skipped + inserted + duplicates`, and the target count must equal the source count. `reconcile-summary` is a separate read-only check.

| Safety need | Mechanism |
| --- | --- |
| No duplicates on retry | Re-inserting a source `_id` fails with error 11000, which is counted as a duplicate. With `ordered=False`, the rest of the batch is still inserted. Any other error stops the load |
| Resume without rescanning MongoDB | A restart skips every batch below the watermark without sending it |
| Workers finishing out of order | The watermark moves only over a contiguous run of finished batches (a min-heap). Batches after it are re-sent and come back as duplicates |
| Wrong source or wrong target | A run's identity is the archive SHA-256, the member, the target and the batch limits. Resuming also requires the same collection UUID. A non-empty target without a matching run is refused |
| Two loaders at once | A heartbeat lock of 120 s. A run whose heartbeat has expired is marked `abandoned` |
| Ctrl+C or an SSH drop | SIGINT, SIGTERM and SIGHUP let in-flight batches finish, save the checkpoint and exit with code 130 |
| Malformed events | A lenient `$jsonSchema` validator requires `_id`, a string `collection` and a numeric `time_stamp`. It runs with `validationAction: warn`, so `mongod` logs violations but rejects no source document |

## 3. Environment

| Item | Value |
| --- | --- |
| VM | `e2-standard-4`: 4 vCPU, 15 GiB RAM, no swap |
| Disks | Boot disk: 30 GB `pd-balanced`, holding a copy of the archive. Data disk: 80 GB `pd-balanced`, the MongoDB `dbPath` |
| Software | MongoDB 8.0.34, mongorestore 100.20.0, Python 3.12.3, pymongo 4.18.3, pigz (Ubuntu 24.04 package) |
| Source | `glamira_ubl_oct2019_nov2019.tar.gz`, 5,495,914,358 bytes, SHA-256 `30beabd5…a89a53aa8` |
| Isolation | Separate benchmark database, one new collection per run, all dropped afterwards. `countly.summary` was not touched (still 41,432,473 documents) |
| Method | One run at a time. Before each run the page cache was dropped. During the run `vmstat 5` was recorded, and `mongod` CPU was read from `/proc` before and after |

## 4. Why this design: each component measured

**Reading the archive** (no MongoDB). Every row reads the whole archive.

| Stage | Wall time | Throughput | CPU (user+sys) |
| --- | ---: | ---: | ---: |
| Read the 5.5 GB `.tar.gz` from disk | 31 s | 180 MB/s | 5 s |
| Decompress with Python `tarfile` | 174 s | 193 MB/s | 174 s |
| Decompress with `tar` + `pigz` | 130 s | 259 MB/s | 265 s |
| `pigz` + split by length prefix | 254 s | 163K docs/s | 417 s |
| `pigz` + split + `bson.decode` of every document | 463 s | 90K docs/s | 622 s |

**Writing to MongoDB.** Each row includes the decompression and the split.

| Writer | Wall time | Docs/s | CPU busy |
| --- | ---: | ---: | ---: |
| `mongorestore`, 1 insertion worker | 12 min 7 s | 56,977 | 89 % |
| `mongorestore`, 4 insertion workers | 12 min 25 s | 55,598 | 89 % |
| Raw `insert_many`, 1 thread | 12 min 6 s | 57,085 | 52 % |
| Raw `insert_many`, **4 threads** | **8 min 49 s** | **78,379** | 69 % |
| Raw `insert_many`, 8 threads | 8 min 59 s | 76,911 | 69 % |

**What the measurements decided:**
- **`pigz` instead of Python gzip:** about 25 % faster.
- **Split without decoding:** about 2 minutes. Decoding every document would double the read time, and the loader never needs to decode.
- **Raw `insert_many` with 4 threads:** the fastest writer.
  - It is 27 % faster than `mongorestore`, which is CPU-bound at 89 % and did not speed up with more workers.
  - Going from 4 to 8 threads gained nothing: the limit is on the server.
  - About 30 % of the CPU stays free for `mongod`.
- **Disk was never the limit.** I/O wait stayed at 1–2 %, and throughput did not drop as the `_id` index grew.

## 5. Results of the production loader

Four runs, all into the disposable database `glamira_load_bench`, at git `72073d2`.

| Run | What it tests | Wall time | Result |
| --- | --- | ---: | --- |
| R1 | Full load, validator `warn` (default) | **8 min 41 s** | 41,432,473 inserted, 0 duplicates, `completed` |
| R2 | Full load, validator `off` | 8 min 48 s | 41,432,473 inserted, `completed` |
| R3a → R3b | `SIGKILL` 270 s into a load; wait out the heartbeat; rerun the same command | 8 min 59 s for the resume | 15,045,000 skipped + 24,131,473 inserted + 2,256,000 duplicates = 41,432,473, `completed` |
| R3c | Worst case: checkpoint reset to 0 on a full collection, so every document is a duplicate | 41 min 9 s | 0 inserted, 41,432,473 duplicates, `completed`; collection count unchanged |
| R4 | `reconcile-summary` on R1 | 11 min 29 s | `ok`: totals equal, 27 / 27 event types equal, 1,000 / 1,000 byte-identical |

### 5.1 Comparing the runs

| | R1: normal load | R2: no validator | R3b: resume after a crash | R3c: everything a duplicate |
| --- | ---: | ---: | ---: | ---: |
| Wall time | 8 min 41 s | 8 min 48 s | 8 min 59 s | 41 min 9 s |
| Inserted | 41,432,473 | 41,432,473 | 24,131,473 | 0 |
| Skipped by watermark | 0 | 0 | 15,045,000 | 0 |
| Duplicates | 0 | 0 | 2,256,000 | 41,432,473 |
| Throughput | about 80K docs/s | about 79K docs/s | — | 16.8K docs/s |
| `mongod` CPU | 647 s | about 617 s | — | 6,929 s |

- **The validator is almost free (R1 against R2).**
  - Wall time differs by 7 s, and in the opposite direction, which is within noise.
  - `mongod` used 30 s more CPU with the validator (+5 %), so it stays on by default.
- **A crash costs little (R3b).**
  - The last checkpoint covered 15,045 batches. The roughly 2.26 M documents written after it came back as duplicates, which matches 30 s × about 80K docs/s.
  - Nothing was lost or doubled.
  - The resume still took as long as a full load. Skipped batches must still be decompressed and split, and duplicates are expensive.
- **Duplicates cost about 5× an insert (R3c).**
  - Replaying all 41.4 M documents onto a full collection used 10.7× the normal `mongod` CPU, plus 1,639 s of client CPU to build error reports.
  - This is why the checkpoint interval is short, and why a rerun after `completed` returns immediately instead of replaying.

### 5.2 Where R1's time goes

One producer thread reads and splits the stream; four worker threads insert.

**Producer thread** (the critical path, 521 s)

| Component | Seconds | Meaning |
| --- | ---: | --- |
| `hash_s` | 31 | SHA-256 of the archive for the run identity, computed before streaming |
| `source_wait_s` | 244 | Waiting for `pigz` to deliver decompressed bytes |
| `split_s` | 119 | Cutting documents and forming batches |
| `slot_wait_s` | 117 | Waiting because all 4 workers were busy |
| `checkpoint_s` | 0.6 | Journaled checkpoint writes, every 30 s |
| Other | about 10 | Collecting results, final count |

**Insert workers**
- 1,135 s of insert wall time summed over the four threads: about 284 s each, so each was busy about 58 % of the time.
- 242 s of client CPU, spent by the driver framing raw bytes into messages.

**CPU**

| Process | CPU seconds | Share |
| --- | ---: | ---: |
| `mongod` | 647 | 51 % |
| Loader (Python: split, driver, hash) | 403 (334 user + 69 sys) | 31 % |
| `pigz` | 229 | 18 % |
| **Total** | **1,279** | about 2.5 of 4 vCPU on average |

- **The producer sets the pace, not MongoDB.** Half of its time goes to waiting for decompression: `pigz` cannot parallelize inflate, and it competes with `mongod` for CPU. More insert workers would not help.
- **Memory:** peak loader RSS was **106 MB**; the stream is never held in memory.
- **Throughput was steady**, between 79K and 88K docs/s for every million documents. The first million shows only 24K docs/s, because that window includes the 31 s hash.

### 5.3 Reconciliation (R4)

| Component | Seconds | What it does |
| --- | ---: | --- |
| Hash | 33 | SHA-256 of the archive |
| Source scan | 479 | Decodes every document to read `collection` |
| Target `$group` | 175 | Counts per event type on the server |
| Sample fetch and compare | 1 | 1,000 documents by `_id` |

## 6. Limitations

- **One run per configuration.** Run-to-run variance was not measured; R1 and R2 suggest it is at least ±10 s.
- **Idle VM, cold page cache, empty target, only the `_id` index.** Secondary indexes created before the load would slow it down, so create them afterwards.
- **`mongod` log not reviewed.** The validator's `warn` messages were not checked for these runs. `reconcile-summary` confirms that every document is present and that a 1,000-document sample is byte-identical.
- **A resume still decompresses the skipped batches.** A gzip stream cannot be seeked without an index; on this data that costs about 2 minutes.
- **Byte-level comparison is sampled.** 1,000 of 41.4 M documents are compared byte for byte; totals and per-type counts cover every document.
