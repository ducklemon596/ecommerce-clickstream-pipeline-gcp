# Checkout Price Sign Check

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Only `checkout_success` events are considered. The check looks at `cart_products[].price`, which is an item price, not a verified order amount. For strings it detects a leading minus sign followed by a digit; it does not parse locale-dependent amounts or claim that every other string is nonnegative. Numeric values are checked directly.

| Check | Result |
|---|---:|
| Checkout-success events | 101 |
| Checkout events with missing/invalid cart | 0 |
| Object cart items | 112 |
| Non-object checkout cart items | 0 |
| Nonempty price strings | 112 |
| Strings with leading negative sign | 0 |
| Strings without a recognizable leading number | 0 |
| Numeric prices / negative numeric prices | 0 / 0 |
| Missing / null / empty / invalid prices | 0 / 0 / 0 / 0 |
| Checkout events with top-level `order_amount` present / non-null | 0 / 0 |

**Not assessed:** order-level revenue and unusually large amounts. The sample uses locale-formatted item-price strings; currency-specific parsing, price semantics, and business thresholds are not confirmed.
