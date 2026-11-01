# NULL Analysis

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Missing keys and explicit BSON nulls count as NULL; empty strings/arrays/objects do not. This is the existing top-level calculation, with no nested-field expansion. A rate above 50% is flagged for review, not automatically treated as a defect: event types have different payloads.

| Field | Missing | BSON null | Missing + null | Rate | Review |
|---|---:|---:|---:|---:|---|
| `cat_id` | 73,948 | 26,051 | 99,999 | 99.9990% | >50% |
| `is_paypal` | 99,492 | 497 | 99,989 | 99.99% | >50% |
| `recommendation_clicked_position` | 99,708 | 1 | 99,709 | 99.71% | >50% |
| `recommendation_product_id` | 99,708 | 1 | 99,709 | 99.71% | >50% |
| `key_search` | 99,312 | 355 | 99,667 | 99.67% | >50% |
| `order_id` | 99,607 | 0 | 99,607 | 99.61% | >50% |
| `currency` | 99,492 | 11 | 99,503 | 99.50% | >50% |
| `price` | 99,492 | 11 | 99,503 | 99.50% | >50% |
| `cart_products` | 98,687 | 0 | 98,687 | 98.69% | >50% |
| `viewing_product_id` | 94,427 | 0 | 94,427 | 94.43% | >50% |
| `collect_id` | 73,948 | 0 | 73,948 | 73.95% | >50% |
| `recommendation` | 72,007 | 0 | 72,007 | 72.01% | >50% |
| `utm_medium` | 72,007 | 0 | 72,007 | 72.01% | >50% |
| `utm_source` | 72,007 | 0 | 72,007 | 72.01% | >50% |
| `product_id` | 45,608 | 0 | 45,608 | 45.61% | — |
| `show_recommendation` | 0 | 20,073 | 20,073 | 20.07% | — |
| `option` | 19,542 | 0 | 19,542 | 19.54% | — |
| `_id` | 0 | 0 | 0 | 0.00% | — |
| `api_version` | 0 | 0 | 0 | 0.00% | — |
| `collection` | 0 | 0 | 0 | 0.00% | — |
| `current_url` | 0 | 0 | 0 | 0.00% | — |
| `device_id` | 0 | 0 | 0 | 0.00% | — |
| `email_address` | 0 | 0 | 0 | 0.00% | — |
| `ip` | 0 | 0 | 0 | 0.00% | — |
| `local_time` | 0 | 0 | 0 | 0.00% | — |
| `referrer_url` | 0 | 0 | 0 | 0.00% | — |
| `resolution` | 0 | 0 | 0 | 0.00% | — |
| `store_id` | 0 | 0 | 0 | 0.00% | — |
| `time_stamp` | 0 | 0 | 0 | 0.00% | — |
| `user_agent` | 0 | 0 | 0 | 0.00% | — |
| `user_id_db` | 0 | 0 | 0 | 0.00% | — |

Percentages use all sampled events, so a field relevant to only one event may be mostly absent by design.
