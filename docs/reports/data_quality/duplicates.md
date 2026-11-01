# Duplicate Detection

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Identifier check uses `_id`. Missing, null, and blank IDs are excluded; counts are type-aware.

| Key | Usable rows | Skipped rows | Duplicate groups | Excess rows |
|---|---:|---:|---:|---:|
| `_id` | 100,000 | 0 | 0 | 0 |
| `(ip, time_stamp)` | 100,000 | 0 | 1,323 | 1,397 |

The 1,323 repeated IP/timestamp groups contain **2,720 rows** in total: 1,323 first occurrences plus 1,397 excess rows.
Of those groups, 584 include multiple event-type labels and 739 have one observed label. Missing or invalid labels share one placeholder.

## Repeated pairs by IP version

Addresses are parsed only for classification. Pair grouping preserves the original exact IP string and BSON timestamp; equivalent spellings are not merged. IPv4-mapped IPv6 addresses are classified as IPv6.

| IP version | Duplicate groups | Rows in groups | Excess rows |
|---|---:|---:|---:|
| IPv4 | 1,323 | 2,720 | 1,397 |
| IPv6 | 0 | 0 | 0 |
| Invalid address | 0 | 0 | 0 |

## Group sizes

| Rows per group | Groups | Rows in those groups |
|---:|---:|---:|
| 2 | 1,270 | 2,540 |
| 3 | 36 | 108 |
| 4 | 15 | 60 |
| 6 | 2 | 12 |

Excess rows count repetitions after the first in each group. IP/timestamp pairs exclude missing, null, or blank IPs and missing/null timestamps. A shared IP and second can represent legitimate distinct actions; never deduplicate events solely on this pair. Raw IP examples are not retained.
