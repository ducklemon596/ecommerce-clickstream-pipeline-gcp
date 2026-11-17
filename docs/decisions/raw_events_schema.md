# Decision record: schema of the raw events table (Avro → BigQuery)

**Status:** proposed, 2026-11-16; personal-data handling decided by the owner the same day. **Scope:** the file format and schema used to export `countly.summary` to GCS and to load it into the BigQuery raw layer.

## Context

- **What is being decided:** the export to GCS uses Avro (decided). The BigQuery raw table gets an explicit schema, and that schema must be identical to the one written into the Avro files.
- **Evidence:**
  - *Types and nullability:* the full-data [schema profile](../reports/schema_profile.md) (41,432,473 documents, 2026-11-14).
  - *Value-level facts:* one read-only `$facet` scan of `countly.summary` on 2026-11-16 (944 s). It checked timestamp range, integrality of `order_id`, bool values, string formats of IDs and positions, and the contents of `cart_products[].option`.
- **The problem to solve:** BigQuery needs one type per column, and the source has 6 fields with mixed types:

  | Field | Types in the source (full data) |
  | --- | --- |
  | `option` | array 22.2 M, object 12.1 M |
  | `order_id` | string 88,540, int 16,116, double 9,963 |
  | `utm_source`, `utm_medium` | bool about 10.85 M, string about 90 K |
  | `recommendation_product_position` | int 20,128, string 18,344 |
  | `cart_products[].option` | array 673,929, string 148,509 |
  | `cart_products[]` IDs | int; the same IDs are strings everywhere else |

## How BigQuery reads Avro (constraints)

Source: [Loading Avro data from Cloud Storage](https://docs.cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro).

| Avro | BigQuery | Consequence for this schema |
| --- | --- | --- |
| `["null", T]` | NULLABLE `T` | Every optional field is written this way |
| Union with more than one non-null type | RECORD with one nullable sub-field per type | Unusable for analysis, so mixed types are resolved **before** writing |
| `array` | REPEATED | Arrays of arrays are not supported; none exist here |
| `record` | RECORD | Each record type needs a unique Avro name |
| `long` with `timestamp-micros` | TIMESTAMP, **only** with `use_avro_logical_types=true` | The load job must set this flag; without it the column arrives as INTEGER |
| Field names | Must match `[A-Za-z_][A-Za-z0-9_]*` | `option.category id` cannot keep its name; it becomes `category_id` |
| Compression | Snappy, DEFLATE or ZSTD blocks, read in parallel | DEFLATE is used: built into `fastavro`, no extra dependency |

**Column modes**
- BigQuery can relax a column from REQUIRED to NULLABLE later, but never the reverse ([managing table schemas](https://docs.cloud.google.com/bigquery/docs/managing-table-schemas)).
- So starting strict is the reversible choice.
- How a load job checks a non-union Avro field against a REQUIRED column must be confirmed with one small test load (see Verification).

## Principles

1. **One wide table for all 27 event types.** Event-specific fields are NULLABLE. The [data dictionary](../data_dictionary.md) shows that each such field belongs to a fixed set of event types, so NULL outside them is expected.
2. **Raw keeps values; only representations change.**
   - Allowed: ObjectId → hex string, int → decimal string, the bool `false` → the string `"false"`.
   - Not done here: parsing (prices, `local_time`), cleaning (cookie fragments in `show_recommendation`), mapping `""` to NULL. These belong in staging.
3. **When a field mixes strings and numbers, the raw column is STRING.** This is lossless: every observed number is integral.
4. **Identifiers are STRING everywhere,** so joins need no casts. Product, option and value IDs are strings at the top level and ints in `cart_products[]`; the raw layer unifies them.
5. **Anything unplanned fails the export:** an unknown field, an unknown `option` key, an unexpected type, or a non-integral ID. Nothing is silently dropped or coerced.
6. **Schema-level choices are based on the full data, not the sample:**
   - *REQUIRED:* a column is REQUIRED only when it was present and non-null in all 41,432,473 documents.
   - *STRUCT vs MAP:* the `option` filter keys are a closed set of 10, so they form a STRUCT rather than a MAP.

## Complex types and why they are needed

Most fields are scalars. Three source fields hold nested data that cannot be flattened into one value per event without losing information. The examples below are real documents from the 100K sample (`data/summary_sample.bson`, sequential, non-random); counts come from the full profile.

### 1. `option` as an array → `option`: ARRAY\<STRUCT\>

**Where:** `view_product_detail` (10.94 M), `select_product_option` (8.84 M), `select_product_option_quality` (2.23 M), `add_to_cart_action` (187,901).

**Why it must be an array:** one event describes a product configured with **several** options at once (metal, stone, …). The number of options varies per product, so fixed columns cannot hold them.

`view_product_detail`, `_id` `5ed8cb2bc671fc36b74653ad`, two elements:

```json
"option": [
  {"option_label": "alloy",   "option_id": "332084", "value_label": "", "value_id": "3279318"},
  {"option_label": "diamond", "option_id": "",       "value_label": "", "value_id": ""}
]
```

**Why each element must be a struct:** the fields of one element belong together. With separate arrays (`option_ids[]`, `value_ids[]`), the pairing of `option_id` 332084 with `value_id` 3279318 would depend on array positions only. Elements also differ in which keys they have: `quality` and `quality_label` only appear in `select_product_option_quality`.

`select_product_option_quality`, `_id` `5ed8cb2a56b3dd3742261b8c`:

```json
"option": [
  {"option_label": "stone/diamonds", "option_id": "57695", "value_label": "diamond-Brillant",
   "value_id": "308213", "quality": "A", "quality_label": "I"}
]
```

In BigQuery, the array is read with `UNNEST`:

```sql
SELECT e._id, o.option_label, o.value_id
FROM raw.events AS e, UNNEST(e.option) AS o
WHERE e.collection = 'view_product_detail'
```

### 2. `option` as an object → `option_filter`: STRUCT

**Where:** `view_listing_page` (11.26 M), `listing_page_recommendation_*` (783,412), `view_all_recommend` (33,664), `view_sorting_relevance` (15,284).

**Why it is a different column:** here `option` is not a list of chosen options. It is the **filter state** of a listing page, a single object with named keys. BigQuery cannot put an array and an object in one column (see Context), so the two shapes are split by type.

**Why a struct, not a map or JSON:** the keys form a closed set of 10 across all 12,092,054 objects.

- `view_listing_page`, `view_sorting_relevance` and the listing recommendation events (12,058,390 objects): `alloy`, `diamond`, `shapediamond`.
- `view_all_recommend` (33,664 objects): `alloy`, `stone`, `price`, `finish`, `pearlcolor`, `Kollektion`, `kollektion_id`, `category id`.
- Within each event type, every key of its set is present in 100% of the objects. The key set depends on the event type, not on the user's selection.

`view_listing_page`, `_id` `5ed8cb2cfeae1f377811165c` (no filter selected, so every value is `""`):

```json
"option": {"alloy": "", "diamond": "", "shapediamond": ""}
```

Becomes `option_filter = {alloy: "", diamond: "", shapediamond: "", stone: NULL, …}`. Keys absent from the event are NULL, and `option_filter.alloy` is queried like an ordinary column, without `UNNEST`.

### 3. `cart_products` → ARRAY\<STRUCT\> with a nested ARRAY\<STRUCT\>

**Where:** `view_shopping_cart` (343,077), `checkout` (88,540), `checkout_success` (26,079): 822,438 cart lines in total.

**Why two levels:** one cart holds **several products**, and each product has **its own options**. This is the only place in the data with an array inside an array element. BigQuery does not allow an array directly inside an array, but an array inside a struct inside an array is valid, which is exactly this shape.

`view_shopping_cart`, `_id` `5ed8cb1b66a4b337241602da`: 5 products, each with 2 options (first two shown):

```json
"cart_products": [
  {"product_id": 97471,
   "option": [{"option_label": "diamond", "option_id": 250775, "value_label": "White Sapphire", "value_id": 2085213},
              {"option_label": "alloy",   "option_id": 250776, "value_label": "Weißgold 585",   "value_id": 2085222}]},
  {"product_id": 98502,
   "option": [{"option_label": "diamond", "option_id": 190114, "value_label": "Diamond",     "value_id": 1511580},
              {"option_label": "alloy",   "option_id": 190115, "value_label": "Rotgold 585", "value_id": 1511600}]},
  …
]
```

**Two irregularities the schema has to absorb:**

- The IDs are **ints** here, while the same IDs are strings in `option[]` and `product_id`. They become strings, so `cart_products[].product_id` joins `product_id` without a cast.
- `option` is sometimes the string `""` instead of an array (148,509 lines). `checkout_success`, `_id` `5ed8c8d02c94b7370c160266`:

  ```json
  "cart_products": [{"product_id": 97507, "amount": 1, "price": "55,00", "currency": "€", "option": ""}]
  ```

  `""` becomes `[]`: the product has no options. A REPEATED field cannot hold a string.

The fields of a line depend on the event: `view_shopping_cart` lines have `product_id` and `option` only, `checkout` adds `amount`, and only `checkout_success` also has `price` and `currency`. So everything except the arrays is NULLABLE inside a line.

Reading both levels:

```sql
SELECT e._id, line.product_id, line.amount, opt.option_label, opt.value_label
FROM raw.events AS e, UNNEST(e.cart_products) AS line
LEFT JOIN UNNEST(line.option) AS opt
WHERE e.collection = 'checkout_success'
```

### Not complex in the source, but typed in Avro

`time_stamp` is a plain int of Unix seconds (`1591266092` for the first example). It is written as an Avro `long` with the logical type `timestamp-micros` (`1591266092000000`) so that BigQuery creates a TIMESTAMP column, which partitioning needs.

## Proposed schema: `raw.events`

**Table settings**
- Partitioned by `DATE(time_stamp)`. The data spans 2020-04-01 to 2020-06-04: 65 daily partitions.
- Clustered by `collection`.

### Top-level columns

| Column | BigQuery type | Mode | Source → raw |
| --- | --- | --- | --- |
| `_id` | STRING | REQUIRED | ObjectId → 24-char hex |
| `collection` | STRING | REQUIRED | as is (event type) |
| `time_stamp` | TIMESTAMP | REQUIRED | int Unix seconds → micros (Avro `timestamp-micros`). Range 1585699201–1591266092 |
| `api_version` | STRING | REQUIRED | as is (always `"1.0"`) |
| `store_id` | STRING | REQUIRED | as is (always digits) |
| `current_url`, `referrer_url` | STRING | REQUIRED | as is; `referrer_url` is `""` for direct entries |
| `ip`, `user_id_db`, `user_agent` | STRING | REQUIRED | as is. **Sensitive**; `ip` is needed to join `ip_locations` |
| `device_id_hash` | STRING | REQUIRED | HMAC-SHA256 of `device_id`, 64 hex chars. The raw value is not exported |
| `email_hash` | STRING | NULLABLE | HMAC-SHA256 of the trimmed, lower-cased `email_address`; `""` and null kept as they are (95.20% empty, 397 nulls). The raw value is not exported |
| `local_time` | STRING | NULLABLE | as is. 12.6 M values do not match `YYYY-MM-DD HH:MM:SS`; the most frequent ones are not zero-padded (`2020-05-20 3:6:40`). Parse in staging |
| `resolution` | STRING | NULLABLE | as is |
| `show_recommendation` | STRING | NULLABLE | as is: `"true"` 33.59 M, `"false"` 79 K, null 7.77 M, and about 150 cookie fragments |
| `product_id`, `viewing_product_id`, `recommendation_product_id` | STRING | NULLABLE | as is (always digits) |
| `recommendation_clicked_position` | INT64 | NULLABLE | as is. Every non-null value is `0` |
| `recommendation_product_position` | STRING | NULLABLE | int (1–14) → decimal string; strings (`"1"`…, `""`) kept |
| `recommendation` | BOOL | NULLABLE | as is (only `false` or null) |
| `utm_source`, `utm_medium` | STRING | NULLABLE | bool `false` → `"false"`, the same convention as `show_recommendation`; campaign names kept (`criteo`, `recommendation`, …). `true` never occurs |
| `cat_id`, `collect_id`, `key_search` | STRING | NULLABLE | as is |
| `price`, `currency` | STRING | NULLABLE | as is: locale-formatted price, currency symbol |
| `is_paypal` | BOOL | NULLABLE | as is (only `true` or null) |
| `order_id` | STRING | NULLABLE | int / integral double → decimal string (`2501001205.0` → `"2501001205"`, max 10,000,000,002); `""` in `checkout` kept |
| `option` | ARRAY\<STRUCT> | REPEATED | the **array** form of `option` (product events). Empty for other events |
| `option_filter` | STRUCT | NULLABLE | the **object** form of `option` (listing, sorting and `view_all_recommend` events). Null for other events |
| `cart_products` | ARRAY\<STRUCT> | REPEATED | `view_shopping_cart`, `checkout`, `checkout_success`. Empty for other events |

### Nested fields

All nested fields are NULLABLE STRING unless stated otherwise.

**`option[]`**
- Fields: `option_label`, `option_id`, `value_label`, `value_id`, `quality`, `quality_label`.
- All are strings in the source, and each is missing in some elements.
- `value_id` holds 97 non-digit values.

**`option_filter`**
- Fields: `alloy`, `diamond`, `shapediamond`, `stone`, `price`, `finish`, `pearlcolor`, `kollektion`, `kollektion_id`, `category_id`.
- Two keys are renamed: `Kollektion` → `kollektion` (BigQuery column names are case-insensitive), and `category id` → `category_id` (the space is invalid in Avro).

**`cart_products[]`**
- `product_id`: int → string.
- `amount`: INT64. Observed range −1 to 9,999.
- `price`, `currency`: as is.
- `option`: REPEATED STRUCT of `option_id` (int → string), `option_label`, `value_id` (int → string), `value_label`.
  - The source sometimes stores `""` instead of an array: 148,509 lines, and `""` is the only string ever seen there.
  - `""` becomes `[]`.

## Full type mapping: source → Avro → BigQuery

Every column of `raw.events`. *Source types* are BSON types counted over all 41,432,473 documents ([schema profile](../reports/schema_profile.md)). Avro types are shown in short form; `OptionItem`, `OptionFilter`, `CartProduct` and `CartOption` are the named Avro records defined at their first use.

Avro notation used below:
- `["null", T]` with `"default": null` → NULLABLE.
- `{"type": "array", "items": T}` with `"default": []` → REPEATED.
- `ts-micros` = `{"type": "long", "logicalType": "timestamp-micros"}`.

### Top level (`Event`)

| Column | Source field | Source types (full data) | Avro type | BigQuery type | Mode |
| --- | --- | --- | --- | --- | --- |
| `_id` | `_id` | objectId 41.43 M | `string` | STRING | REQUIRED |
| `collection` | `collection` | string 41.43 M | `string` | STRING | REQUIRED |
| `time_stamp` | `time_stamp` | int 41.43 M | `ts-micros` | TIMESTAMP | REQUIRED |
| `api_version` | `api_version` | string 41.43 M | `string` | STRING | REQUIRED |
| `store_id` | `store_id` | string 41.43 M | `string` | STRING | REQUIRED |
| `current_url` | `current_url` | string 41.43 M | `string` | STRING | REQUIRED |
| `referrer_url` | `referrer_url` | string 41.43 M | `string` | STRING | REQUIRED |
| `ip` | `ip` | string 41.43 M | `string` | STRING | REQUIRED |
| `device_id_hash` | `device_id` | string 41.43 M | `string` | STRING | REQUIRED |
| `user_id_db` | `user_id_db` | string 41.43 M | `string` | STRING | REQUIRED |
| `user_agent` | `user_agent` | string 41.43 M | `string` | STRING | REQUIRED |
| `local_time` | `local_time` | string 41.43 M, null 240 | `["null","string"]` | STRING | NULLABLE |
| `resolution` | `resolution` | string 41.43 M, null 240 | `["null","string"]` | STRING | NULLABLE |
| `email_hash` | `email_address` | string 41.43 M, null 397 | `["null","string"]` | STRING | NULLABLE |
| `show_recommendation` | `show_recommendation` | string 33.67 M, null 7.77 M | `["null","string"]` | STRING | NULLABLE |
| `product_id` | `product_id` | string 22.24 M | `["null","string"]` | STRING | NULLABLE |
| `viewing_product_id` | `viewing_product_id` | string 1.99 M | `["null","string"]` | STRING | NULLABLE |
| `recommendation_product_id` | `recommendation_product_id` | string 217,700, null 25,596 | `["null","string"]` | STRING | NULLABLE |
| `recommendation_clicked_position` | `recommendation_clicked_position` | int 179,226, null 25,547 | `["null","long"]` | INT64 | NULLABLE |
| `recommendation_product_position` | `recommendation_product_position` | **int 20,128, string 18,344**, null 51 | `["null","string"]` | STRING | NULLABLE |
| `recommendation` | `recommendation` | bool 10.94 M, null 68 | `["null","boolean"]` | BOOL | NULLABLE |
| `utm_source` | `utm_source` | **bool 10.86 M, string 88,179**, null 68 | `["null","string"]` | STRING | NULLABLE |
| `utm_medium` | `utm_medium` | **bool 10.85 M, string 90,721**, null 68 | `["null","string"]` | STRING | NULLABLE |
| `cat_id` | `cat_id` | null 12.04 M, string 258 | `["null","string"]` | STRING | NULLABLE |
| `collect_id` | `collect_id` | string 12.04 M | `["null","string"]` | STRING | NULLABLE |
| `key_search` | `key_search` | null 163,108, string 75,200 | `["null","string"]` | STRING | NULLABLE |
| `price` | `price` | string 186,590, null 1,311 | `["null","string"]` | STRING | NULLABLE |
| `currency` | `currency` | string 186,590, null 1,311 | `["null","string"]` | STRING | NULLABLE |
| `is_paypal` | `is_paypal` | null 186,592, bool 1,309 | `["null","boolean"]` | BOOL | NULLABLE |
| `order_id` | `order_id` | **string 88,540, int 16,116, double 9,963** | `["null","string"]` | STRING | NULLABLE |
| `option` | `option` when array | **array 22.21 M** (object 12.09 M) | `array<OptionItem>` | RECORD | REPEATED |
| `option_filter` | `option` when object | **object 12.09 M** (array 22.21 M) | `["null", OptionFilter]` | RECORD | NULLABLE |
| `cart_products` | `cart_products` | array 457,696 | `array<CartProduct>` | RECORD | REPEATED |

Bold source types are the mixed ones; the rules that resolve them are in the column table above.

### `OptionItem` (elements of `option`)

| Field | Source types | Avro type | BigQuery type | Mode |
| --- | --- | --- | --- | --- |
| `option_label` | string 33.46 M | `["null","string"]` | STRING | NULLABLE |
| `option_id` | string 33.28 M | `["null","string"]` | STRING | NULLABLE |
| `value_label` | string 33.46 M | `["null","string"]` | STRING | NULLABLE |
| `value_id` | string 33.39 M | `["null","string"]` | STRING | NULLABLE |
| `quality` | string 2.23 M | `["null","string"]` | STRING | NULLABLE |
| `quality_label` | string 1.93 M | `["null","string"]` | STRING | NULLABLE |

33,573,308 elements in total; each field is missing in some, hence NULLABLE.

### `OptionFilter` (`option_filter`)

| Field | Source key | Source types | Avro type | BigQuery type | Mode |
| --- | --- | --- | --- | --- | --- |
| `alloy` | `alloy` | string 12.09 M | `["null","string"]` | STRING | NULLABLE |
| `diamond` | `diamond` | string 12.06 M | `["null","string"]` | STRING | NULLABLE |
| `shapediamond` | `shapediamond` | string 12.06 M | `["null","string"]` | STRING | NULLABLE |
| `stone` | `stone` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `price` | `price` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `finish` | `finish` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `pearlcolor` | `pearlcolor` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `kollektion` | `Kollektion` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `kollektion_id` | `kollektion_id` | string 33,664 | `["null","string"]` | STRING | NULLABLE |
| `category_id` | `category id` | string 33,664 | `["null","string"]` | STRING | NULLABLE |

### `CartProduct` (elements of `cart_products`)

| Field | Source types | Avro type | BigQuery type | Mode |
| --- | --- | --- | --- | --- |
| `product_id` | int 822,438 | `["null","string"]` | STRING | NULLABLE |
| `amount` | int 160,181 | `["null","long"]` | INT64 | NULLABLE |
| `price` | string 35,065 | `["null","string"]` | STRING | NULLABLE |
| `currency` | string 35,065 | `["null","string"]` | STRING | NULLABLE |
| `option` | **array 673,929, string `""` 148,509** | `array<CartOption>` | RECORD | REPEATED |

### `CartOption` (elements of `cart_products[].option`)

| Field | Source types | Avro type | BigQuery type | Mode |
| --- | --- | --- | --- | --- |
| `option_id` | int 1.13 M | `["null","string"]` | STRING | NULLABLE |
| `option_label` | string 1.13 M | `["null","string"]` | STRING | NULLABLE |
| `value_id` | int 1.13 M | `["null","string"]` | STRING | NULLABLE |
| `value_label` | string 1.13 M | `["null","string"]` | STRING | NULLABLE |

**Totals:** 33 top-level columns (11 REQUIRED, 19 NULLABLE scalars, 3 complex) and 25 nested fields in 4 record types. Both the Avro schema and the BigQuery JSON schema are generated from one field list (see Verification). This table was checked against that list; the exporter will commit it to the repository.

## What the raw layer cannot tell apart

| Lost distinction | Why | Size |
| --- | --- | --- |
| Missing key vs explicit null | BigQuery has a single NULL | e.g. `recommendation_product_id`: 25,596 nulls |
| `cart_products[].option` `""` vs `[]` | A REPEATED field cannot hold a string | 148,509 lines, all counted at export |
| `order_id` int vs double | Both are written as one decimal string | 9,963 doubles, all integral |
| `utm_*` bool `false` vs a string `"false"` | Both are written as `"false"` | No string `"false"` was seen among the campaign values |

Each conversion is counted by the exporter and recorded with the export run, so all of this stays auditable.

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Keep the mixed types as Avro unions | BigQuery would produce a RECORD per union, such as `order_id.long` and `order_id.string`, and every query would need `COALESCE` |
| A `JSON` column for the whole document or for `option` | No type contract at the raw layer, slower queries, and the mixed-type problem only moves to dbt |
| `order_id` and positions as INT64 | `""` would have to become NULL, which is a value change. The cast belongs in staging |
| `option_filter` as a MAP, i.e. `ARRAY<STRUCT<key, value>>` (reviewed by the owner, 2026-11-17: STRUCT kept) | The 10 keys form two fixed sets, one per event type, each present in 100% of its objects. A STRUCT is read as plain columns, scans only the sub-column queried, and fails the export on an unknown key instead of hiding drift. Sparse NULLs cost almost nothing in BigQuery, and a new key is an additive NULLABLE field. The only loss is the original key names (`Kollektion`, `category id`), which the mapping table records |
| One table per event type (27 tables) | Most analyses span event types (funnel, sessions), and the shared 15 columns would be duplicated |

## Verification so far

- **Generated from one definition.** The Avro schema and the BigQuery JSON schema both come from a single field list, so they cannot drift.
- **Sample check:** the 100K sequential sample (non-random) converted with **0 violations** and was written with `fastavro` (`validator=True`, `strict=True`, deflate).
  - It read back as 100,000 rows, 18.7 MB with the hashes (hex hashes compress worse than the raw values), which extrapolates to about 8 GB for the full data.
  - After hashing: 100,000 / 100,000 device hashes and 7,557 email hashes are 64 hex characters, 92,443 emails stay `""`, and no raw email or device ID appears in the file.
  - Conversions applied: 27,350 / 27,340 bool → string in `utm_*`, 26,066 objects → `option_filter`, 101 `order_id` int/double → string, 1,740 cart product IDs, 43 `""` → `[]`.

**Still to verify**
- **Full-data conversion:** run the converter on all 41.4 M documents. This happens at the export step; every planned rule is backed by the full profile, but only a full pass proves there is no unplanned case.
- **One test load into BigQuery:** a small Avro file with `use_avro_logical_types=true` into a table created from the BigQuery JSON schema, to confirm:
  - TIMESTAMP and REQUIRED behaviour;
  - the empty-array and null-STRUCT representation;
  - partitioning.

## Personal data

**Decision (owner, 2026-11-16):** `email_address` and `device_id` are pseudonymized at export. Only the hashes leave MongoDB.

| Choice | Reason |
| --- | --- |
| **HMAC-SHA256 with a secret key**, not plain SHA-256 | Emails are guessable: a plain hash can be reversed by hashing a list of known addresses. Without the key, the HMAC cannot be recomputed |
| **One key for every export run** | The same person gets the same hash across files and reruns, so distinct-customer and repeat-visit analysis still work |
| **Key from the environment** (`GLAMIRA_PII_HASH_KEY`, 32 random bytes as hex) | Never committed or stored with the data. It must be kept, because losing it means new exports no longer match old hashes |
| **Email trimmed and lower-cased before hashing** | `A@x.com` and `a@x.com` are the same customer |
| **`device_id` hashed exactly as stored** | It is an opaque identifier, so there is nothing to normalize |
| **`""` and null not hashed** | A hash of the empty string would look like a real identifier; emptiness stays visible |

**Still exported as is:**
- *Sensitive columns:* `ip` (needed for the geolocation join), `user_id_db`, `user_agent`, and free text in `key_search`.
- *How to protect them:* keep the raw dataset restricted. Column-level policy tags can be added later without reloading.

## Open questions for the owner

1. **Date range vs project description.** The data covers **2020-04-01 to 2020-06-04**, while the archive name says October–November 2019. The README now states the measured range; the business questions on time trends should use it.
