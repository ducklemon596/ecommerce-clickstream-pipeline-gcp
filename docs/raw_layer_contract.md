# Raw layer data contract: Parquet files and BigQuery tables

**Status:** in force from 2026-11-17; files are Parquet since 2026-11-22 (Avro before; see the [format benchmark](../benchmarks/README.md)). **Applies to:** every file written by `export-raw` and every table in the BigQuery `glamira_raw` dataset.

The contract is code, not this page. Each table is declared once in [`tables.py`](../src/glamira_pipeline/export/tables.py). From that one declaration:

- the BigQuery schemas in [`schemas/raw/*.bq.json`](../schemas/raw/) are generated, field descriptions included;
- the Parquet (Arrow) schema of the files is derived from the BigQuery schema;
- the row converter is driven by the same declaration.

A unit test fails if the committed schema files differ from the declaration. The tables below are generated from the same source. Why the schema looks like this, including rejected alternatives, is in the [decision record](decisions/raw_events_schema.md).

## 1. Data flow

```mermaid
flowchart LR
    M[(MongoDB countly<br/>summary, ip_locations,<br/>products, product_option_values)] -->|read-only cursor| C[export-raw<br/>convert + HMAC]
    C --> F[part-NNNNN.parquet<br/>schema file<br/>_manifest.json]
    F -->|publish-export| G[(GCS<br/>raw/&lt;table&gt;/export_id=…/)]
    G -->|_load.json → Cloud Function<br/>PARQUET load job| B[(BigQuery glamira_raw.*)]
```

| Table | Source collection | Grain | Key | Rows (2026-11-17) | Partition / cluster |
| --- | --- | --- | --- | --- | --- |
| `glamira_raw.events` | `countly.summary` | One tracking event | `_id` | 41,432,473 | `DATE(time_stamp)` (65 days) / `collection` |
| `glamira_raw.ip_locations` | `countly.ip_locations` | One distinct valid IP | `ip_hash` | 3,239,627 | none (small) |
| `glamira_raw.products` | `countly.products` | One product ID referenced by events | `product_id` | 19,557 | none |
| `glamira_raw.product_option_values` | `countly.product_option_values` | One (product, option, value) | `product_id, option_id, value_id` | 923,294 | none |

Row counts are those of the source collections; an export must reproduce them exactly (section 6).

## 2. Type system

| Contract type | Parquet (Arrow) type | BigQuery type | Notes |
| --- | --- | --- | --- |
| STRING | `string` | STRING | All identifiers, including numeric ones |
| INT64 | `int64` | INT64 | |
| BOOL | `bool` | BOOL | |
| NUMERIC | `decimal128(38, 9)` | NUMERIC | Exact; BigQuery NUMERIC is precisely (38, 9). A value with more than 9 decimals fails the export |
| TIMESTAMP | `timestamp[us, tz=UTC]` | TIMESTAMP | UTC microseconds |
| RECORD | `struct` | STRUCT | Struct type names below (e.g. `OptionItem`) are labels for the documentation |

| Mode | Parquet (Arrow) | BigQuery | Empty value |
| --- | --- | --- | --- |
| REQUIRED | not nullable | REQUIRED | A missing or null source value fails the export |
| NULLABLE | nullable | NULLABLE | NULL (missing key and explicit null are not distinguished) |
| REPEATED | non-null `list<T>` | REPEATED (ARRAY), with list inference | `[]` |

**When a field is REQUIRED:** for events, when it was present and non-null in all 41,432,473 documents. For the enrichment tables, only when the producing pipeline guarantees it: its MongoDB validator requires a non-null value. A REQUIRED column can be relaxed to NULLABLE later without a reload; the reverse is impossible.

## 3. Conversion rules

Raw keeps values; only representations change. Every rule other than `as_is` is counted per source path in the export manifest.

| Rule | Accepts | Produces | Anything else |
| --- | --- | --- | --- |
| `as_is` | Exactly the contract type (Decimal128 for NUMERIC, BSON date for TIMESTAMP) | Same value | Violation |
| `objectid_hex` | ObjectId | 24-char lowercase hex | Violation |
| `unix_seconds` | int | seconds × 1,000,000 (TIMESTAMP) | Violation |
| `integer_as_string` | string, int, integral double | string unchanged; number as decimal digits (`3571009023.0` → `"3571009023"`) | bool or non-integral number: violation |
| `bool_as_string` | string, bool | string unchanged; `false` → `"false"`, `true` → `"true"` | Violation |
| `int_as_bool` | bool, 0, 1 | bool; `0` → `false`, `1` → `true` | Any other int: violation |
| `number_as_decimal` | int, double, Decimal128 | exact decimal | Violation |
| `hmac` | string | HMAC-SHA256 hex (64 chars); `""` kept | Violation |
| `hmac_email` | string | HMAC of the trimmed, lower-cased value; `""` kept | Violation |
| `hmac_ip` | string | HMAC of the canonical IP (`ipaddress`), so `2001:DB8:0::1` and `2001:db8::1` match; an unparseable value is hashed as stored and counted | Violation |
| `array_form` | array of objects, or object | array → rows; object → `[]` (it goes to the `object_form` column) | Violation |
| `object_form` | object, or array | object → STRUCT; array → NULL | Violation |
| `empty_string_as_empty_array` | array of objects, or `""` | `""` → `[]` | Violation |

**Rules applied to every document**
- **Unknown keys are refused.** A key that is not in the contract fails the export, at the top level and inside every nested object.
- **Redundant `_id`.** In `products` and `product_option_values`, the source `_id` repeats the key fields. The converter checks that they are equal and then drops `_id`.
- **Violations stop the export.** The error names the table, the document number, the `_id` and the field path. For `ip_locations` the `_id` is left out, because it is a raw IP.

## 4. Personal data

Decided by the owner on 2026-11-16 (email, device ID) and 2026-11-17 (IP, customer ID).

| Source field | Raw column | Treatment |
| --- | --- | --- |
| `summary.email_address` | `events.email_hash` | `hmac_email` |
| `summary.device_id` | `events.device_id_hash` | `hmac` |
| `summary.ip` | `events.ip_hash` | `hmac_ip` |
| `summary.user_id_db` | `events.user_id_hash` | `hmac` (exactly as stored; `""` for the 95.19% anonymous events stays `""`) |
| `ip_locations._id` (the IP) | `ip_locations.ip_hash` | `hmac_ip`: same key and normalization, so `events.ip_hash = ip_locations.ip_hash` is the geolocation join |

- **Key:** `GLAMIRA_PII_HASH_KEY`, at least 32 random bytes as hex. Generate it with `python -c 'import secrets; print(secrets.token_hex(32))'`.
  - It lives only in the environment of the export run. It is never committed, logged or written next to the data.
  - It must be kept: an export with another key produces hashes that do not join with earlier ones.
- **Checking the key:** each manifest records `pii_key_fingerprint`, an HMAC of a fixed message. Equal fingerprints mean the hashes are comparable. The key cannot be recovered from the fingerprint.
- **Not pseudonymized:** `user_agent` (kept for browser, OS and device analysis in staging; `device_id_hash` already identifies the device), free text in `key_search`, and URLs. Keep the `glamira_raw` dataset restricted; column-level policy tags can be added later without a reload.

## 5. Tables

### 5.1 `glamira_raw.events`

Source: `countly.summary`, 27 event types. Source types are from the full scan of 41,432,473 documents on 2026-11-14.

**Field meanings**
- Event-specific fields are NULL outside the event types that send them; the [data dictionary](data_dictionary.md) lists which types send which field.
- The source `option` has two shapes, and they go to different columns:
  - the **array form** in product events → `option`;
  - the **object form** in listing events → `option_filter`.
- Real examples of each nested type are in the [decision record](decisions/raw_events_schema.md#complex-types-and-why-they-are-needed).

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `_id` | STRING | REQUIRED | `_id` | objectId 41.43 M | `objectid_hex` | Event ID: source ObjectId as 24 hex chars |
| `collection` | STRING | REQUIRED | `collection` | string 41.43 M | — | Event type, e.g. view_product_detail |
| `time_stamp` | TIMESTAMP | REQUIRED | `time_stamp` | int 41.43 M | `unix_seconds` | Event time (UTC) from Unix seconds |
| `api_version` | STRING | REQUIRED | `api_version` | string 41.43 M | — | Tracker API version |
| `store_id` | STRING | REQUIRED | `store_id` | string 41.43 M | — | Glamira store ID (digits) |
| `current_url` | STRING | REQUIRED | `current_url` | string 41.43 M | — | Page URL |
| `referrer_url` | STRING | REQUIRED | `referrer_url` | string 41.43 M | — | Referrer URL; '' for direct entries |
| `ip_hash` | STRING | REQUIRED | `ip` | string 41.43 M | `hmac_ip` | HMAC-SHA256 of the normalized client IP; joins ip_locations.ip_hash |
| `device_id_hash` | STRING | REQUIRED | `device_id` | string 41.43 M | `hmac` | HMAC-SHA256 of the device ID |
| `user_id_hash` | STRING | REQUIRED | `user_id_db` | string 41.43 M | `hmac` | HMAC-SHA256 of the customer ID; '' for anonymous visits (95.19%) |
| `user_agent` | STRING | REQUIRED | `user_agent` | string 41.43 M | — | Browser user agent |
| `local_time` | STRING | NULLABLE | string` | `local_time` | string 41.43 M, null 240 | — | Client local time as sent, e.g. '2020-05-20 3:6:40' |
| `resolution` | STRING | NULLABLE | string` | `resolution` | string 41.43 M, null 240 | — | Screen resolution as sent |
| `email_hash` | STRING | NULLABLE | string` | `email_address` | string 41.43 M, null 397 | `hmac_email` | HMAC-SHA256 of the trimmed, lower-cased email; '' when not given |
| `show_recommendation` | STRING | NULLABLE | string` | `show_recommendation` | string 33.67 M, null 7.77 M | — | 'true'/'false' as sent; a few malformed values |
| `product_id` | STRING | NULLABLE | string` | `product_id` | string 22.24 M | — | Product of a product event |
| `viewing_product_id` | STRING | NULLABLE | string` | `viewing_product_id` | string 1.99 M | — | Product page on which a recommendation was shown |
| `recommendation_product_id` | STRING | NULLABLE | string` | `recommendation_product_id` | string 217,700, null 25,596 | — | Recommended product |
| `recommendation_clicked_position` | INT64 | NULLABLE | long` | `recommendation_clicked_position` | int 179,226, null 25,547 | — | Clicked slot (always 0 observed) |
| `recommendation_product_position` | STRING | NULLABLE | string` | `recommendation_product_position` | int 20,128, string 18,344, null 51 | `integer_as_string` | Slot of the recommended product; int or string in the source |
| `recommendation` | BOOL | NULLABLE | boolean` | `recommendation` | bool 10.94 M, null 68 | — | Recommendation flag (only false observed) |
| `utm_source` | STRING | NULLABLE | string` | `utm_source` | bool 10.86 M, string 88,179, null 68 | `bool_as_string` | Campaign source; source false becomes 'false' |
| `utm_medium` | STRING | NULLABLE | string` | `utm_medium` | bool 10.85 M, string 90,721, null 68 | `bool_as_string` | Campaign medium; source false becomes 'false' |
| `cat_id` | STRING | NULLABLE | string` | `cat_id` | null 12.04 M, string 258 | — | Category ID of a listing page |
| `collect_id` | STRING | NULLABLE | string` | `collect_id` | string 12.04 M | — | Collection ID of a listing page |
| `key_search` | STRING | NULLABLE | string` | `key_search` | null 163,108, string 75,200 | — | Search text (search_box_action) |
| `price` | STRING | NULLABLE | string` | `price` | string 186,590, null 1,311 | — | Locale-formatted price (add_to_cart_action) |
| `currency` | STRING | NULLABLE | string` | `currency` | string 186,590, null 1,311 | — | Currency symbol (add_to_cart_action) |
| `is_paypal` | BOOL | NULLABLE | boolean` | `is_paypal` | null 186,592, bool 1,309 | — | PayPal express checkout (only true observed) |
| `order_id` | STRING | NULLABLE | string` | `order_id` | string 88,540, int 16,116, double 9,963 | `integer_as_string` | Order number (checkout_success); '' in checkout |
| `option` | ARRAY<STRUCT> | REPEATED | `option` | array 22.21 M, object 12.09 M | `array_form` | Chosen product options: the array form of the source 'option' |
| `option_filter` | STRUCT | NULLABLE | OptionFilter` | `option` | array 22.21 M, object 12.09 M | `object_form` | Listing filter state: the object form of the source 'option' |
| `cart_products` | ARRAY<STRUCT> | REPEATED | `cart_products` | array 457,696 | — | Cart lines (cart and checkout events) |

**`option` — struct `OptionItem`**

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `option[].option_label` | STRING | NULLABLE | string` | `option[].option_label` | string 33.46 M | — | Option name, e.g. alloy, diamond, stone/diamonds |
| `option[].option_id` | STRING | NULLABLE | string` | `option[].option_id` | string 33.28 M | — | Product option ID; joins product_option_values.option_id |
| `option[].value_label` | STRING | NULLABLE | string` | `option[].value_label` | string 33.46 M | — | Selected value label |
| `option[].value_id` | STRING | NULLABLE | string` | `option[].value_id` | string 33.39 M | — | Selected value ID; joins product_option_values.value_id |
| `option[].quality` | STRING | NULLABLE | string` | `option[].quality` | string 2.23 M | — | Stone quality code (select_product_option_quality only) |
| `option[].quality_label` | STRING | NULLABLE | string` | `option[].quality_label` | string 1.93 M | — | Stone quality label (select_product_option_quality only) |

**`option_filter` — struct `OptionFilter`**

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `option_filter.alloy` | STRING | NULLABLE | string` | `option.alloy` | string 12.09 M | — | Metal filter |
| `option_filter.diamond` | STRING | NULLABLE | string` | `option.diamond` | string 12.06 M | — | Stone filter |
| `option_filter.shapediamond` | STRING | NULLABLE | string` | `option.shapediamond` | string 12.06 M | — | Stone shape filter |
| `option_filter.stone` | STRING | NULLABLE | string` | `option.stone` | string 33,664 | — | Stone filter (view_all_recommend) |
| `option_filter.price` | STRING | NULLABLE | string` | `option.price` | string 33,664 | — | Price filter (view_all_recommend) |
| `option_filter.finish` | STRING | NULLABLE | string` | `option.finish` | string 33,664 | — | Finish filter (view_all_recommend) |
| `option_filter.pearlcolor` | STRING | NULLABLE | string` | `option.pearlcolor` | string 33,664 | — | Pearl colour filter (view_all_recommend) |
| `option_filter.kollektion` | STRING | NULLABLE | string` | `option.Kollektion` | string 33,664 | — | Collection filter; source key 'Kollektion' |
| `option_filter.kollektion_id` | STRING | NULLABLE | string` | `option.kollektion_id` | string 33,664 | — | Collection ID filter (view_all_recommend) |
| `option_filter.category_id` | STRING | NULLABLE | string` | `option.category id` | string 33,664 | — | Category filter; source key 'category id' |

**`cart_products` — struct `CartProduct`**

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `cart_products[].product_id` | STRING | NULLABLE | string` | `cart_products[].product_id` | int 822,438 | `integer_as_string` | Product ID; int in the source |
| `cart_products[].amount` | INT64 | NULLABLE | long` | `cart_products[].amount` | int 160,181 | — | Quantity (checkout, checkout_success); -1 to 9,999 observed |
| `cart_products[].price` | STRING | NULLABLE | string` | `cart_products[].price` | string 35,065 | — | Locale-formatted unit price (checkout_success), e.g. '55,00' |
| `cart_products[].currency` | STRING | NULLABLE | string` | `cart_products[].currency` | string 35,065 | — | Currency symbol (checkout_success), e.g. '€' |
| `cart_products[].option` | ARRAY<STRUCT> | REPEATED | `cart_products[].option` | array 673,929, string 148,509 | `empty_string_as_empty_array` | Chosen options; the source string '' becomes an empty array |

**`option` — struct `CartOption`**

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `cart_products[].option[].option_id` | STRING | NULLABLE | string` | `cart_products[].option[].option_id` | int 1.13 M | `integer_as_string` | Option ID; int in the source |
| `cart_products[].option[].option_label` | STRING | NULLABLE | string` | `cart_products[].option[].option_label` | string 1.13 M | — | Option name |
| `cart_products[].option[].value_id` | STRING | NULLABLE | string` | `cart_products[].option[].value_id` | int 1.13 M | `integer_as_string` | Value ID; int in the source |
| `cart_products[].option[].value_label` | STRING | NULLABLE | string` | `cart_products[].option[].value_label` | string 1.13 M | — | Selected value label |

### 5.2 `glamira_raw.ip_locations`

Source: `countly.ip_locations`, written by `enrich-ip-locations` (offline IP2Location DB3 BIN dated 2016-11-29). Source types measured on 2026-11-17 over all 3,239,627 documents.

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `ip_hash` | STRING | REQUIRED | `_id` | string 3.24 M | `hmac_ip` | HMAC-SHA256 of the normalized IP; joins events.ip_hash |
| `ip_version` | INT64 | REQUIRED | `ip_version` | int 3.24 M | — | 4 or 6 |
| `status` | STRING | REQUIRED | `status` | string 3.24 M | — | resolved, no_match, not_public, unsupported_ipv6 or lookup_failed |
| `country_code` | STRING | NULLABLE | string` | `country_code` | string 3.20 M, null 38,241 | — | ISO 3166-1 alpha-2; null unless resolved |
| `country_name` | STRING | NULLABLE | string` | `country_name` | string 3.20 M, null 38,241 | — | Country name; null unless resolved |
| `region` | STRING | NULLABLE | string` | `region` | string 3.20 M, null 40,075 | — | Region; null when unknown |
| `city` | STRING | NULLABLE | string` | `city` | string 3.20 M, null 40,075 | — | City; null when unknown |
| `database_id` | STRING | REQUIRED | `database_id` | string 3.24 M | — | SHA-256 of the IP2Location BIN used |

### 5.3 `glamira_raw.products`

Source: `countly.products`, written by `crawl-products` from the 2026 catalog. These prices are not the prices of the 2020 events. Source types measured on 2026-11-17 over all 19,557 documents. The source `_id` equals `product_id` and is dropped.

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `product_id` | STRING | REQUIRED | `product_id` | string 19,557 | — | Product ID, same form as events.product_id |
| `status` | STRING | REQUIRED | `status` | string 19,557 | — | success, not_found, error or blocked |
| `status_code` | INT64 | NULLABLE | long` | `status_code` | int 19,557 | — | HTTP status; null on a network error |
| `attempts` | INT64 | REQUIRED | `attempts` | int 19,557 | — | Crawl attempts |
| `error` | STRING | NULLABLE | string` | `error` | null 19,557 | — | Error message of a failed attempt |
| `name` | STRING | NULLABLE | string` | `name` | string 19,121, null 436 | — | Product name |
| `sku` | STRING | NULLABLE | string` | `sku` | string 19,121, null 436 | — | SKU |
| `attribute_set_id` | STRING | NULLABLE | string` | `attribute_set_id` | int 19,121, null 436 | `integer_as_string` | Attribute set ID |
| `attribute_set` | STRING | NULLABLE | string` | `attribute_set` | string 19,121, null 436 | — | Attribute set name |
| `type_id` | STRING | NULLABLE | string` | `type_id` | string 19,121, null 436 | — | simple, product_set, virtual or deposit |
| `product_type` | STRING | NULLABLE | string` | `product_type` | string 19,121, null 436 | — | ring, wedding_ring, pendant, ... |
| `product_type_value` | STRING | NULLABLE | string` | `product_type_value` | string 19,065, null 492 | — | Product type code |
| `collection` | STRING | NULLABLE | string` | `collection` | string 19,121, null 436 | — | Collection name |
| `collection_id` | STRING | NULLABLE | string` | `collection_id` | string 18,471, null 1,086 | — | Collection ID |
| `category` | STRING | NULLABLE | string` | `category` | int 18,968, null 436, string 153 | `integer_as_string` | Category ID; usually '0' |
| `category_name` | STRING | NULLABLE | string` | `category_name` | string 19,121, null 436 | — | Category name |
| `gender` | STRING | NULLABLE | string` | `gender` | string 14,324, bool 4,797, null 436 | `bool_as_string` | women, men, or 'false' when the site sends false |
| `price` | NUMERIC | NULLABLE | decimal(38,9)` | `price` | decimal 19,120, null 437 | — | Price in currency, tax included |
| `min_price` | NUMERIC | NULLABLE | decimal(38,9)` | `min_price` | decimal 18,639, null 918 | — | Lowest configurable price |
| `max_price` | NUMERIC | NULLABLE | decimal(38,9)` | `max_price` | decimal 18,639, null 918 | — | Highest configurable price |
| `min_price_format` | STRING | NULLABLE | string` | `min_price_format` | string 19,121, null 436 | — | Formatted lowest price |
| `max_price_format` | STRING | NULLABLE | string` | `max_price_format` | string 19,121, null 436 | — | Formatted highest price |
| `full_price` | NUMERIC | NULLABLE | decimal(38,9)` | `full_price` | decimal 19,121, null 436 | — | List price |
| `sale_price` | NUMERIC | NULLABLE | decimal(38,9)` | `sale_price` | decimal 19,121, null 436 | — | Sale price |
| `full_price_format` | STRING | NULLABLE | string` | `full_price_format` | string 19,121, null 436 | — | Formatted list price |
| `sale_price_format` | STRING | NULLABLE | string` | `sale_price_format` | string 19,121, null 436 | — | Formatted sale price |
| `currency` | STRING | NULLABLE | string` | `currency` | string 19,121, null 436 | — | ISO currency code, e.g. USD |
| `include_tax` | BOOL | NULLABLE | boolean` | `include_tax` | bool 19,121, null 436 | — | Whether prices include tax |
| `default_tax` | NUMERIC | NULLABLE | decimal(38,9)` | `default_tax` | int 19,121, null 436 | `number_as_decimal` | Default tax rate |
| `current_tax` | NUMERIC | NULLABLE | decimal(38,9)` | `current_tax` | int 19,121, null 436 | `number_as_decimal` | Current tax rate |
| `use_gold_price` | BOOL | NULLABLE | boolean` | `use_gold_price` | bool 19,121, null 436 | — | Price follows the gold price |
| `option_count` | INT64 | NULLABLE | long` | `option_count` | int 19,121, null 436 | — | Number of configurable options |
| `source` | STRUCT | REQUIRED | `source` | object 19,557 | — | Storefront request that produced the row |
| `run_id` | STRING | REQUIRED | `run_id` | string 19,557 | — | Crawl run ID (enrichment_runs) |
| `crawled_at` | TIMESTAMP | REQUIRED | `crawled_at` | date 19,557 | — | Crawl time (UTC) |

**`source` — struct `ProductSource`**

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `source.host` | STRING | REQUIRED | `source.host` | string 19,557 | — | Storefront host that answered |
| `source.store_code` | STRING | REQUIRED | `source.store_code` | string 19,557 | — | Storefront code |
| `source.url` | STRING | REQUIRED | `source.url` | string 19,557 | — | Requested react_data URL |
| `source.requested_currency` | STRING | REQUIRED | `source.requested_currency` | string 19,557 | — | Currency requested |

### 5.4 `glamira_raw.product_option_values`

Source: `countly.product_option_values`. Source types measured on 2026-11-17 over all 923,294 documents. The source `_id` is `{product_id, option_id, value_id}` and is dropped.

| Column | BigQuery | Mode | Source field | Source types (observed) | Rule | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| `product_id` | STRING | REQUIRED | `product_id` | string 923,294 | — | Product ID |
| `option_id` | STRING | REQUIRED | `option_id` | string 923,294 | — | Option ID; joins events option[].option_id |
| `value_id` | STRING | NULLABLE | string` | `value_id` | string 888,623, null 34,671 | — | Value ID; null for free-text options such as engraving |
| `part_type` | STRING | NULLABLE | string` | `part_type` | string 809,378, null 113,916 | — | Part, e.g. stone1, alloy |
| `option_type` | STRING | NULLABLE | string` | `option_type` | string 923,294 | — | alloy, stone, engraving_font, ... |
| `option_title` | STRING | NULLABLE | string` | `option_title` | string 923,294 | — | Option title in the store language |
| `option_default_title` | STRING | NULLABLE | string` | `option_default_title` | string 923,294 | — | Option default title |
| `is_require` | BOOL | NULLABLE | boolean` | `is_require` | int 923,294 | `int_as_bool` | Option is mandatory; source 0/1 |
| `sort_order` | STRING | NULLABLE | string` | `sort_order` | string 923,294 | `integer_as_string` | Display order as served |
| `value_sku` | STRING | NULLABLE | string` | `value_sku` | string 814,866, null 108,428 | — | Value token used in product URLs |
| `value_title` | STRING | NULLABLE | string` | `value_title` | string 923,294 | — | Value title |
| `value_default_title` | STRING | NULLABLE | string` | `value_default_title` | string 888,623, null 34,671 | — | Value default title |
| `value_store_title` | STRING | NULLABLE | string` | `value_store_title` | string 905,449, null 17,845 | — | Value title in the store |
| `is_default` | BOOL | NULLABLE | boolean` | `is_default` | bool 895,890, null 18,358, int 9,046 | `int_as_bool` | Default value; source bool or 0 |
| `value_price` | NUMERIC | NULLABLE | decimal(38,9)` | `value_price` | decimal 888,623, null 34,671 | — | Price surcharge of the value |
| `price_type` | STRING | NULLABLE | string` | `price_type` | string 888,623, null 34,671 | — | fixed, percent or abs |
| `run_id` | STRING | REQUIRED | `run_id` | string 923,294 | — | Crawl run ID |
| `crawled_at` | TIMESTAMP | REQUIRED | `crawled_at` | date 923,294 | — | Crawl time (UTC) |

### 5.5 Join keys

| Join | Notes |
| --- | --- |
| `events.ip_hash = ip_locations.ip_hash` | Hash of the canonical IP on both sides. Events with an unparseable IP (6 in the full data) have no match |
| `events.product_id` (or `viewing_product_id`, `cart_products[].product_id`) `= products.product_id` | All STRING; cart IDs were ints in the source |
| `events.option[].option_id / value_id = product_option_values.option_id / value_id` | Also `cart_products[].option[]`. The catalog is from 2026, so some 2020 values no longer exist |

## 6. Export run: files and checks

```bash
export GLAMIRA_PII_HASH_KEY=...   # the project key, from a secret store
uv run export-raw --table all --output-dir /data/exports --export-id 2026-11-22 --workers 3
uv run verify-export /data/exports/2026-11-17
```

Rerunning the same `export-raw` command resumes the export. Committed chunks are verified and skipped, and only uncommitted work is redone. The design, crash cases and retry policy are in the [retry and idempotency decision record](decisions/export_retry_idempotency.md).

| Option | Default | Meaning |
| --- | --- | --- |
| `--table` | required | `events`, `ip_locations`, `products`, `product_option_values` or `all`; repeatable |
| `--output-dir` | required | Export root |
| `--export-id` | required | Files go to `<output-dir>/<export-id>/<table>/`. The same ID with other inputs is refused |
| `--database` | `countly` | Source database |
| `--limit N` | all | First N documents by `_id`, as one chunk; the manifest labels it a non-random sample |
| `--rows-per-file` | 1,000,000 | Rows per Parquet part (written in row groups of 50,000) |
| `--workers` | 1 | Processes exporting chunks in parallel. The output does not depend on it. On the 4-vCPU VM, use 3 and leave a core for `mongod` |

**Output per table**

```text
<output-dir>/<export-id>/<table>/
  _export.json                  identity: source UUID, chunk plan and counts, schema SHA, key fingerprint, versions
  <table>.bq.json               BigQuery schema of the target table; the Parquet schema derives from it
  chunk=<id>/part-00000.parquet Snappy-compressed rows of one chunk, sorted by _id
  chunk=<id>/_SUCCESS.json      chunk commit marker: rows, first and last _id, SHA-256 of each part
  _manifest.json                written last; its presence means "complete"
```

`events` has one chunk per UTC day of the `_id` ObjectId time (65 in the full data); the other tables have one chunk, `all`.

**What the export guarantees**
- **Contract.** Every row passes the contract (sections 2–5), or the export stops at the first violation and that chunk gets no marker.
- **Counts.** The chunk counts add up to the collection count, and each chunk writes exactly as many rows as its range held before and after the read.
- **Atomic commits.** A part becomes visible only after `fsync` and rename, and a chunk only through its marker. An interrupted chunk is redone on the next run.
- **Determinism.** The same inputs give the same bytes, whichever process or worker count wrote them. Each part's SHA-256 is recorded in its chunk marker and in the manifest.

**`_manifest.json`** records the following:
- the export ID and selection, plus the source namespace, UUID and document count;
- per chunk: rows, parts and the attempt that committed it;
- per part: name, rows, bytes and SHA-256;
- `content_sha256`, a hash of all parts that ignores timestamps;
- the conversion counts per source path;
- the schema SHA-256 (of the committed `.bq.json`) and the PII key fingerprint;
- the git SHA, the timestamps, the read/convert/write seconds, the worker count and the wall time.

**`verify-export`** checks a stored export, for example after a move or before an upload. It takes an export directory or a single table directory.

| Check | Default | `--full` |
| --- | --- | --- |
| Inventory both ways: every listed part exists; no extra part, `.tmp` file or unknown chunk | yes | yes |
| Size and SHA-256 of every part, and `content_sha256` | yes | yes |
| `schema_sha256` equals the committed `schemas/raw/<table>.bq.json` and the copy in the export | yes | yes |
| Every part's Parquet footer holds the schema derived from the contract and the manifest's row count | yes | yes |
| Decode every row | no | yes |

The default reads only the footers, a few kilobytes per part: the SHA-256 covers every byte that was checked when the part was written. Use `--full` to test the Parquet library itself, for example after a pyarrow upgrade.

**Exit codes**

| Code | `export-raw` | `verify-export` |
| --- | --- | --- |
| `0` | Success, or already complete | Every table matches |
| `1` | Configuration, contract violation, count or coverage mismatch, changed committed chunk, different identity, MongoDB or file error | First difference found |
| `130` | Interrupted; rerun to resume | — |

**Measured** on the project VM, 2026-11-22, with `--workers 3` ([report](reports/full_export.md)):
- **Volume:** 45,614,951 rows and 4.69 GB of Parquet (9.30 GB as Avro), with 0 violations and no retries.
- **Export:** 42 min 39 s; `events` alone took 39 min 50 s, at 17,336 rows/s. With Avro the export took 52 min 46 s.
- **Verify:** `verify-export` of all four tables took 30 s.

## 7. Loading into BigQuery

```bash
uv run publish-export /data/exports/2026-11-17 --bucket <bucket> --dataset glamira_raw
```

- `publish-export` verifies the export, uploads it to `gs://<bucket>/raw/<table>/export_id=<export-id>/`, and writes `_load.json` last.
- The `bigquery-loader` Cloud Function then loads each table into `glamira_raw.<table>`. It creates the table from the contract on first use, with day partitioning on `events.time_stamp` and clustering by `collection`.
- The load uses a deterministic job ID and `WRITE_TRUNCATE_DATA`, then checks the row count. Repeating any step changes nothing.
- The cloud setup is in the [GCP setup guide](runbooks/gcp_setup.md), and running and checking a load in the [load runbook](runbooks/bigquery_load.md); how the load works is in the [warehouse guide](../src/glamira_pipeline/warehouse/README.md).

**Load options fixed by this contract:**
- Source format PARQUET into the table created from `schemas/raw/<table>.bq.json`; the schema is never taken from the files.
- `enable_list_inference`: otherwise Parquet LIST columns arrive as `list.element` records instead of REPEATED fields.
- `decimal_target_types=NUMERIC`, for the `decimal128(38, 9)` columns.

## 8. Changing the contract

1. Edit the table declaration in `tables.py`, together with its converter rule if a new rule is needed.
2. Run `uv run write-raw-schemas`, then the unit tests. The schema-file test fails until the files are regenerated.
3. Prefer additive changes:
   - **New NULLABLE column, or a new field inside a STRUCT:** append it in BigQuery with `bq update`. Old files stay valid.
   - **REQUIRED → NULLABLE:** allowed in place.
   - **Rename, type change, or NULLABLE → REQUIRED:** needs a new table and a full re-export.
4. Export into a new `--export-id`; an existing export cannot be resumed with a changed contract or converter.
5. Record why in the decision record, and update this page.

## 9. Known limitations

- **CPU-bound export.** Convert (contract checks and HMAC) is 62% of the work since the Parquet writer cut the write stage to a third. Three workers on 4 shared vCPUs, which `mongod` also uses, give less than 3×.
- **Converter changes need a new export ID.** The export identity covers the schema hash, not the converter code.
- **Lost distinctions.** Missing key vs explicit null, `""` vs `[]` in cart options, int vs double `order_id`, bool `false` vs string `"false"`. Each conversion is counted, so the counts are auditable. Details are in the decision record.
- **Different time frames.** Enrichment data is from 2026 (catalog) and 2016 (IP database), while events are from 2020-04-01 to 2020-06-04.
- **Free-text PII.** The pseudonymized columns are covered by the contract, but `current_url`, `referrer_url` and `key_search` are exported as sent and may contain what a visitor typed.
