# Data Exploration Report

- Generated at (UTC): 2026-11-01T01:47:10+00:00
- Input sample: `summary_sample.bson`
- Source: `glamira_ubl_oct2019_nov2019.tar.gz` → `dump/countly/summary.bson`.
- Rows analyzed: 100,000
- Extraction and sampling: first documents from the BSON member (sequential, non-random); no full archive extraction.
- Scope: local sample only; do not interpret as full-dataset statistics.

## Overview

- Records profiled: 100,000
- Top-level fields: 31
- Event types: 21
- Unique non-empty IPs: 13,725 (count only; values omitted)
- Timestamp range (interpreted as Unix seconds, UTC): 2020-06-04T06:38:29+00:00 to 2020-06-04T10:21:32+00:00

## Rows by event type

| Event type | Rows | Share |
|---|---:|---:|
| view_product_detail | 27,993 | 27.99% |
| view_listing_page | 26,032 | 26.03% |
| select_product_option | 19,731 | 19.73% |
| select_product_option_quality | 6,160 | 6.16% |
| view_static_page | 4,840 | 4.84% |
| product_detail_recommendation_visible | 3,844 | 3.84% |
| view_landing_page | 3,461 | 3.46% |
| view_home_page | 3,131 | 3.13% |
| product_detail_recommendation_noticed | 1,438 | 1.44% |
| view_shopping_cart | 920 | 0.92% |
| search_box_action | 688 | 0.69% |
| view_my_account | 526 | 0.53% |
| add_to_cart_action | 508 | 0.51% |
| checkout | 292 | 0.29% |
| product_detail_recommendation_clicked | 291 | 0.29% |
| checkout_success | 101 | 0.10% |
| listing_page_recommendation_visible | 17 | 0.02% |
| view_sorting_relevance | 14 | 0.01% |
| landing_page_recommendation_visible | 10 | 0.01% |
| listing_page_recommendation_noticed | 2 | 0.00% |
| listing_page_recommendation_clicked | 1 | 0.00% |

## Top-level fields and observed BSON types

| Field | Present rows | Types among present values |
|---|---:|---|
| `_id` | 100,000/100,000 | ObjectId: 100,000 |
| `api_version` | 100,000/100,000 | str: 100,000 |
| `cart_products` | 1,313/100,000 | list: 1,313 |
| `cat_id` | 26,052/100,000 | null: 26,051, str: 1 |
| `collect_id` | 26,052/100,000 | str: 26,052 |
| `collection` | 100,000/100,000 | str: 100,000 |
| `currency` | 508/100,000 | str: 497, null: 11 |
| `current_url` | 100,000/100,000 | str: 100,000 |
| `device_id` | 100,000/100,000 | str: 100,000 |
| `email_address` | 100,000/100,000 | str: 100,000 |
| `ip` | 100,000/100,000 | str: 100,000 |
| `is_paypal` | 508/100,000 | null: 497, bool: 11 |
| `key_search` | 688/100,000 | null: 355, str: 333 |
| `local_time` | 100,000/100,000 | str: 100,000 |
| `option` | 80,458/100,000 | list: 54,392, dict: 26,066 |
| `order_id` | 393/100,000 | str: 292, int: 65, float: 36 |
| `price` | 508/100,000 | str: 497, null: 11 |
| `product_id` | 54,392/100,000 | str: 54,392 |
| `recommendation` | 27,993/100,000 | bool: 27,993 |
| `recommendation_clicked_position` | 292/100,000 | int: 291, null: 1 |
| `recommendation_product_id` | 292/100,000 | str: 291, null: 1 |
| `referrer_url` | 100,000/100,000 | str: 100,000 |
| `resolution` | 100,000/100,000 | str: 100,000 |
| `show_recommendation` | 100,000/100,000 | str: 79,927, null: 20,073 |
| `store_id` | 100,000/100,000 | str: 100,000 |
| `time_stamp` | 100,000/100,000 | int: 100,000 |
| `user_agent` | 100,000/100,000 | str: 100,000 |
| `user_id_db` | 100,000/100,000 | str: 100,000 |
| `utm_medium` | 27,993/100,000 | bool: 27,340, str: 653 |
| `utm_source` | 27,993/100,000 | bool: 27,350, str: 643 |
| `viewing_product_id` | 5,573/100,000 | str: 5,573 |

No document values are included in this report.
