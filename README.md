# Glamira Project 5

Local source-data investigation for the Glamira event BSON dump. Phase 0 profiling uses a small, sequential sample and does not connect to GCP or MongoDB.

## Phase 0 sample reports

Requirements: Python version declared in `.python-version`, dependencies in `pyproject.toml`, and the source archive `glamira_ubl_oct2019_nov2019.tar.gz` in the repository root.

```bash
uv sync
uv run extract-sample --limit 10000
uv run generate-reports
```

The extractor streams the beginning of `dump/countly/summary.bson` from the compressed tar archive, one document at a time, and writes:

- `data/summary_sample.bson` — original BSON documents for profiling.
- `data/summary_sample.json` — a readable Canonical Extended JSON array preserving BSON types such as ObjectId, dates, and decimals.
- `data/summary_sample.metadata.json` — source, sampling method, counts, output sizes, and extraction timestamp.

All local files under `data/` are ignored by Git. Extraction accepts 1–100,000 documents and stops after the requested prefix, without unpacking the full dump. The sample is sequential and non-random. Rerunning replaces these sample outputs after successful extraction; malformed input fails with a nonzero exit status and temporary files are cleaned up. Use `--output data/another_sample.bson` to change the output stem, or `--archive PATH` for the archive location.

The report generator uses the BSON sample, reads at most 100,000 documents, and writes:

- `docs/reports/data_exploration_report.md`
- `docs/reports/schema_null_report.md`
- `docs/reports/data_quality_report.md`

Override paths or the document cap with `uv run generate-reports --help`. Reports omit raw document values and IP addresses. Do not use sample findings as full-dataset claims.
