# Raw layer in BigQuery: data profile

**Observed:** 2026-11-24 (UTC), on `glamira_raw` after the Parquet load of 2026-11-22.
**Code:** [`dbt/models/profiling/`](../../dbt/models/profiling/), run as described in the [dbt README](../../dbt/README.md#profiling-the-raw-layer).

**Outcome:** the four raw tables (45,614,951 rows) were profiled column by column in BigQuery:
- 5 dbt models, built in 12 s, **23.1 GiB scanned** (about $0.14 on demand, or inside the 1 TB free tier);
- every number that could be compared with the MongoDB profiles of the source matches, so the export and load changed no value;
- the profile shows what the dbt staging layer must handle: 6 constant columns, a dirty boolean flag, negative prices, and cart lines that mostly lack a price.

The full per-column tables are the [profile docs blocks](../../dbt/models/profiling/docs/), shown in `dbt docs` under each source. This report summarizes them. Column meanings are in the [raw layer contract](../raw_layer_contract.md) and the [data dictionary](../data_dictionary.md).

## 1. Method

| Item | Choice |
| --- | --- |
| Tool | dbt with [dbt_profiler](https://hub.getdbt.com/data-mie/dbt_profiler/latest/) 1.0.0, on dbt-core 1.12.7 and dbt-bigquery 1.12.4 |
| Measures | Per column: not-null proportion, distinct count, uniqueness; min and max for numbers and times; avg, median and standard deviation for numbers |
| Arrays | dbt_profiler would run `count(distinct)` on an ARRAY column, which BigQuery rejects. `events.option` and `events.cart_products` are profiled by a separate model, `profile_events_arrays`: array lengths, then the not-null proportion and distinct count of each element field |
| Output | One table per source in `glamira_dbt_profiling`, then a docs block per table for `dbt docs` |
| Run | Developed on the 100K-row sample (55 MiB scanned), then run once on prod. Every query is capped by `maximum_bytes_billed` |
| Why dbt | The sources, their descriptions and the profiles now live in the dbt project that the staging models will use, and the findings below become dbt tests there |

Distinct counts are exact (`count(distinct)`). The profile tables are snapshots: they change only when the models are rebuilt.

**Cost per model**

| Model | Rows profiled | Bytes scanned |
| --- | ---: | ---: |
| `profile_events` | 41,432,473 | 21.4 GiB |
| `profile_events_arrays` | 41,432,473 | 974 MiB |
| `profile_ip_locations` | 3,239,627 | 577 MiB |
| `profile_product_option_values` | 923,294 | 170 MiB |
| `profile_products` | 19,557 | 8 MiB |
| **Total** | | **23.1 GiB** |

dbt_profiler writes one `SELECT` per column, joined by `UNION ALL`. BigQuery still billed each column once: the scan equals the size of the columns read.

## 2. Tables and keys

| Table | Rows | Columns | Key | Unique |
| --- | ---: | ---: | --- | :---: |
| `events` | 41,432,473 | 33 (2 ARRAY, 1 STRUCT) | `_id` | ✓ |
| `ip_locations` | 3,239,627 | 8 | `ip_hash` | ✓ |
| `products` | 19,557 | 36 (1 STRUCT) | `product_id` | ✓ |
| `product_option_values` | 923,294 | 18 | `product_id`, `option_id`, `value_id` | — |

| Relationship | Profile | Measured |
| --- | --- | --- |
| `events.ip_hash` → `ip_locations.ip_hash` | 3,239,628 distinct hashes in events, 3,239,627 in `ip_locations` | The extra hash belongs to the 6 events with an unparseable IP, the case the contract names. All other events match |
| `events.product_id` → `products.product_id` | 19,417 distinct in events, 19,557 products | `products` also holds the IDs from `viewing_product_id` and cart lines ([product IDs](product_ids_distinct.md)) |
| `events.option[].option_id` → `product_option_values.option_id` | 40,341 distinct in events, 170,256 in the catalog | Coverage was measured in the [load report](bigquery_load.md#42-verification) |

## 3. Profile of `events`

The 15 columns common to all 27 event types are complete: `_id`, `collection`, `time_stamp`, `api_version`, `store_id`, the URLs, the four hashes and `user_agent` are 100% not null. `local_time`, `resolution` and `email_hash` miss 0.001%.

The other columns belong to some event types only, so their not-null rate is the share of those types, not missing data ([data dictionary](../data_dictionary.md)):

| Column | Not null | Distinct | Set by |
| --- | ---: | ---: | --- |
| `show_recommendation` | 81.25% | 142 | Most event types |
| `product_id` | 53.68% | 19,417 | Product events |
| `option` (array not empty) | 53.60% | — | Product events |
| `option_filter` | 29.19% | — | Listing pages |
| `collect_id` | 29.07% | 62 | Listing pages |
| `utm_source`, `utm_medium`, `recommendation` | 26.42% | 7 / 82 / 1 | `view_product_detail` |
| `viewing_product_id` | 4.80% | 16,981 | Recommendation events |
| `cart_products` (array not empty) | 0.88% | — | Cart and checkout events |
| `recommendation_product_id` | 0.53% | 9,695 | Recommendation clicks |
| `price`, `currency` | 0.45% | 28,611 / 85 | `add_to_cart_action` |
| `recommendation_clicked_position` | 0.43% | 1 | Recommendation clicks |
| `order_id` | 0.28% | 26,032 | `checkout_success` |
| `key_search` | 0.18% | 31,946 | `search_box_action` |
| `recommendation_product_position` | 0.09% | 165 | Recommendation clicks |
| `is_paypal` | 0.003% | 1 | PayPal checkout |
| `cat_id` | 0.001% | 37 | Rare listing pages |

`time_stamp` spans 2020-04-01 00:00:01 → 2020-06-04 10:21:32 UTC with 5,492,095 distinct seconds.

**Array fields**

| Array | Rows not empty | Length max / mean | Elements | Element fields |
| --- | ---: | ---: | ---: | --- |
| `option` | 22,208,495 (53.60%) | 4 / 0.81 | 33,573,308 | `option_id` 99.14% not null (40,341 distinct), `value_id` 99.44% (266,736), labels 99.67%; `quality` 6.65%, `quality_label` 5.75% |
| `cart_products` | 364,982 (0.88%) | 31 / 0.02 | 822,438 | `product_id` 100% (10,922 distinct); `amount` 19.48%; `price` and `currency` **4.26%** |

## 4. Profile of the enrichment tables

| Table | Findings |
| --- | --- |
| `ip_locations` | `status`: resolved 3,201,386, no_match 36,471, unsupported_ipv6 1,474, not_public 296. Country is set on 98.82% of IPs, region and city on 98.76%; 219 countries, 49,340 cities. One IP2Location database (`database_id`) |
| `products` | `status`: success or not_found (HTTP 200 or 404); `error` is always null. Attributes are set on 97.77% of products, the success rows. 15 product types, 76 collections, one currency, one tax mode |
| `product_option_values` | 18,965 products, 170,256 options, 16 option types. `value_id` is null on 3.76%, the free-text options such as engraving |

## 5. Cross-check with the MongoDB source

The same quantities were measured on `countly.summary` and the enrichment collections before the export ([data dictionary](../data_dictionary.md), [contract](../raw_layer_contract.md)):

| Quantity | MongoDB | BigQuery | |
| --- | ---: | ---: | :---: |
| Events, event types | 41,432,473 / 27 | 41,432,473 / 27 | ✓ |
| `show_recommendation` null | 7,766,848 | 7,766,848 | ✓ |
| `recommendation_product_position` set (int 20,128 + string 18,344) | 38,472 | 38,472 | ✓ |
| `cart_products[].price` set | 35,065 | 35,065 | ✓ |
| `products.min_price` set | 18,639 | 18,639 | ✓ |
| `products.price` / `value_price` set | 19,120 / 888,623 | 19,120 / 888,623 | ✓ |
| Unique IPs, geolocated share | 3,239,627 / 98.82% | 3,239,627 / 98.82% | ✓ |

Together with the row and day counts of the [load report](bigquery_load.md#42-verification), this shows that the export and load kept every value, including NULLs and empty strings, distinct.

## 6. Findings and what dbt staging must do

| # | Finding | Evidence | Staging rule (Project 07) |
| --- | --- | --- | --- |
| 1 | **Constant columns** | `api_version`, `recommendation_clicked_position` (always 0), `recommendation` (always false), `is_paypal` (always true); `products.currency`, `include_tax` | Drop them, or keep them with an `accepted_values` test so a change is noticed |
| 2 | **`show_recommendation` is a dirty flag** | 33,586,437 `true`, 79,029 `false`, 7,766,848 NULL, and 159 rows with 140 malformed values such as `true; _gcl_au=…` | Map to BOOL; other values → NULL; `accepted_values` on the cleaned column |
| 3 | **Cart lines mostly lack prices** | `price` and `currency` on 4.26% of 822,438 lines, `amount` on 19.48% | Revenue comes from `checkout_success` lines only, as the data dictionary states |
| 4 | **Negative prices** | 2 products with `min_price` < 0 (down to −1,737); 8,198 option values with `value_price` < 0 (down to −44) | Option surcharges can be discounts: keep them. Flag negative `min_price` as invalid |
| 5 | **Prices as text in events** | `price` (28,611 distinct) and `cart_products[].price` are locale-formatted strings | Parse to NUMERIC per locale; test the parse rate |
| 6 | **`recommendation_product_position` mixes forms** | 165 distinct strings, int and text in the source | `SAFE_CAST` to INT64, empty → NULL |
| 7 | **Empty strings stand for absence** | `user_id_hash` and `email_hash` are `''` for anonymous visits; `order_id` is `''` in `checkout` | `NULLIF(col, '')` |
| 8 | **Keys hold** | `_id`, `ip_hash`, `product_id` unique; one unmatched IP hash | `unique`, `not_null` and `relationships` tests, with the 6 unparseable IPs as a documented exception |

## 7. Limitations

- **One snapshot.** The profile reflects the export of 2026-11-22. Rebuild the profiling models after a new load.
- **Event-type sparsity is not split here.** The not-null rates above are over all events. The rates per event type were measured on MongoDB in the [schema profile](schema_profile.md); the staging tests will check them per `collection`.
- **Nested STRUCT fields.** `option_filter` and `products.source` are profiled as a whole (not-null rate), not field by field. `cart_products[].option` is not profiled.
- **Datasets created.** The run created `glamira_dbt_sample_profiling` and `glamira_dbt_profiling`. They hold only the small profile tables (under 1 MB).
