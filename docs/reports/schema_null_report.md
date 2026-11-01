# Schema and NULL Report

- Generated at (UTC): 2026-11-01T01:47:10+00:00
- Input sample: `summary_sample.bson`
- Source: `glamira_ubl_oct2019_nov2019.tar.gz` → `dump/countly/summary.bson`.
- Rows analyzed: 100,000
- Extraction and sampling: first documents from the BSON member (sequential, non-random); no full archive extraction.
- Scope: local sample only; do not interpret as full-dataset statistics.

## How values are classified

- **Missing**: the key is absent from a BSON document.
- **Explicit null**: the key exists and its BSON value is null (`None`).
- **Empty**: an empty string, list, or object.
- **Populated**: present, non-null, and non-empty.
- **Invalid type**: checked only for fields with a provisional expected type listed below. Other fields show their observed types without guessing a contract.

Provisional type checks: `collection` → str, `time_stamp` → int, `ip` → str, `current_url` → str, `referrer_url` → str, `product_id` → str, `cart_products` → list.

## Field states across the full sample

| Field | Missing | Explicit null | Empty | Populated | Invalid type |
|---|---:|---:|---:|---:|---:|
| `_id` | 0 | 0 | 0 | 100000 | 0 |
| `api_version` | 0 | 0 | 0 | 100000 | 0 |
| `cart_products` | 98687 | 0 | 252 | 1061 | 0 |
| `cat_id` | 73948 | 26051 | 0 | 1 | 0 |
| `collect_id` | 73948 | 0 | 20055 | 5997 | 0 |
| `collection` | 0 | 0 | 0 | 100000 | 0 |
| `currency` | 99492 | 11 | 0 | 497 | 0 |
| `current_url` | 0 | 0 | 0 | 100000 | 0 |
| `device_id` | 0 | 0 | 0 | 100000 | 0 |
| `email_address` | 0 | 0 | 92443 | 7557 | 0 |
| `ip` | 0 | 0 | 0 | 100000 | 0 |
| `is_paypal` | 99492 | 497 | 0 | 11 | 0 |
| `key_search` | 99312 | 355 | 23 | 310 | 0 |
| `local_time` | 0 | 0 | 0 | 100000 | 0 |
| `option` | 19542 | 0 | 0 | 80458 | 0 |
| `order_id` | 99607 | 0 | 292 | 101 | 0 |
| `price` | 99492 | 11 | 0 | 497 | 0 |
| `product_id` | 45608 | 0 | 0 | 54392 | 0 |
| `recommendation` | 72007 | 0 | 0 | 27993 | 0 |
| `recommendation_clicked_position` | 99708 | 1 | 0 | 291 | 0 |
| `recommendation_product_id` | 99708 | 1 | 0 | 291 | 0 |
| `referrer_url` | 0 | 0 | 11417 | 88583 | 0 |
| `resolution` | 0 | 0 | 0 | 100000 | 0 |
| `show_recommendation` | 0 | 20073 | 0 | 79927 | 0 |
| `store_id` | 0 | 0 | 0 | 100000 | 0 |
| `time_stamp` | 0 | 0 | 0 | 100000 | 0 |
| `user_agent` | 0 | 0 | 0 | 100000 | 0 |
| `user_id_db` | 0 | 0 | 92443 | 7557 | 0 |
| `utm_medium` | 72007 | 0 | 0 | 27993 | 0 |
| `utm_source` | 72007 | 0 | 0 | 27993 | 0 |
| `viewing_product_id` | 94427 | 0 | 0 | 5573 | 0 |

Always populated in this sample: `_id`, `api_version`, `collection`, `current_url`, `device_id`, `ip`, `local_time`, `resolution`, `store_id`, `time_stamp`, `user_agent`.

## Per-event field presence and NULL patterns

### `add_to_cart_action` (508 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 508 | 0 | ObjectId: 508 |
| `api_version` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `cart_products` | 508 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 508 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 508 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `currency` | 0 | 11 | 0 | 497 | 0 | str: 497, null: 11 |
| `current_url` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `device_id` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `email_address` | 0 | 0 | 441 | 67 | 0 | str: 508 |
| `ip` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `is_paypal` | 0 | 497 | 0 | 11 | 0 | null: 497, bool: 11 |
| `key_search` | 508 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `option` | 0 | 0 | 0 | 508 | 0 | list: 508 |
| `order_id` | 508 | 0 | 0 | 0 | 0 | — |
| `price` | 0 | 11 | 0 | 497 | 0 | str: 497, null: 11 |
| `product_id` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `recommendation` | 508 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 508 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 508 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 54 | 454 | 0 | str: 508 |
| `resolution` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `show_recommendation` | 0 | 50 | 0 | 458 | 0 | str: 458, null: 50 |
| `store_id` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `time_stamp` | 0 | 0 | 0 | 508 | 0 | int: 508 |
| `user_agent` | 0 | 0 | 0 | 508 | 0 | str: 508 |
| `user_id_db` | 0 | 0 | 441 | 67 | 0 | str: 508 |
| `utm_medium` | 508 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 508 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 508 | 0 | 0 | 0 | 0 | — |

### `checkout` (292 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 292 | 0 | ObjectId: 292 |
| `api_version` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `cart_products` | 0 | 0 | 0 | 292 | 0 | list: 292 |
| `cat_id` | 292 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 292 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `currency` | 292 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `device_id` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `email_address` | 0 | 0 | 101 | 191 | 0 | str: 292 |
| `ip` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `is_paypal` | 292 | 0 | 0 | 0 | 0 | — |
| `key_search` | 292 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `option` | 292 | 0 | 0 | 0 | 0 | — |
| `order_id` | 0 | 0 | 292 | 0 | 0 | str: 292 |
| `price` | 292 | 0 | 0 | 0 | 0 | — |
| `product_id` | 292 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 292 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 292 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 292 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 3 | 289 | 0 | str: 292 |
| `resolution` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `show_recommendation` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `store_id` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `time_stamp` | 0 | 0 | 0 | 292 | 0 | int: 292 |
| `user_agent` | 0 | 0 | 0 | 292 | 0 | str: 292 |
| `user_id_db` | 0 | 0 | 101 | 191 | 0 | str: 292 |
| `utm_medium` | 292 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 292 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 292 | 0 | 0 | 0 | 0 | — |

### `checkout_success` (101 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 101 | 0 | ObjectId: 101 |
| `api_version` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `cart_products` | 0 | 0 | 0 | 101 | 0 | list: 101 |
| `cat_id` | 101 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 101 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `currency` | 101 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `device_id` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `email_address` | 0 | 0 | 36 | 65 | 0 | str: 101 |
| `ip` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `is_paypal` | 101 | 0 | 0 | 0 | 0 | — |
| `key_search` | 101 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `option` | 101 | 0 | 0 | 0 | 0 | — |
| `order_id` | 0 | 0 | 0 | 101 | 0 | int: 65, float: 36 |
| `price` | 101 | 0 | 0 | 0 | 0 | — |
| `product_id` | 101 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 101 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 101 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 101 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 1 | 100 | 0 | str: 101 |
| `resolution` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `show_recommendation` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `store_id` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `time_stamp` | 0 | 0 | 0 | 101 | 0 | int: 101 |
| `user_agent` | 0 | 0 | 0 | 101 | 0 | str: 101 |
| `user_id_db` | 0 | 0 | 36 | 65 | 0 | str: 101 |
| `utm_medium` | 101 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 101 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 101 | 0 | 0 | 0 | 0 | — |

### `landing_page_recommendation_visible` (10 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 10 | 0 | ObjectId: 10 |
| `api_version` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `cart_products` | 10 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 10 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 10 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `currency` | 10 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `device_id` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `email_address` | 0 | 0 | 9 | 1 | 0 | str: 10 |
| `ip` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `is_paypal` | 10 | 0 | 0 | 0 | 0 | — |
| `key_search` | 10 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `option` | 10 | 0 | 0 | 0 | 0 | — |
| `order_id` | 10 | 0 | 0 | 0 | 0 | — |
| `price` | 10 | 0 | 0 | 0 | 0 | — |
| `product_id` | 10 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 10 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 10 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 10 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 2 | 8 | 0 | str: 10 |
| `resolution` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `show_recommendation` | 0 | 1 | 0 | 9 | 0 | str: 9, null: 1 |
| `store_id` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `time_stamp` | 0 | 0 | 0 | 10 | 0 | int: 10 |
| `user_agent` | 0 | 0 | 0 | 10 | 0 | str: 10 |
| `user_id_db` | 0 | 0 | 9 | 1 | 0 | str: 10 |
| `utm_medium` | 10 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 10 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 10 | 0 | 0 | 0 | 0 | — |

### `listing_page_recommendation_clicked` (1 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 1 | 0 | ObjectId: 1 |
| `api_version` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `cart_products` | 1 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 0 | 1 | 0 | 0 | 0 | null: 1 |
| `collect_id` | 0 | 0 | 1 | 0 | 0 | str: 1 |
| `collection` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `currency` | 1 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `device_id` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `email_address` | 0 | 0 | 1 | 0 | 0 | str: 1 |
| `ip` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `is_paypal` | 1 | 0 | 0 | 0 | 0 | — |
| `key_search` | 1 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `option` | 0 | 0 | 0 | 1 | 0 | dict: 1 |
| `order_id` | 1 | 0 | 0 | 0 | 0 | — |
| `price` | 1 | 0 | 0 | 0 | 0 | — |
| `product_id` | 1 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 1 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 0 | 1 | 0 | 0 | 0 | null: 1 |
| `recommendation_product_id` | 0 | 1 | 0 | 0 | 0 | null: 1 |
| `referrer_url` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `resolution` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `show_recommendation` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `store_id` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `time_stamp` | 0 | 0 | 0 | 1 | 0 | int: 1 |
| `user_agent` | 0 | 0 | 0 | 1 | 0 | str: 1 |
| `user_id_db` | 0 | 0 | 1 | 0 | 0 | str: 1 |
| `utm_medium` | 1 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 1 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 1 | 0 | 0 | 0 | 0 | — |

### `listing_page_recommendation_noticed` (2 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 2 | 0 | ObjectId: 2 |
| `api_version` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `cart_products` | 2 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 0 | 2 | 0 | 0 | 0 | null: 2 |
| `collect_id` | 0 | 0 | 2 | 0 | 0 | str: 2 |
| `collection` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `currency` | 2 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `device_id` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `email_address` | 0 | 0 | 2 | 0 | 0 | str: 2 |
| `ip` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `is_paypal` | 2 | 0 | 0 | 0 | 0 | — |
| `key_search` | 2 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `option` | 0 | 0 | 0 | 2 | 0 | dict: 2 |
| `order_id` | 2 | 0 | 0 | 0 | 0 | — |
| `price` | 2 | 0 | 0 | 0 | 0 | — |
| `product_id` | 2 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 2 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 2 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 2 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 1 | 1 | 0 | str: 2 |
| `resolution` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `show_recommendation` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `store_id` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `time_stamp` | 0 | 0 | 0 | 2 | 0 | int: 2 |
| `user_agent` | 0 | 0 | 0 | 2 | 0 | str: 2 |
| `user_id_db` | 0 | 0 | 2 | 0 | 0 | str: 2 |
| `utm_medium` | 2 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 2 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 2 | 0 | 0 | 0 | 0 | — |

### `listing_page_recommendation_visible` (17 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 17 | 0 | ObjectId: 17 |
| `api_version` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `cart_products` | 17 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 0 | 17 | 0 | 0 | 0 | null: 17 |
| `collect_id` | 0 | 0 | 16 | 1 | 0 | str: 17 |
| `collection` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `currency` | 17 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `device_id` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `email_address` | 0 | 0 | 16 | 1 | 0 | str: 17 |
| `ip` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `is_paypal` | 17 | 0 | 0 | 0 | 0 | — |
| `key_search` | 17 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `option` | 0 | 0 | 0 | 17 | 0 | dict: 17 |
| `order_id` | 17 | 0 | 0 | 0 | 0 | — |
| `price` | 17 | 0 | 0 | 0 | 0 | — |
| `product_id` | 17 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 17 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 17 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 17 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 6 | 11 | 0 | str: 17 |
| `resolution` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `show_recommendation` | 0 | 3 | 0 | 14 | 0 | str: 14, null: 3 |
| `store_id` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `time_stamp` | 0 | 0 | 0 | 17 | 0 | int: 17 |
| `user_agent` | 0 | 0 | 0 | 17 | 0 | str: 17 |
| `user_id_db` | 0 | 0 | 16 | 1 | 0 | str: 17 |
| `utm_medium` | 17 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 17 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 17 | 0 | 0 | 0 | 0 | — |

### `product_detail_recommendation_clicked` (291 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 291 | 0 | ObjectId: 291 |
| `api_version` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `cart_products` | 291 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 291 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 291 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `currency` | 291 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `device_id` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `email_address` | 0 | 0 | 279 | 12 | 0 | str: 291 |
| `ip` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `is_paypal` | 291 | 0 | 0 | 0 | 0 | — |
| `key_search` | 291 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `option` | 291 | 0 | 0 | 0 | 0 | — |
| `order_id` | 291 | 0 | 0 | 0 | 0 | — |
| `price` | 291 | 0 | 0 | 0 | 0 | — |
| `product_id` | 291 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 291 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 0 | 0 | 0 | 291 | 0 | int: 291 |
| `recommendation_product_id` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `referrer_url` | 0 | 0 | 47 | 244 | 0 | str: 291 |
| `resolution` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `show_recommendation` | 0 | 63 | 0 | 228 | 0 | str: 228, null: 63 |
| `store_id` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `time_stamp` | 0 | 0 | 0 | 291 | 0 | int: 291 |
| `user_agent` | 0 | 0 | 0 | 291 | 0 | str: 291 |
| `user_id_db` | 0 | 0 | 279 | 12 | 0 | str: 291 |
| `utm_medium` | 291 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 291 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 0 | 0 | 0 | 291 | 0 | str: 291 |

### `product_detail_recommendation_noticed` (1,438 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 1438 | 0 | ObjectId: 1438 |
| `api_version` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `cart_products` | 1438 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 1438 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 1438 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `currency` | 1438 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `device_id` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `email_address` | 0 | 0 | 1349 | 89 | 0 | str: 1438 |
| `ip` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `is_paypal` | 1438 | 0 | 0 | 0 | 0 | — |
| `key_search` | 1438 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `option` | 1438 | 0 | 0 | 0 | 0 | — |
| `order_id` | 1438 | 0 | 0 | 0 | 0 | — |
| `price` | 1438 | 0 | 0 | 0 | 0 | — |
| `product_id` | 1438 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 1438 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 1438 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 1438 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 266 | 1172 | 0 | str: 1438 |
| `resolution` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `show_recommendation` | 0 | 247 | 0 | 1191 | 0 | str: 1191, null: 247 |
| `store_id` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `time_stamp` | 0 | 0 | 0 | 1438 | 0 | int: 1438 |
| `user_agent` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |
| `user_id_db` | 0 | 0 | 1349 | 89 | 0 | str: 1438 |
| `utm_medium` | 1438 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 1438 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 0 | 0 | 0 | 1438 | 0 | str: 1438 |

### `product_detail_recommendation_visible` (3,844 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 3844 | 0 | ObjectId: 3844 |
| `api_version` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `cart_products` | 3844 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 3844 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 3844 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `currency` | 3844 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `device_id` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `email_address` | 0 | 0 | 3628 | 216 | 0 | str: 3844 |
| `ip` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `is_paypal` | 3844 | 0 | 0 | 0 | 0 | — |
| `key_search` | 3844 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `option` | 3844 | 0 | 0 | 0 | 0 | — |
| `order_id` | 3844 | 0 | 0 | 0 | 0 | — |
| `price` | 3844 | 0 | 0 | 0 | 0 | — |
| `product_id` | 3844 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 3844 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 3844 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 3844 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 654 | 3190 | 0 | str: 3844 |
| `resolution` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `show_recommendation` | 0 | 819 | 0 | 3025 | 0 | str: 3025, null: 819 |
| `store_id` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `time_stamp` | 0 | 0 | 0 | 3844 | 0 | int: 3844 |
| `user_agent` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |
| `user_id_db` | 0 | 0 | 3628 | 216 | 0 | str: 3844 |
| `utm_medium` | 3844 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 3844 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 0 | 0 | 0 | 3844 | 0 | str: 3844 |

### `search_box_action` (688 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 688 | 0 | ObjectId: 688 |
| `api_version` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `cart_products` | 688 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 688 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 688 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `currency` | 688 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `device_id` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `email_address` | 0 | 0 | 615 | 73 | 0 | str: 688 |
| `ip` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `is_paypal` | 688 | 0 | 0 | 0 | 0 | — |
| `key_search` | 0 | 355 | 23 | 310 | 0 | null: 355, str: 333 |
| `local_time` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `option` | 688 | 0 | 0 | 0 | 0 | — |
| `order_id` | 688 | 0 | 0 | 0 | 0 | — |
| `price` | 688 | 0 | 0 | 0 | 0 | — |
| `product_id` | 688 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 688 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 688 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 688 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 76 | 612 | 0 | str: 688 |
| `resolution` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `show_recommendation` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `store_id` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `time_stamp` | 0 | 0 | 0 | 688 | 0 | int: 688 |
| `user_agent` | 0 | 0 | 0 | 688 | 0 | str: 688 |
| `user_id_db` | 0 | 0 | 615 | 73 | 0 | str: 688 |
| `utm_medium` | 688 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 688 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 688 | 0 | 0 | 0 | 0 | — |

### `select_product_option` (19,731 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 19731 | 0 | ObjectId: 19731 |
| `api_version` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `cart_products` | 19731 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 19731 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 19731 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `currency` | 19731 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `device_id` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `email_address` | 0 | 0 | 18540 | 1191 | 0 | str: 19731 |
| `ip` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `is_paypal` | 19731 | 0 | 0 | 0 | 0 | — |
| `key_search` | 19731 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `option` | 0 | 0 | 0 | 19731 | 0 | list: 19731 |
| `order_id` | 19731 | 0 | 0 | 0 | 0 | — |
| `price` | 19731 | 0 | 0 | 0 | 0 | — |
| `product_id` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `recommendation` | 19731 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 19731 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 19731 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 2806 | 16925 | 0 | str: 19731 |
| `resolution` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `show_recommendation` | 0 | 3622 | 0 | 16109 | 0 | str: 16109, null: 3622 |
| `store_id` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `time_stamp` | 0 | 0 | 0 | 19731 | 0 | int: 19731 |
| `user_agent` | 0 | 0 | 0 | 19731 | 0 | str: 19731 |
| `user_id_db` | 0 | 0 | 18540 | 1191 | 0 | str: 19731 |
| `utm_medium` | 19731 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 19731 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 19731 | 0 | 0 | 0 | 0 | — |

### `select_product_option_quality` (6,160 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 6160 | 0 | ObjectId: 6160 |
| `api_version` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `cart_products` | 6160 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 6160 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 6160 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `currency` | 6160 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `device_id` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `email_address` | 0 | 0 | 5729 | 431 | 0 | str: 6160 |
| `ip` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `is_paypal` | 6160 | 0 | 0 | 0 | 0 | — |
| `key_search` | 6160 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `option` | 0 | 0 | 0 | 6160 | 0 | list: 6160 |
| `order_id` | 6160 | 0 | 0 | 0 | 0 | — |
| `price` | 6160 | 0 | 0 | 0 | 0 | — |
| `product_id` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `recommendation` | 6160 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 6160 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 6160 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 992 | 5168 | 0 | str: 6160 |
| `resolution` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `show_recommendation` | 0 | 1102 | 0 | 5058 | 0 | str: 5058, null: 1102 |
| `store_id` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `time_stamp` | 0 | 0 | 0 | 6160 | 0 | int: 6160 |
| `user_agent` | 0 | 0 | 0 | 6160 | 0 | str: 6160 |
| `user_id_db` | 0 | 0 | 5729 | 431 | 0 | str: 6160 |
| `utm_medium` | 6160 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 6160 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 6160 | 0 | 0 | 0 | 0 | — |

### `view_home_page` (3,131 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 3131 | 0 | ObjectId: 3131 |
| `api_version` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `cart_products` | 3131 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 3131 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 3131 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `currency` | 3131 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `device_id` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `email_address` | 0 | 0 | 2693 | 438 | 0 | str: 3131 |
| `ip` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `is_paypal` | 3131 | 0 | 0 | 0 | 0 | — |
| `key_search` | 3131 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `option` | 3131 | 0 | 0 | 0 | 0 | — |
| `order_id` | 3131 | 0 | 0 | 0 | 0 | — |
| `price` | 3131 | 0 | 0 | 0 | 0 | — |
| `product_id` | 3131 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 3131 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 3131 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 3131 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 1061 | 2070 | 0 | str: 3131 |
| `resolution` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `show_recommendation` | 0 | 4 | 0 | 3127 | 0 | str: 3127, null: 4 |
| `store_id` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `time_stamp` | 0 | 0 | 0 | 3131 | 0 | int: 3131 |
| `user_agent` | 0 | 0 | 0 | 3131 | 0 | str: 3131 |
| `user_id_db` | 0 | 0 | 2693 | 438 | 0 | str: 3131 |
| `utm_medium` | 3131 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 3131 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 3131 | 0 | 0 | 0 | 0 | — |

### `view_landing_page` (3,461 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 3461 | 0 | ObjectId: 3461 |
| `api_version` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `cart_products` | 3461 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 3461 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 3461 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `currency` | 3461 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `device_id` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `email_address` | 0 | 0 | 3309 | 152 | 0 | str: 3461 |
| `ip` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `is_paypal` | 3461 | 0 | 0 | 0 | 0 | — |
| `key_search` | 3461 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `option` | 3461 | 0 | 0 | 0 | 0 | — |
| `order_id` | 3461 | 0 | 0 | 0 | 0 | — |
| `price` | 3461 | 0 | 0 | 0 | 0 | — |
| `product_id` | 3461 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 3461 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 3461 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 3461 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 212 | 3249 | 0 | str: 3461 |
| `resolution` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `show_recommendation` | 0 | 9 | 0 | 3452 | 0 | str: 3452, null: 9 |
| `store_id` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `time_stamp` | 0 | 0 | 0 | 3461 | 0 | int: 3461 |
| `user_agent` | 0 | 0 | 0 | 3461 | 0 | str: 3461 |
| `user_id_db` | 0 | 0 | 3309 | 152 | 0 | str: 3461 |
| `utm_medium` | 3461 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 3461 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 3461 | 0 | 0 | 0 | 0 | — |

### `view_listing_page` (26,032 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 26032 | 0 | ObjectId: 26032 |
| `api_version` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `cart_products` | 26032 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 0 | 26031 | 0 | 1 | 0 | null: 26031, str: 1 |
| `collect_id` | 0 | 0 | 20036 | 5996 | 0 | str: 26032 |
| `collection` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `currency` | 26032 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `device_id` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `email_address` | 0 | 0 | 25029 | 1003 | 0 | str: 26032 |
| `ip` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `is_paypal` | 26032 | 0 | 0 | 0 | 0 | — |
| `key_search` | 26032 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `option` | 0 | 0 | 0 | 26032 | 0 | dict: 26032 |
| `order_id` | 26032 | 0 | 0 | 0 | 0 | — |
| `price` | 26032 | 0 | 0 | 0 | 0 | — |
| `product_id` | 26032 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 26032 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 26032 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 26032 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 851 | 25181 | 0 | str: 26032 |
| `resolution` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `show_recommendation` | 0 | 39 | 0 | 25993 | 0 | str: 25993, null: 39 |
| `store_id` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `time_stamp` | 0 | 0 | 0 | 26032 | 0 | int: 26032 |
| `user_agent` | 0 | 0 | 0 | 26032 | 0 | str: 26032 |
| `user_id_db` | 0 | 0 | 25029 | 1003 | 0 | str: 26032 |
| `utm_medium` | 26032 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 26032 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 26032 | 0 | 0 | 0 | 0 | — |

### `view_my_account` (526 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 526 | 0 | ObjectId: 526 |
| `api_version` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `cart_products` | 526 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 526 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 526 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `currency` | 526 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `device_id` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `email_address` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `ip` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `is_paypal` | 526 | 0 | 0 | 0 | 0 | — |
| `key_search` | 526 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `option` | 526 | 0 | 0 | 0 | 0 | — |
| `order_id` | 526 | 0 | 0 | 0 | 0 | — |
| `price` | 526 | 0 | 0 | 0 | 0 | — |
| `product_id` | 526 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 526 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 526 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 526 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 33 | 493 | 0 | str: 526 |
| `resolution` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `show_recommendation` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `store_id` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `time_stamp` | 0 | 0 | 0 | 526 | 0 | int: 526 |
| `user_agent` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `user_id_db` | 0 | 0 | 0 | 526 | 0 | str: 526 |
| `utm_medium` | 526 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 526 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 526 | 0 | 0 | 0 | 0 | — |

### `view_product_detail` (27,993 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 27993 | 0 | ObjectId: 27993 |
| `api_version` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `cart_products` | 27993 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 27993 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 27993 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `currency` | 27993 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `device_id` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `email_address` | 0 | 0 | 26592 | 1401 | 0 | str: 27993 |
| `ip` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `is_paypal` | 27993 | 0 | 0 | 0 | 0 | — |
| `key_search` | 27993 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `option` | 0 | 0 | 0 | 27993 | 0 | list: 27993 |
| `order_id` | 27993 | 0 | 0 | 0 | 0 | — |
| `price` | 27993 | 0 | 0 | 0 | 0 | — |
| `product_id` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `recommendation` | 0 | 0 | 0 | 27993 | 0 | bool: 27993 |
| `recommendation_clicked_position` | 27993 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 27993 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 3720 | 24273 | 0 | str: 27993 |
| `resolution` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `show_recommendation` | 0 | 14105 | 0 | 13888 | 0 | null: 14105, str: 13888 |
| `store_id` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `time_stamp` | 0 | 0 | 0 | 27993 | 0 | int: 27993 |
| `user_agent` | 0 | 0 | 0 | 27993 | 0 | str: 27993 |
| `user_id_db` | 0 | 0 | 26592 | 1401 | 0 | str: 27993 |
| `utm_medium` | 0 | 0 | 0 | 27993 | 0 | bool: 27340, str: 653 |
| `utm_source` | 0 | 0 | 0 | 27993 | 0 | bool: 27350, str: 643 |
| `viewing_product_id` | 27993 | 0 | 0 | 0 | 0 | — |

### `view_shopping_cart` (920 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 920 | 0 | ObjectId: 920 |
| `api_version` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `cart_products` | 0 | 0 | 252 | 668 | 0 | list: 920 |
| `cat_id` | 920 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 920 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `currency` | 920 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `device_id` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `email_address` | 0 | 0 | 583 | 337 | 0 | str: 920 |
| `ip` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `is_paypal` | 920 | 0 | 0 | 0 | 0 | — |
| `key_search` | 920 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `option` | 920 | 0 | 0 | 0 | 0 | — |
| `order_id` | 920 | 0 | 0 | 0 | 0 | — |
| `price` | 920 | 0 | 0 | 0 | 0 | — |
| `product_id` | 920 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 920 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 920 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 920 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 50 | 870 | 0 | str: 920 |
| `resolution` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `show_recommendation` | 0 | 1 | 0 | 919 | 0 | str: 919, null: 1 |
| `store_id` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `time_stamp` | 0 | 0 | 0 | 920 | 0 | int: 920 |
| `user_agent` | 0 | 0 | 0 | 920 | 0 | str: 920 |
| `user_id_db` | 0 | 0 | 583 | 337 | 0 | str: 920 |
| `utm_medium` | 920 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 920 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 920 | 0 | 0 | 0 | 0 | — |

### `view_sorting_relevance` (14 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 14 | 0 | ObjectId: 14 |
| `api_version` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `cart_products` | 14 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 14 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 14 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `currency` | 14 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `device_id` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `email_address` | 0 | 0 | 13 | 1 | 0 | str: 14 |
| `ip` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `is_paypal` | 14 | 0 | 0 | 0 | 0 | — |
| `key_search` | 14 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `option` | 0 | 0 | 0 | 14 | 0 | dict: 14 |
| `order_id` | 14 | 0 | 0 | 0 | 0 | — |
| `price` | 14 | 0 | 0 | 0 | 0 | — |
| `product_id` | 14 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 14 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 14 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 14 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 3 | 11 | 0 | str: 14 |
| `resolution` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `show_recommendation` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `store_id` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `time_stamp` | 0 | 0 | 0 | 14 | 0 | int: 14 |
| `user_agent` | 0 | 0 | 0 | 14 | 0 | str: 14 |
| `user_id_db` | 0 | 0 | 13 | 1 | 0 | str: 14 |
| `utm_medium` | 14 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 14 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 14 | 0 | 0 | 0 | 0 | — |

### `view_static_page` (4,840 rows)

| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 0 | 0 | 0 | 4840 | 0 | ObjectId: 4840 |
| `api_version` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `cart_products` | 4840 | 0 | 0 | 0 | 0 | — |
| `cat_id` | 4840 | 0 | 0 | 0 | 0 | — |
| `collect_id` | 4840 | 0 | 0 | 0 | 0 | — |
| `collection` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `currency` | 4840 | 0 | 0 | 0 | 0 | — |
| `current_url` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `device_id` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `email_address` | 0 | 0 | 3478 | 1362 | 0 | str: 4840 |
| `ip` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `is_paypal` | 4840 | 0 | 0 | 0 | 0 | — |
| `key_search` | 4840 | 0 | 0 | 0 | 0 | — |
| `local_time` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `option` | 4840 | 0 | 0 | 0 | 0 | — |
| `order_id` | 4840 | 0 | 0 | 0 | 0 | — |
| `price` | 4840 | 0 | 0 | 0 | 0 | — |
| `product_id` | 4840 | 0 | 0 | 0 | 0 | — |
| `recommendation` | 4840 | 0 | 0 | 0 | 0 | — |
| `recommendation_clicked_position` | 4840 | 0 | 0 | 0 | 0 | — |
| `recommendation_product_id` | 4840 | 0 | 0 | 0 | 0 | — |
| `referrer_url` | 0 | 0 | 579 | 4261 | 0 | str: 4840 |
| `resolution` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `show_recommendation` | 0 | 8 | 0 | 4832 | 0 | str: 4832, null: 8 |
| `store_id` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `time_stamp` | 0 | 0 | 0 | 4840 | 0 | int: 4840 |
| `user_agent` | 0 | 0 | 0 | 4840 | 0 | str: 4840 |
| `user_id_db` | 0 | 0 | 3478 | 1362 | 0 | str: 4840 |
| `utm_medium` | 4840 | 0 | 0 | 0 | 0 | — |
| `utm_source` | 4840 | 0 | 0 | 0 | 0 | — |
| `viewing_product_id` | 4840 | 0 | 0 | 0 | 0 | — |

## Interpretation

Field sparsity differs by event type in this sample, which is consistent with a schema-on-read event model. Treat missing fields on event types that do not use them as potentially expected; confirm semantics with the event producer before calling them defects.

Some fields can contain both missing values and explicit BSON nulls. The two states are reported separately. Type checks are provisional and should be replaced with a documented source contract when available.
