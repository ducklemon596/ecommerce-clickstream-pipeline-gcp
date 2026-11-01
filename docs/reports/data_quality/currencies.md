# Currency Values

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Top-level currency values are counted across all sampled events; nested currency values are counted across object items in every `cart_products` array. These are distinct contexts, so counts should not be added as event counts.

| Value | Top-level events | Cart items |
|---|---:|---:|
| `$` | 17 | 4 |
| `AED` | 1 | 0 |
| `AU $` | 20 | 6 |
| `CAD $` | 2 | 1 |
| `CHF` | 13 | 6 |
| `CHF '` | 3 | 0 |
| `CLP` | 18 | 0 |
| `Ft` | 48 | 1 |
| `HKD $` | 4 | 0 |
| `Kč` | 6 | 1 |
| `MXN $` | 1 | 0 |
| `RM` | 2 | 0 |
| `RON` | 12 | 0 |
| `SGD $` | 6 | 0 |
| `ZAR` | 5 | 0 |
| `din` | 1 | 0 |
| `kn` | 2 | 1 |
| `kr` | 32 | 9 |
| `zł` | 7 | 2 |
| `£` | 38 | 13 |
| `лв` | 4 | 0 |
| `лв.` | 0 | 1 |
| `₫` | 1 | 0 |
| `€` | 242 | 63 |
| `₱` | 6 | 1 |
| `₴` | 1 | 0 |
| `₺` | 4 | 1 |
| `￥` | 1 | 0 |

| Context | Rows/items | Nonempty values | Missing | Null | Empty | Invalid/redacted |
|---|---:|---:|---:|---:|---:|---:|
| Top level | 100,000 | 497 | 99,492 | 11 | 0 | 0 |
| Cart items | 1,740 | 110 | 1,628 | 0 | 2 | 0 |

Non-object cart items excluded from currency checks: 0.

Currency symbols can be ambiguous. Normalize currencies and confirm exchange-rate rules before comparing monetary values. Invalid or suspicious currency values are counted without exposing their contents.
