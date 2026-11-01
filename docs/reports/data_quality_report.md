# Data Quality Report — Summary

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

| Check | Sample result | Details |
|---|---|---|
| NULL analysis | 31 top-level fields measured; high rates require event context | [NULL report](data_quality/nulls.md) |
| Duplicate identifiers | _id: 0 groups, 0 excess rows (100,000 usable IDs) | [Duplicates](data_quality/duplicates.md) |
| Duplicate IP/timestamp pairs | 1,323 groups, 1,397 excess rows; not necessarily duplicate events | [Duplicates](data_quality/duplicates.md) |
| Timestamps | 0 future, 0 invalid, 0 missing/null | [Timestamps](data_quality/timestamps.md) |
| Checkout price signs | 0 leading-negative strings or negative numeric prices in 112 cart items from 101 checkout-success events | [Revenue](data_quality/revenue.md) |
| Currency values | 28 distinct currency-like values across top-level and cart items | [Currencies](data_quality/currencies.md) |
| IP syntax | 100,000 valid, 0 invalid format, 0 invalid type | [IP addresses](data_quality/ip_addresses.md) |

Order-level revenue and unusually large amounts are **not assessed**: confirmed amount semantics, locale parsing, and thresholds are unavailable.

These observations describe this sample only. Empty values, explicit BSON nulls, and missing keys are separate categories.
