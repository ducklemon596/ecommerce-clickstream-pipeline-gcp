# Product configuration deduplication — local 100K checkpoint

Observed **4 November 2026**, using the real local `data/summary_sample.json` (sequential, non-random Extended JSON prefix). No MongoDB server or website was contacted. The full VM scan remains unexecuted.

## Extension: product URLs across event types

The implementation examines `current_url` for all event types in the input, independently of detail-only configuration output. It never reads `referrer_url`. The bounded sample is the local 100K sequential JSON prefix; the requested VM event-type inspection remains blocked because the SSH account has no readable MongoDB configuration.

| URL inventory metric | Result |
| --- | ---: |
| `current_url` references encountered | 100,000 |
| Invalid/unsupported URLs | 0 |
| Distinct valid HTTP(S) URLs of all kinds | 56,682 |
| Distinct URLs matching observed product pages | 37,549 |
| Product URL occurrences | 59,448 |
| Other product-shaped URLs awaiting review | 7 |
| Unverified candidate occurrences | 9 |
| Scan/SQLite processing time | 4.747 s |
| Source documents/s | 21,066 |
| Peak process RSS | 56.57 MiB |

Outputs are in `data/product_configurations/current_url_only_100k/`: `product_urls.jsonl` and `unverified_product_urls.jsonl`, alongside configuration output, SQLite checkpoint and summary. Matching uses exact hostname/path evidence from current URLs carrying an explicit `product_id` or `viewing_product_id` and store ID, regardless of event type. It supports `.html` and observed `/catalog/product/view/id/…` routes. Mapping arrays preserve ambiguous IDs/stores and identify the source ID field.

This is conservative observed evidence, not a website inventory: a URL-shaped candidate without matching evidence stays unverified. The inventory preserves exact URL variants, including tracking; configuration keys continue to exclude tracking. The 100K local prefix contains 21 event types, fewer than the roughly 27–28 expected from the VM. It validates current URL logic on a sample but cannot identify the additional full-dataset types. The 17,715 configurations and 27,988 occurrences remain consistent. The VM was started and returned to `TERMINATED`, but inspection could not proceed because SSH account `thienquang050906` could not read its `~/.config/glamira/restore.yml`; no other user's credential file was accessed. To complete the event-type survey, make a read-only URI/config available to this SSH account. No full VM scan was run.

## Measured result

| Metric | Result |
| --- | ---: |
| Source documents scanned | 100,000 |
| `view_product_detail` events | 27,993 |
| Accepted detail events | 27,988 |
| Rejected detail events | 5 |
| Unique product/store/host/configuration combinations | 17,715 |
| Duplicate accepted occurrences beyond the first | 10,273 |
| Sum of exported occurrence counts | 27,988 |
| Accepted events with empty configuration | 6,564 |
| Unique empty configurations | 4,090 |
| Events with tracking parameters removed from options | 15,617 |
| Events retaining unknown parameters | 51 |
| Processing time, including JSON read and SQLite commits | 2.203 s |
| Throughput | 45,400 source documents/s |
| Peak Python process RSS | 53.68 MiB |

All five rejected events had malformed parameter names, such as a leading `?`/`;` or a nonempty value with an empty name. No missing/invalid product ID, store ID, or URL was observed among these detail events. Production code also handles those conditions and conflicting repeated option values. Each rejected event has one first-failure reason.

Count checks passed: **27,993 = 27,988 + 5**, **27,988 = 17,715 + 10,273**, and every JSONL row had a distinct composite key. A separate export pass reconciled occurrence totals; SQLite `PRAGMA integrity_check` returned `ok`. The final implementation's unit suite includes normalization, checkpoint rollback/resume and mocked MongoDB reader tests. These are not evidence of live MongoDB performance.

The timing excludes input SHA-256 calculation and JSONL/report export. It is a single local execution with uncontrolled filesystem cache, not a full-scale benchmark or VM runtime estimate. RSS is the process high-water mark, including interpreter/library overhead. Batch size was 5,000; Python 3.10.12, SQLite 3.37.2 and PyMongo 4.18.3 were used. Input SHA-256: `e4f4704a4cacfc08557a2fa5ad1820f4d5f7c3ccf233c3b73d083b11738de36b`.

## Schema decisions and limitations

The actual event has `store_id`, not `store`. Output includes both `store_id` and its `store` alias, plus the full URL hostname. Store ID and hostname both participate in the key: several store IDs share a hostname, and some IDs include development hosts in this sample.

Options come exclusively from nonempty URL parameters. Missing/empty values are omitted and no default rows are manufactured. Unknown parameters are retained with warnings; known tracking parameters and `no_cache` are excluded. Values are preserved after standard query decoding.

All 27,988 accepted events had internal-ID option arrays whose values could not be compared with URL labels; 10,165 had URL keys absent from the option labels. These include additional legitimate URL option names and unknown parameters, so this is a warning rather than a failed configuration. Exact option-value parity is not claimed. Some representative URLs lead to checkout configuration paths; a later crawler must validate target suitability separately.

## Output examples

These are real output rows containing no marketing click identifiers:

```jsonl
{"product_id":"100002","store":"12","store_id":"12","hostname":"www.glamira.fr","normalized_options":{"alloy":"white_yellow-585","diamond":"diamond-Swarovsky","stone2":"diamond-sapphire","stone3":"diamond-Swarovsky"},"source_url":"https://www.glamira.fr/glamira-ring-palmier.html?alloy=white_yellow-585&diamond=diamond-Swarovsky&stone2=diamond-sapphire&stone3=diamond-Swarovsky","occurrence_count":1}
{"product_id":"100039","store":"52","store_id":"52","hostname":"www.glamira.rs","normalized_options":{},"source_url":"https://www.glamira.rs/glamira-pendant-jolandi.html","occurrence_count":1}
```

Full private outputs are in ignored `data/product_configurations/sample_100k_final/`: `configurations.sqlite3`, `configurations.jsonl`, `summary.json`, and `summary.md`. The JSONL retains representative source URLs, which can include tracking values; do not publish the full artifact.

## Reproduction and next step

```bash
uv run deduplicate-products --sample data/summary_sample.json \
  --limit 100000 --batch-size 5000 \
  --output-dir data/product_configurations/sample_100k_final
```

An existing completed checkpoint regenerates exports without rescanning or incrementing counts. Use a fresh output directory to measure another scan. The [workflow README](../../src/glamira_pipeline/products/README.md) contains the prepared MongoDB VM command, permissions, normalization policy and resume limitations. Run the full scan only after authorization; crawling is outside this checkpoint.
