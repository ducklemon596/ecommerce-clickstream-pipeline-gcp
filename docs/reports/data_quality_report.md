# Data Quality Report

- Generated at (UTC): 2026-11-01T01:47:10+00:00
- Input sample: `summary_sample.bson`
- Source: `glamira_ubl_oct2019_nov2019.tar.gz` → `dump/countly/summary.bson`.
- Rows analyzed: 100,000
- Extraction and sampling: first documents from the BSON member (sequential, non-random); no full archive extraction.
- Scope: local sample only; do not interpret as full-dataset statistics.

## Summary of checks

| Check | Result | Interpretation / action |
|---|---|---|
| Duplicate `_id` values | 0 duplicate groups; 0 excess rows | Review if nonzero; `_id` is expected to identify a document. |
| Duplicate `(ip, time_stamp)` pairs | 1,323 groups; 1,397 excess rows | Not a unique event key: timestamps have second-level granularity and many events can share a second. |
| Future timestamps | 0/100,000 valid numeric timestamps | Review any future-dated rows. |
| Missing/null/empty `ip` | 0 missing; 0 null; 0 empty | IP coverage denominator is all sampled events. |
| Valid IP format | 100,000/100,000 non-empty string IP values | Syntax check only; no geolocation or routability claim. |
| Currency coverage in checkout cart items | 110/112 items with currency | Multiple currency codes/symbols require normalization before cross-market revenue comparison. |
| Negative or unusually large revenue | Not reliably assessed | Top-level checkout `price`/`currency` are absent in this sample; nested prices are locale-formatted strings. Parse with locale and currency rules before numeric checks. |

## Fields missing or null in over 50% of sample rows

| Field | Missing or explicit null | Rate |
|---|---:|---:|
| `cart_products` | 98,687/100,000 | 98.7% |
| `cat_id` | 99,999/100,000 | 100.0% |
| `collect_id` | 73,948/100,000 | 73.9% |
| `currency` | 99,503/100,000 | 99.5% |
| `is_paypal` | 99,989/100,000 | 100.0% |
| `key_search` | 99,667/100,000 | 99.7% |
| `order_id` | 99,607/100,000 | 99.6% |
| `price` | 99,503/100,000 | 99.5% |
| `recommendation` | 72,007/100,000 | 72.0% |
| `recommendation_clicked_position` | 99,709/100,000 | 99.7% |
| `recommendation_product_id` | 99,709/100,000 | 99.7% |
| `utm_medium` | 72,007/100,000 | 72.0% |
| `utm_source` | 72,007/100,000 | 72.0% |
| `viewing_product_id` | 94,427/100,000 | 94.4% |

## Currency values observed in checkout items

`€` (63), `£` (13), `kr` (9), `CHF` (6), `AU $` (6), `$` (4), `zł` (2), `kn` (1), `₺` (1), `Ft` (1), `CAD $` (1), `₱` (1), `лв.` (1), `Kč` (1)

## Limitations and full-data risks

- This is a sequential prefix sample of 100,000 documents from a BSON dump, not a random or population-representative sample.
- Duplicate-pair results can be inflated by timestamp precision and event volume; do not deduplicate on `(ip, time_stamp)`.
- Revenue sanity checks need a confirmed nested cart schema, decimal parsing rules, and currency-specific thresholds.
- Counts and quality rates must be recomputed on the full collection before making population-wide claims.
