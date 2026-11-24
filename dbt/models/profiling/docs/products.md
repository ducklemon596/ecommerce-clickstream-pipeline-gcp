{% docs profile_products %}
Profile of `products` on target `prod`, 19557 rows.

| Column | Type | Not null | Distinct | Unique | Min | Max |
| --- | --- | ---: | ---: | :---: | --- | --- |
| `product_id` | string | 100.00% | 19557 | yes |  |  |
| `status` | string | 100.00% | 2 |  |  |  |
| `status_code` | int64 | 100.00% | 2 |  | 200 | 404 |
| `attempts` | int64 | 100.00% | 2 |  | 1 | 2 |
| `error` | string | 0.00% | 0 |  |  |  |
| `name` | string | 97.77% | 19066 |  |  |  |
| `sku` | string | 97.77% | 19121 |  |  |  |
| `attribute_set_id` | string | 97.77% | 4 |  |  |  |
| `attribute_set` | string | 97.77% | 4 |  |  |  |
| `type_id` | string | 97.77% | 4 |  |  |  |
| `product_type` | string | 97.77% | 15 |  |  |  |
| `product_type_value` | string | 97.48% | 14 |  |  |  |
| `collection` | string | 97.77% | 76 |  |  |  |
| `collection_id` | string | 94.45% | 75 |  |  |  |
| `category` | string | 97.77% | 23 |  |  |  |
| `category_name` | string | 97.77% | 19 |  |  |  |
| `gender` | string | 97.77% | 3 |  |  |  |
| `price` | numeric | 97.77% | 3158 |  | 0 | 13217 |
| `min_price` | numeric | 95.31% | 762 |  | -1737 | 13217 |
| `max_price` | numeric | 95.31% | 11805 |  | 0 | 2670673 |
| `min_price_format` | string | 97.77% | 762 |  |  |  |
| `max_price_format` | string | 97.77% | 11805 |  |  |  |
| `full_price` | numeric | 97.77% | 4990 |  | 0 | 1636437 |
| `sale_price` | numeric | 97.77% | 6992 |  | 0 | 1390971.45 |
| `full_price_format` | string | 97.77% | 4990 |  |  |  |
| `sale_price_format` | string | 97.77% | 4540 |  |  |  |
| `currency` | string | 97.77% | 1 |  |  |  |
| `include_tax` | bool | 97.77% | 1 |  |  |  |
| `default_tax` | numeric | 97.77% | 3 |  | 0 | 7 |
| `current_tax` | numeric | 97.77% | 3 |  | 0 | 7 |
| `use_gold_price` | bool | 97.77% | 2 |  |  |  |
| `option_count` | int64 | 97.77% | 17 |  | 0 | 18 |
| `source` | struct | 100.00% |  |  |  |  |
| `run_id` | string | 100.00% | 12 |  |  |  |
| `crawled_at` | timestamp | 100.00% | 19444 |  | 2026-11-12 17:49:01.691+00 | 2026-11-12 20:00:31.756+00 |
{% enddocs %}
