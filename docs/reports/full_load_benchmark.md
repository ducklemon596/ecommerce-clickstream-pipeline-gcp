# Full-load benchmark: decompress, split and insert measured separately

**Observed:** 2026-11-14 on the project VM. Every stage processed the **full** `summary.bson` member: **41,432,473 documents**, **33,530,129,089 bytes**.
**Purpose:** find where load time actually goes before choosing a loader design. This report records measurements only; it does not choose the design.

## Environment

| Item | Value |
| --- | --- |
| VM | `e2-standard-4`: 4 vCPU, 15 GiB RAM, no swap |
| Disks | Boot disk 30 GB `pd-balanced` (archive copy here); data disk 80 GB `pd-balanced` (MongoDB `dbPath`) |
| Software | MongoDB 8.0.34, mongorestore 100.20.0, Python 3.12.3, pymongo 4.18.3, pigz (Ubuntu 24.04 package) |
| Source | `glamira_ubl_oct2019_nov2019.tar.gz`, 5,495,914,358 bytes, SHA-256 `30beabd5…a89a53aa8`, member `dump/countly/summary.bson` |
| Target | Database `glamira_bench`, one new collection per run, dropped after its count was checked. `countly.*` was not touched |
| Method | `scripts/bench_load.py`. Stages ran one at a time; page cache dropped before each one; `vmstat 5` recorded during each one |

The data disk holds only `dbPath`, and the boot disk had 11 GB free. **The 33.5 GB BSON could not be extracted to a file on this VM.** Every stage therefore streams the member from the `.tar.gz`, as the original restore did.

## Results

### Reading, decompressing and splitting (no MongoDB)

| Stage | What it does | Wall time | Throughput | CPU (user+sys) |
| --- | --- | ---: | ---: | ---: |
| Read archive | Read 5.5 GB `.tar.gz` from `pd-balanced` | 31 s | 180 MB/s | 5 s |
| Decompress, Python `gzip` | `tarfile` (mode `r\|gz`) → `/dev/null`; no splitting | 174 s | 193 MB/s | 174 s |
| Decompress, `pigz` | `tar` + `pigz` → `/dev/null`; no splitting | 130 s | 259 MB/s | 265 s |
| Split, raw | `pigz` + cut into 100K-doc batches by the 4-byte length prefix | 254 s | 163K docs/s | 417 s |
| Split + decode | as above, plus `bson.decode` of every document | 463 s | 90K docs/s | 622 s |
| Split + gzip batches | as above (raw), plus `gzip -6` of every batch (old loader) | 961 s | 43K docs/s | 1,104 s |

### Writing to MongoDB (each includes `pigz` decompression and splitting)

| Stage | Wall time | Docs/s | Stored | CPU busy (vmstat) |
| --- | ---: | ---: | ---: | ---: |
| `mongorestore`, 1 insertion worker | **12 min 7 s** (727 s) | 56,977 | 41,432,473; 0 failures | 89% |
| `mongorestore`, 4 insertion workers | 12 min 25 s (745 s) | 55,598 | 41,432,473; 0 failures | 89% |
| Python `insert_many(RawBSONDocument, ordered=False)`, 1 thread | 12 min 6 s (726 s) | 57,085 | 41,432,473 | 52% |
| Python `insert_many`, **4 threads** | **8 min 49 s** (529 s) | **78,379** | 41,432,473 | 69% |
| Python `insert_many`, 8 threads | 8 min 59 s (539 s) | 76,911 | 41,432,473 | 69% |
| Python decode + `ReplaceOne(upsert=True)`, 1 thread (old loader) | **56 min 57 s** (3,417 s) | 12,126 | 41,432,473 | 39% |

- **Disk wait (`wa`) stayed at 1–2 %** in every MongoDB stage, so the disks were never the limit.
- **Throughput did not decay** as the `_id` index grew. Per-million-document windows stayed flat; the 4-thread insert stayed between 57K and 83K docs/s from the first window to the last.
- **The reference restore of 2026-10-31** (stdin, into `countly.summary`) took 14 min 51 s. That is consistent with the 12 min measured here on a dropped-cache, otherwise idle VM.

## What the numbers show

1. **Decompression is not the bottleneck.** `pigz` takes about 2 minutes for the whole member; Python's `gzip` takes about 3 minutes.
2. **Splitting by length prefix is cheap.** It costs about 2 minutes on top of decompression (254 s − 130 s), with no decoding. A Python batcher is not what makes a loader slow.
3. **The old loader's time is explained by two choices, not by batching:**
   - Re-gzipping every batch: about 12 extra minutes (961 s − 254 s).
   - Decode + upsert: about 57 minutes, **6.5× slower** than a plain insert with 4 threads.
   - Together with reading the chunks back, this accounts for the roughly 2 h observed earlier.
4. **A Python loader can be faster than `mongorestore`.** Raw-BSON `insert_many` with 4 threads finished in 8 min 49 s, against 12 min 7 s for `mongorestore`.
   - `mongorestore` is CPU-bound on this 4-vCPU VM (89 % busy), and adding insertion workers did not help.
   - The Python path never decodes documents and left about 30 % CPU idle. Going from 4 to 8 threads gained nothing, so the server side is the limit at that point.
5. **Retry cost.** `insert_many(ordered=False)` keyed on the source `_id` is idempotent: replaying a batch only produces duplicate-key errors, which can be counted and skipped. A checkpoint (for example a byte offset per batch) therefore needs no upsert.

## Limitations

- **One run per configuration.** Run-to-run variance was not measured.
- **Idle VM, cold page cache, empty target collections.** A load into a collection that already holds data, or with secondary indexes, will be slower.
- **No document validator was enabled** during the inserts. A `$jsonSchema` validator adds server CPU that was not measured.
- **Duplicate-key retries were not measured.** Re-inserting batches that already exist was not benchmarked.
- **Extracted-file variant not measured.** Reading from an extracted `.bson` file could not be tested because the VM has no disk space for it outside `dbPath`. It would at most save the roughly 2 minutes of decompression.
- **Old-loader reconstruction.** The 2 h figure for the old loader is the earlier observation. This benchmark reproduces its parts separately rather than rerunning the original code.
