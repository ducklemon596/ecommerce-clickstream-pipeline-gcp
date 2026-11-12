# Glamira Project 5: sample data quality

This project extracts a bounded local sample from a Glamira MongoDB BSON dump and assesses its data quality. The current sample is a **sequential, non-random prefix**: findings describe the sample, not the 41 million-document collection. The quality workflow reads local JSON and does not connect to MongoDB or GCP.

## Setup

Install Python and `uv`, put `glamira_ubl_oct2019_nov2019.tar.gz` in the project root, then run:

```bash
uv sync
uv run extract-sample --limit 100000
uv run assess-data-quality
```

If the JSON sample already exists, skip extraction and run the quality command directly. Samples under `data/` are ignored by Git and can contain customer data.

## Extract a sample

The extractor reads `dump/countly/summary.bson` from the compressed tar stream, one document at a time, and stops at the requested limit (1–100,000). It creates:

- `data/summary_sample.json`: a Canonical Extended JSON array, preserving BSON types.
- `data/summary_sample.metadata.json`: source, selection method, counts, size, and extraction time.

Use `uv run extract-sample --help` for `--archive`, `--limit`, and `--output`. The output path must end in `.json`; metadata uses the same stem. Rerunning replaces those two outputs after successful extraction. A malformed or missing source returns a nonzero exit and staged files are cleaned up. Existing BSON sample files are left untouched.

## Assess data quality

```bash
uv run assess-data-quality --sample data/summary_sample.json --max-documents 100000
```

The command streams up to 100,000 JSON documents in one pass. Duplicate detection keeps hashes of identifiers and IP/timestamp pairs without retaining raw IP addresses or full records. If the input exceeds the cap, the report says only a prefix was assessed. Use `--output-dir` to choose the directory for the reports.

The command creates [a short summary](docs/reports/data_quality_report.md) and six reports under `docs/reports/data_quality/`:

- `nulls.md`: top-level missing and explicit-null rates, with >50% flagged for review.
- `duplicates.md`: `_id` and IP/timestamp duplicate counts, group sizes, mixed event types, and IPv4/IPv6/invalid-address breakdowns.
- `timestamps.md`: UTC timestamp range and future values, plus local time field coverage and wall-clock range (timezone unknown).
- `revenue.md`: leading negative signs in `checkout_success` item prices.
- `currencies.md`: top-level and cart-item currency values.
- `ip_addresses.md`: completeness and IPv4/IPv6 syntax counts.

The checks treat missing keys, BSON nulls, and empty values separately. Sparse event-specific fields are not automatically defects; IP/timestamp duplicates do not prove duplicate events. Numeric `time_stamp` values are interpreted as Unix seconds in UTC, an assumption to confirm with the data producer. Checkout prices occur inside `cart_products`; order-level revenue and unusually large prices remain unassessed until price semantics, locale parsing, and thresholds are confirmed. Currency symbols may be ambiguous.

Input errors return a nonzero exit before reports are generated. The report writer stages all seven files before publishing each one; the summary is published last. The generated reports can be replaced by rerunning the command.

## Historical event-field specification

The earlier [event-field specification](docs/specifications/event_type_expected_fields.preview.md) is retained as a historical observation of the same local sample. Its former profiler and supporting metrics have been removed.

## Tests

```bash
uv run python -m unittest discover -s tests/unit -v
```

## IP location enrichment

The maintained workflow uses an unsorted MongoDB cursor with requested batch size **50K**, an in-memory IP Counter, durable counter output, offline BIN lookup and verified staging publication. SQLite checkpoint and benchmark implementations have been retired.

See the [IP Location README](src/glamira_pipeline/ip_location/README.md) for sample/full commands, schema, recovery limitations and measured comparisons explaining the choice.

## Product configurations

`uv run deduplicate-products` streams JSON or MongoDB events, extracts observed URL configurations from `view_product_detail`, and deduplicates them on disk with SQLite. It retains product ID, store ID and hostname, counts occurrences and exports JSONL. No web crawling or default inference occurs.

The same pass inventories `current_url` across all event types, exporting evidence-backed matches and unverified candidates separately. It never reads `referrer_url`.

See the [product workflow](src/glamira_pipeline/products/README.md) for local/VM commands and recovery rules, and the [100K validation report](docs/reports/product_configuration_deduplication.md) for measured results.

The [product configuration research](analysis/product_configuration_research/README.md) investigates all 27 event types, with measured counterexamples and proposed reconstruction rules awaiting review. It includes selection timing, quality representation, recommendation ownership, and cart-option mapping limitations.
