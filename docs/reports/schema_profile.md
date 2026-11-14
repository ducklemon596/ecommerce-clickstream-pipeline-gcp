# Schema profile — `countly.summary`

- Observed (UTC): 2026-11-14T21:23:57+00:00.
- Method: Full scan: every document read once with an unsorted `find({})` cursor.
- Documents profiled: **41,432,473** of 41,432,473 requested; collection estimate 41,432,473.
- Git commit: `a8e95c10e6fb86a9042a8b24d9f30cee39ff02c0`.

Rates are relative to **containers**: events of the type for a top-level field, array elements for `a[]`, object elements of `a[]` for `a[].b`. *Missing* = key absent; *Null* = explicit BSON null; *Empty* = empty/whitespace string, empty array or empty object. Present includes null and empty values. Event types are labelled by `collection`; missing or non-string values are `<missing>`.

| Event type | Events | Share | Paths |
|---|---:|---:|---:|
| `view_listing_page` | 11,259,694 | 27.18% | 21 |
| `view_product_detail` | 10,944,427 | 26.42% | 25 |
| `select_product_option` | 8,844,342 | 21.35% | 22 |
| `select_product_option_quality` | 2,231,825 | 5.39% | 24 |
| `view_static_page` | 1,451,565 | 3.50% | 15 |
| `view_landing_page` | 1,434,230 | 3.46% | 15 |
| `product_detail_recommendation_visible` | 1,302,362 | 3.14% | 16 |
| `view_home_page` | 1,053,420 | 2.54% | 15 |
| `listing_page_recommendation_visible` | 718,048 | 1.73% | 21 |
| `product_detail_recommendation_noticed` | 490,780 | 1.18% | 16 |
| `view_shopping_cart` | 343,077 | 0.83% | 24 |
| `landing_page_recommendation_visible` | 314,999 | 0.76% | 15 |
| `search_box_action` | 238,308 | 0.58% | 16 |
| `add_to_cart_action` | 187,901 | 0.45% | 25 |
| `product_detail_recommendation_clicked` | 179,228 | 0.43% | 18 |
| `view_my_account` | 112,066 | 0.27% | 15 |
| `checkout` | 88,540 | 0.21% | 26 |
| `landing_page_recommendation_noticed` | 58,186 | 0.14% | 15 |
| `listing_page_recommendation_noticed` | 39,819 | 0.10% | 21 |
| `view_all_recommend` | 33,664 | 0.08% | 25 |
| `checkout_success` | 26,079 | 0.06% | 28 |
| `listing_page_recommendation_clicked` | 25,545 | 0.06% | 23 |
| `landing_page_recommendation_clicked` | 20,128 | 0.05% | 17 |
| `product_view_all_recommend_clicked` | 16,682 | 0.04% | 18 |
| `view_sorting_relevance` | 15,284 | 0.04% | 19 |
| `sorting_relevance_click_action` | 1,713 | 0.0041% | 17 |
| `back_to_product_action` | 561 | 0.0014% | 16 |

## `view_listing_page`

11,259,694 events (27.18% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 11,259,694 |
| `api_version` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `cat_id` | 11,259,694 | 100.00% | 0.00% | 99.9977% | 0.00% | null 11,259,438, string 256 |
| `collect_id` | 11,259,694 | 100.00% | 0.00% | 0.00% | 77.18% | string 11,259,694 |
| `collection` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `current_url` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `device_id` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `email_address` | 11,259,694 | 100.00% | 0.00% | 0.0015% | 97.07% | string 11,259,527, null 167 |
| `ip` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `local_time` | 11,259,694 | 100.00% | 0.00% | 0.0001% | 0.00% | string 11,259,687, null 7 |
| `option` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | object 11,259,694 |
| `option.alloy` | 11,259,694 | 100.00% | 0.00% | 0.00% | 76.16% | string 11,259,694 |
| `option.diamond` | 11,259,694 | 100.00% | 0.00% | 0.00% | 70.17% | string 11,259,694 |
| `option.shapediamond` | 11,259,694 | 100.00% | 0.00% | 0.00% | 96.73% | string 11,259,694 |
| `referrer_url` | 11,259,694 | 100.00% | 0.00% | 0.00% | 3.43% | string 11,259,694 |
| `resolution` | 11,259,694 | 100.00% | 0.00% | 0.0001% | 0.00% | string 11,259,687, null 7 |
| `show_recommendation` | 11,259,694 | 100.00% | 0.00% | 0.11% | 0.00% | string 11,247,641, null 12,053 |
| `store_id` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | string 11,259,694 |
| `time_stamp` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.00% | int 11,259,694 |
| `user_agent` | 11,259,694 | 100.00% | 0.00% | 0.00% | 0.0000% | string 11,259,694 |
| `user_id_db` | 11,259,694 | 100.00% | 0.00% | 0.00% | 97.07% | string 11,259,694 |

## `view_product_detail`

10,944,427 events (26.42% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 10,944,427 |
| `api_version` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `collection` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `current_url` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `device_id` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `email_address` | 10,944,427 | 100.00% | 0.00% | 0.0006% | 97.29% | string 10,944,360, null 67 |
| `ip` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `local_time` | 10,944,427 | 100.00% | 0.00% | 0.0021% | 0.00% | string 10,944,194, null 233 |
| `option` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | array 10,944,427 |
| `option[]` | 21,888,854 | 100.00% | 0.00% | 0.00% | 0.00% | object 21,888,854 |
| `option[].option_id` | 21,888,854 | 100.00% | 0.00% | 0.00% | 16.88% | string 21,888,854 |
| `option[].option_label` | 21,888,854 | 100.00% | 0.00% | 0.00% | 0.00% | string 21,888,854 |
| `option[].value_id` | 21,888,854 | 100.00% | 0.00% | 0.00% | 16.89% | string 21,888,854 |
| `option[].value_label` | 21,888,854 | 100.00% | 0.00% | 0.00% | 99.9999% | string 21,888,854 |
| `product_id` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `recommendation` | 10,944,427 | 100.00% | 0.00% | 0.0006% | 0.00% | bool 10,944,359, null 68 |
| `referrer_url` | 10,944,427 | 100.00% | 0.00% | 0.00% | 11.49% | string 10,944,427 |
| `resolution` | 10,944,427 | 100.00% | 0.00% | 0.0021% | 0.00% | string 10,944,194, null 233 |
| `show_recommendation` | 10,944,427 | 100.00% | 0.00% | 50.09% | 0.0000% | null 5,482,437, string 5,461,990 |
| `store_id` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `time_stamp` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | int 10,944,427 |
| `user_agent` | 10,944,427 | 100.00% | 0.00% | 0.00% | 0.00% | string 10,944,427 |
| `user_id_db` | 10,944,427 | 100.00% | 0.00% | 0.00% | 97.29% | string 10,944,427 |
| `utm_medium` | 10,944,427 | 100.00% | 0.00% | 0.0006% | 0.0000% | bool 10,853,638, string 90,721, null 68 |
| `utm_source` | 10,944,427 | 100.00% | 0.00% | 0.0006% | 0.0000% | bool 10,856,180, string 88,179, null 68 |

## `select_product_option`

8,844,342 events (21.35% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 8,844,342 |
| `api_version` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `collection` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `current_url` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `device_id` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `email_address` | 8,844,342 | 100.00% | 0.00% | 0.0001% | 96.27% | string 8,844,337, null 5 |
| `ip` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `local_time` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `option` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | array 8,844,342 |
| `option[]` | 9,076,827 | 100.00% | 0.00% | 0.00% | 0.00% | object 9,076,827 |
| `option[].option_id` | 9,076,827 | 100.00% | 0.00% | 0.00% | 1.99% | string 9,076,827 |
| `option[].option_label` | 9,076,827 | 100.00% | 0.00% | 0.00% | 0.00% | string 9,076,827 |
| `option[].value_id` | 9,076,827 | 99.15% | 0.85% | 0.00% | 1.14% | string 8,999,324 |
| `option[].value_label` | 9,076,827 | 99.9988% | 0.0012% | 0.00% | 1.84% | string 9,076,717 |
| `product_id` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `referrer_url` | 8,844,342 | 100.00% | 0.00% | 0.00% | 10.50% | string 8,844,342 |
| `resolution` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `show_recommendation` | 8,844,342 | 100.00% | 0.00% | 17.50% | 0.00% | string 7,296,987, null 1,547,355 |
| `store_id` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `time_stamp` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | int 8,844,342 |
| `user_agent` | 8,844,342 | 100.00% | 0.00% | 0.00% | 0.00% | string 8,844,342 |
| `user_id_db` | 8,844,342 | 100.00% | 0.00% | 0.00% | 96.27% | string 8,844,342 |

## `select_product_option_quality`

2,231,825 events (5.39% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 2,231,825 |
| `api_version` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `collection` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `current_url` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `device_id` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `email_address` | 2,231,825 | 100.00% | 0.00% | 0.00% | 96.29% | string 2,231,825 |
| `ip` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `local_time` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `option` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | array 2,231,825 |
| `option[]` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | object 2,231,825 |
| `option[].option_id` | 2,231,825 | 87.00% | 13.00% | 0.00% | 0.00% | string 1,941,650 |
| `option[].option_label` | 2,231,825 | 95.09% | 4.91% | 0.00% | 0.00% | string 2,122,284 |
| `option[].quality` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `option[].quality_label` | 2,231,825 | 86.55% | 13.45% | 0.00% | 0.0003% | string 1,931,725 |
| `option[].value_id` | 2,231,825 | 95.09% | 4.91% | 0.00% | 0.00% | string 2,122,284 |
| `option[].value_label` | 2,231,825 | 95.09% | 4.91% | 0.00% | 0.00% | string 2,122,284 |
| `product_id` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `referrer_url` | 2,231,825 | 100.00% | 0.00% | 0.00% | 12.42% | string 2,231,825 |
| `resolution` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `show_recommendation` | 2,231,825 | 100.00% | 0.00% | 15.61% | 0.00% | string 1,883,407, null 348,418 |
| `store_id` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `time_stamp` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | int 2,231,825 |
| `user_agent` | 2,231,825 | 100.00% | 0.00% | 0.00% | 0.00% | string 2,231,825 |
| `user_id_db` | 2,231,825 | 100.00% | 0.00% | 0.00% | 96.29% | string 2,231,825 |

## `view_static_page`

1,451,565 events (3.50% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 1,451,565 |
| `api_version` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `collection` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `current_url` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `device_id` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `email_address` | 1,451,565 | 100.00% | 0.00% | 0.0035% | 77.84% | string 1,451,514, null 51 |
| `ip` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `local_time` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `referrer_url` | 1,451,565 | 100.00% | 0.00% | 0.00% | 10.88% | string 1,451,565 |
| `resolution` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `show_recommendation` | 1,451,565 | 100.00% | 0.00% | 0.13% | 0.00% | string 1,449,621, null 1,944 |
| `store_id` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `time_stamp` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | int 1,451,565 |
| `user_agent` | 1,451,565 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,451,565 |
| `user_id_db` | 1,451,565 | 100.00% | 0.00% | 0.00% | 77.85% | string 1,451,565 |

## `view_landing_page`

1,434,230 events (3.46% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 1,434,230 |
| `api_version` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `collection` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `current_url` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `device_id` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `email_address` | 1,434,230 | 100.00% | 0.00% | 0.0009% | 95.86% | string 1,434,217, null 13 |
| `ip` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `local_time` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `referrer_url` | 1,434,230 | 100.00% | 0.00% | 0.00% | 8.38% | string 1,434,230 |
| `resolution` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `show_recommendation` | 1,434,230 | 100.00% | 0.00% | 0.14% | 0.0001% | string 1,432,249, null 1,981 |
| `store_id` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `time_stamp` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | int 1,434,230 |
| `user_agent` | 1,434,230 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,434,230 |
| `user_id_db` | 1,434,230 | 100.00% | 0.00% | 0.00% | 95.86% | string 1,434,230 |

## `product_detail_recommendation_visible`

1,302,362 events (3.14% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 1,302,362 |
| `api_version` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `collection` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `current_url` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `device_id` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `email_address` | 1,302,362 | 100.00% | 0.00% | 0.0004% | 95.38% | string 1,302,357, null 5 |
| `ip` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `local_time` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `referrer_url` | 1,302,362 | 100.00% | 0.00% | 0.00% | 13.54% | string 1,302,362 |
| `resolution` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `show_recommendation` | 1,302,362 | 100.00% | 0.00% | 19.04% | 0.00% | string 1,054,407, null 247,955 |
| `store_id` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `time_stamp` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | int 1,302,362 |
| `user_agent` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |
| `user_id_db` | 1,302,362 | 100.00% | 0.00% | 0.00% | 95.38% | string 1,302,362 |
| `viewing_product_id` | 1,302,362 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,302,362 |

## `view_home_page`

1,053,420 events (2.54% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 1,053,420 |
| `api_version` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `collection` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `current_url` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `device_id` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `email_address` | 1,053,420 | 100.00% | 0.00% | 0.0045% | 90.84% | string 1,053,373, null 47 |
| `ip` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `local_time` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `referrer_url` | 1,053,420 | 100.00% | 0.00% | 0.00% | 26.86% | string 1,053,420 |
| `resolution` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `show_recommendation` | 1,053,420 | 100.00% | 0.00% | 0.11% | 0.00% | string 1,052,248, null 1,172 |
| `store_id` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,053,420 |
| `time_stamp` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.00% | int 1,053,420 |
| `user_agent` | 1,053,420 | 100.00% | 0.00% | 0.00% | 0.0002% | string 1,053,420 |
| `user_id_db` | 1,053,420 | 100.00% | 0.00% | 0.00% | 90.85% | string 1,053,420 |

## `listing_page_recommendation_visible`

718,048 events (1.73% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 718,048 |
| `api_version` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `cat_id` | 718,048 | 100.00% | 0.00% | 99.9997% | 0.00% | null 718,046, string 2 |
| `collect_id` | 718,048 | 100.00% | 0.00% | 0.00% | 92.45% | string 718,048 |
| `collection` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `current_url` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `device_id` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `email_address` | 718,048 | 100.00% | 0.00% | 0.0001% | 97.21% | string 718,047, null 1 |
| `ip` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `local_time` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `option` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | object 718,048 |
| `option.alloy` | 718,048 | 100.00% | 0.00% | 0.00% | 87.03% | string 718,048 |
| `option.diamond` | 718,048 | 100.00% | 0.00% | 0.00% | 78.60% | string 718,048 |
| `option.shapediamond` | 718,048 | 100.00% | 0.00% | 0.00% | 98.84% | string 718,048 |
| `referrer_url` | 718,048 | 100.00% | 0.00% | 0.00% | 2.19% | string 718,048 |
| `resolution` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `show_recommendation` | 718,048 | 100.00% | 0.00% | 0.12% | 0.00% | string 717,165, null 883 |
| `store_id` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `time_stamp` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | int 718,048 |
| `user_agent` | 718,048 | 100.00% | 0.00% | 0.00% | 0.00% | string 718,048 |
| `user_id_db` | 718,048 | 100.00% | 0.00% | 0.00% | 97.21% | string 718,048 |

## `product_detail_recommendation_noticed`

490,780 events (1.18% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 490,780 |
| `api_version` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `collection` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `current_url` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `device_id` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `email_address` | 490,780 | 100.00% | 0.00% | 0.0006% | 94.71% | string 490,777, null 3 |
| `ip` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `local_time` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `referrer_url` | 490,780 | 100.00% | 0.00% | 0.00% | 13.97% | string 490,780 |
| `resolution` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `show_recommendation` | 490,780 | 100.00% | 0.00% | 16.76% | 0.00% | string 408,541, null 82,239 |
| `store_id` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `time_stamp` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | int 490,780 |
| `user_agent` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |
| `user_id_db` | 490,780 | 100.00% | 0.00% | 0.00% | 94.71% | string 490,780 |
| `viewing_product_id` | 490,780 | 100.00% | 0.00% | 0.00% | 0.00% | string 490,780 |

## `view_shopping_cart`

343,077 events (0.83% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 343,077 |
| `api_version` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `cart_products` | 343,077 | 100.00% | 0.00% | 0.00% | 27.02% | array 343,077 |
| `cart_products[]` | 662,257 | 100.00% | 0.00% | 0.00% | 0.00% | object 662,257 |
| `cart_products[].option` | 662,257 | 100.00% | 0.00% | 0.00% | 17.19% | array 548,441, string 113,816 |
| `cart_products[].option[]` | 921,528 | 100.00% | 0.00% | 0.00% | 0.00% | object 921,528 |
| `cart_products[].option[].option_id` | 921,528 | 100.00% | 0.00% | 0.00% | 0.00% | int 921,528 |
| `cart_products[].option[].option_label` | 921,528 | 100.00% | 0.00% | 0.00% | 0.00% | string 921,528 |
| `cart_products[].option[].value_id` | 921,528 | 100.00% | 0.00% | 0.00% | 0.00% | int 921,528 |
| `cart_products[].option[].value_label` | 921,528 | 100.00% | 0.00% | 0.00% | 0.00% | string 921,528 |
| `cart_products[].product_id` | 662,257 | 100.00% | 0.00% | 0.00% | 0.00% | int 662,257 |
| `collection` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `current_url` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `device_id` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `email_address` | 343,077 | 100.00% | 0.00% | 0.00% | 69.18% | string 343,077 |
| `ip` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `local_time` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `referrer_url` | 343,077 | 100.00% | 0.00% | 0.00% | 5.83% | string 343,077 |
| `resolution` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `show_recommendation` | 343,077 | 100.00% | 0.00% | 0.07% | 0.00% | string 342,851, null 226 |
| `store_id` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `time_stamp` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | int 343,077 |
| `user_agent` | 343,077 | 100.00% | 0.00% | 0.00% | 0.00% | string 343,077 |
| `user_id_db` | 343,077 | 100.00% | 0.00% | 0.00% | 69.18% | string 343,077 |

## `landing_page_recommendation_visible`

314,999 events (0.76% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 314,999 |
| `api_version` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `collection` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `current_url` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `device_id` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `email_address` | 314,999 | 100.00% | 0.00% | 0.00% | 95.81% | string 314,999 |
| `ip` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `local_time` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `referrer_url` | 314,999 | 100.00% | 0.00% | 0.00% | 5.40% | string 314,999 |
| `resolution` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `show_recommendation` | 314,999 | 100.00% | 0.00% | 0.14% | 0.00% | string 314,556, null 443 |
| `store_id` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `time_stamp` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | int 314,999 |
| `user_agent` | 314,999 | 100.00% | 0.00% | 0.00% | 0.00% | string 314,999 |
| `user_id_db` | 314,999 | 100.00% | 0.00% | 0.00% | 95.81% | string 314,999 |

## `search_box_action`

238,308 events (0.58% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 238,308 |
| `api_version` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `collection` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `current_url` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `device_id` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `email_address` | 238,308 | 100.00% | 0.00% | 0.0004% | 90.44% | string 238,307, null 1 |
| `ip` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `key_search` | 238,308 | 100.00% | 0.00% | 68.44% | 3.55% | null 163,108, string 75,200 |
| `local_time` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `referrer_url` | 238,308 | 100.00% | 0.00% | 0.00% | 8.87% | string 238,308 |
| `resolution` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `show_recommendation` | 238,308 | 100.00% | 0.00% | 0.20% | 0.00% | string 237,820, null 488 |
| `store_id` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `time_stamp` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | int 238,308 |
| `user_agent` | 238,308 | 100.00% | 0.00% | 0.00% | 0.00% | string 238,308 |
| `user_id_db` | 238,308 | 100.00% | 0.00% | 0.00% | 90.44% | string 238,308 |

## `add_to_cart_action`

187,901 events (0.45% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 187,901 |
| `api_version` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `collection` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `currency` | 187,901 | 100.00% | 0.00% | 0.70% | 0.0027% | string 186,590, null 1,311 |
| `current_url` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `device_id` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `email_address` | 187,901 | 100.00% | 0.00% | 0.00% | 89.24% | string 187,901 |
| `ip` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `is_paypal` | 187,901 | 100.00% | 0.00% | 99.30% | 0.00% | null 186,592, bool 1,309 |
| `local_time` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `option` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | array 187,901 |
| `option[]` | 375,802 | 100.00% | 0.00% | 0.00% | 0.00% | object 375,802 |
| `option[].option_id` | 375,802 | 100.00% | 0.00% | 0.00% | 16.54% | string 375,802 |
| `option[].option_label` | 375,802 | 100.00% | 0.00% | 0.00% | 0.00% | string 375,802 |
| `option[].value_id` | 375,802 | 100.00% | 0.00% | 0.00% | 16.55% | string 375,802 |
| `option[].value_label` | 375,802 | 100.00% | 0.00% | 0.00% | 100.00% | string 375,802 |
| `price` | 187,901 | 100.00% | 0.00% | 0.70% | 0.0011% | string 186,590, null 1,311 |
| `product_id` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `referrer_url` | 187,901 | 100.00% | 0.00% | 0.00% | 7.99% | string 187,901 |
| `resolution` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `show_recommendation` | 187,901 | 100.00% | 0.00% | 6.38% | 0.00% | string 175,912, null 11,989 |
| `store_id` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `time_stamp` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | int 187,901 |
| `user_agent` | 187,901 | 100.00% | 0.00% | 0.00% | 0.00% | string 187,901 |
| `user_id_db` | 187,901 | 100.00% | 0.00% | 0.00% | 89.24% | string 187,901 |

## `product_detail_recommendation_clicked`

179,228 events (0.43% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 179,228 |
| `api_version` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `collection` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `current_url` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `device_id` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `email_address` | 179,228 | 100.00% | 0.00% | 0.0011% | 95.67% | string 179,226, null 2 |
| `ip` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `local_time` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `recommendation_clicked_position` | 179,228 | 100.00% | 0.00% | 0.0011% | 0.00% | int 179,226, null 2 |
| `recommendation_product_id` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `referrer_url` | 179,228 | 100.00% | 0.00% | 0.00% | 11.89% | string 179,228 |
| `resolution` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `show_recommendation` | 179,228 | 100.00% | 0.00% | 15.04% | 0.00% | string 152,268, null 26,960 |
| `store_id` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `time_stamp` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | int 179,228 |
| `user_agent` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |
| `user_id_db` | 179,228 | 100.00% | 0.00% | 0.00% | 95.68% | string 179,228 |
| `viewing_product_id` | 179,228 | 100.00% | 0.00% | 0.00% | 0.00% | string 179,228 |

## `view_my_account`

112,066 events (0.27% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 112,066 |
| `api_version` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `collection` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `current_url` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `device_id` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `email_address` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `ip` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `local_time` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `referrer_url` | 112,066 | 100.00% | 0.00% | 0.00% | 7.79% | string 112,066 |
| `resolution` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `show_recommendation` | 112,066 | 100.00% | 0.00% | 0.02% | 0.00% | string 112,045, null 21 |
| `store_id` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `time_stamp` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | int 112,066 |
| `user_agent` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |
| `user_id_db` | 112,066 | 100.00% | 0.00% | 0.00% | 0.00% | string 112,066 |

## `checkout`

88,540 events (0.21% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 88,540 |
| `api_version` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `cart_products` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | array 88,540 |
| `cart_products[]` | 125,116 | 100.00% | 0.00% | 0.00% | 0.00% | object 125,116 |
| `cart_products[].amount` | 125,116 | 100.00% | 0.00% | 0.00% | 0.00% | int 125,116 |
| `cart_products[].option` | 125,116 | 100.00% | 0.00% | 0.00% | 21.57% | array 98,134, string 26,982 |
| `cart_products[].option[]` | 161,028 | 100.00% | 0.00% | 0.00% | 0.00% | object 161,028 |
| `cart_products[].option[].option_id` | 161,028 | 100.00% | 0.00% | 0.00% | 0.00% | int 161,028 |
| `cart_products[].option[].option_label` | 161,028 | 100.00% | 0.00% | 0.00% | 0.00% | string 161,028 |
| `cart_products[].option[].value_id` | 161,028 | 100.00% | 0.00% | 0.00% | 0.00% | int 161,028 |
| `cart_products[].option[].value_label` | 161,028 | 100.00% | 0.00% | 0.00% | 0.00% | string 161,028 |
| `cart_products[].product_id` | 125,116 | 100.00% | 0.00% | 0.00% | 0.00% | int 125,116 |
| `collection` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `current_url` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `device_id` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `email_address` | 88,540 | 100.00% | 0.00% | 0.00% | 32.05% | string 88,540 |
| `ip` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `local_time` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `order_id` | 88,540 | 100.00% | 0.00% | 0.00% | 100.00% | string 88,540 |
| `referrer_url` | 88,540 | 100.00% | 0.00% | 0.00% | 1.22% | string 88,540 |
| `resolution` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `show_recommendation` | 88,540 | 100.00% | 0.00% | 0.0011% | 0.00% | string 88,539, null 1 |
| `store_id` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `time_stamp` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | int 88,540 |
| `user_agent` | 88,540 | 100.00% | 0.00% | 0.00% | 0.00% | string 88,540 |
| `user_id_db` | 88,540 | 100.00% | 0.00% | 0.00% | 32.05% | string 88,540 |

## `landing_page_recommendation_noticed`

58,186 events (0.14% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 58,186 |
| `api_version` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `collection` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `current_url` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `device_id` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `email_address` | 58,186 | 100.00% | 0.00% | 0.00% | 95.75% | string 58,186 |
| `ip` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `local_time` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `referrer_url` | 58,186 | 100.00% | 0.00% | 0.00% | 4.10% | string 58,186 |
| `resolution` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `show_recommendation` | 58,186 | 100.00% | 0.00% | 0.17% | 0.00% | string 58,086, null 100 |
| `store_id` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `time_stamp` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | int 58,186 |
| `user_agent` | 58,186 | 100.00% | 0.00% | 0.00% | 0.00% | string 58,186 |
| `user_id_db` | 58,186 | 100.00% | 0.00% | 0.00% | 95.75% | string 58,186 |

## `listing_page_recommendation_noticed`

39,819 events (0.10% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 39,819 |
| `api_version` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `cat_id` | 39,819 | 100.00% | 0.00% | 100.00% | 0.00% | null 39,819 |
| `collect_id` | 39,819 | 100.00% | 0.00% | 0.00% | 90.58% | string 39,819 |
| `collection` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `current_url` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `device_id` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `email_address` | 39,819 | 100.00% | 0.00% | 0.00% | 96.07% | string 39,819 |
| `ip` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `local_time` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `option` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | object 39,819 |
| `option.alloy` | 39,819 | 100.00% | 0.00% | 0.00% | 84.58% | string 39,819 |
| `option.diamond` | 39,819 | 100.00% | 0.00% | 0.00% | 74.76% | string 39,819 |
| `option.shapediamond` | 39,819 | 100.00% | 0.00% | 0.00% | 98.43% | string 39,819 |
| `referrer_url` | 39,819 | 100.00% | 0.00% | 0.00% | 2.19% | string 39,819 |
| `resolution` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `show_recommendation` | 39,819 | 100.00% | 0.00% | 0.13% | 0.00% | string 39,769, null 50 |
| `store_id` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `time_stamp` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | int 39,819 |
| `user_agent` | 39,819 | 100.00% | 0.00% | 0.00% | 0.00% | string 39,819 |
| `user_id_db` | 39,819 | 100.00% | 0.00% | 0.00% | 96.07% | string 39,819 |

## `view_all_recommend`

33,664 events (0.08% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 33,664 |
| `api_version` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `collection` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `current_url` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `device_id` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `email_address` | 33,664 | 100.00% | 0.00% | 0.00% | 100.00% | string 33,664 |
| `ip` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `local_time` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `option` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | object 33,664 |
| `option.Kollektion` | 33,664 | 100.00% | 0.00% | 0.00% | 14.04% | string 33,664 |
| `option.alloy` | 33,664 | 100.00% | 0.00% | 0.00% | 1.60% | string 33,664 |
| `option.category id` | 33,664 | 100.00% | 0.00% | 0.00% | 0.02% | string 33,664 |
| `option.finish` | 33,664 | 100.00% | 0.00% | 0.00% | 87.13% | string 33,664 |
| `option.kollektion_id` | 33,664 | 100.00% | 0.00% | 0.00% | 14.04% | string 33,664 |
| `option.pearlcolor` | 33,664 | 100.00% | 0.00% | 0.00% | 97.92% | string 33,664 |
| `option.price` | 33,664 | 100.00% | 0.00% | 0.00% | 0.03% | string 33,664 |
| `option.stone` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `product_id` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `referrer_url` | 33,664 | 100.00% | 0.00% | 0.00% | 2.35% | string 33,664 |
| `resolution` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `show_recommendation` | 33,664 | 100.00% | 0.00% | 0.06% | 0.00% | string 33,643, null 21 |
| `store_id` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `time_stamp` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | int 33,664 |
| `user_agent` | 33,664 | 100.00% | 0.00% | 0.00% | 0.00% | string 33,664 |
| `user_id_db` | 33,664 | 100.00% | 0.00% | 0.00% | 92.97% | string 33,664 |

## `checkout_success`

26,079 events (0.06% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 26,079 |
| `api_version` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `cart_products` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | array 26,079 |
| `cart_products[]` | 35,065 | 100.00% | 0.00% | 0.00% | 0.00% | object 35,065 |
| `cart_products[].amount` | 35,065 | 100.00% | 0.00% | 0.00% | 0.00% | int 35,065 |
| `cart_products[].currency` | 35,065 | 100.00% | 0.00% | 0.00% | 3.10% | string 35,065 |
| `cart_products[].option` | 35,065 | 100.00% | 0.00% | 0.00% | 21.99% | array 27,354, string 7,711 |
| `cart_products[].option[]` | 43,562 | 100.00% | 0.00% | 0.00% | 0.00% | object 43,562 |
| `cart_products[].option[].option_id` | 43,562 | 100.00% | 0.00% | 0.00% | 0.00% | int 43,562 |
| `cart_products[].option[].option_label` | 43,562 | 100.00% | 0.00% | 0.00% | 0.00% | string 43,562 |
| `cart_products[].option[].value_id` | 43,562 | 100.00% | 0.00% | 0.00% | 0.00% | int 43,562 |
| `cart_products[].option[].value_label` | 43,562 | 100.00% | 0.00% | 0.00% | 0.00% | string 43,562 |
| `cart_products[].price` | 35,065 | 100.00% | 0.00% | 0.00% | 0.0029% | string 35,065 |
| `cart_products[].product_id` | 35,065 | 100.00% | 0.00% | 0.00% | 0.00% | int 35,065 |
| `collection` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `current_url` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `device_id` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `email_address` | 26,079 | 100.00% | 0.00% | 0.00% | 35.27% | string 26,079 |
| `ip` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `local_time` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `order_id` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | int 16,116, double 9,963 |
| `referrer_url` | 26,079 | 100.00% | 0.00% | 0.00% | 1.93% | string 26,079 |
| `resolution` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `show_recommendation` | 26,079 | 100.00% | 0.00% | 0.01% | 0.00% | string 26,077, null 2 |
| `store_id` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `time_stamp` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | int 26,079 |
| `user_agent` | 26,079 | 100.00% | 0.00% | 0.00% | 0.00% | string 26,079 |
| `user_id_db` | 26,079 | 100.00% | 0.00% | 0.00% | 35.27% | string 26,079 |

## `listing_page_recommendation_clicked`

25,545 events (0.06% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 25,545 |
| `api_version` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `cat_id` | 25,545 | 100.00% | 0.00% | 100.00% | 0.00% | null 25,545 |
| `collect_id` | 25,545 | 100.00% | 0.00% | 0.00% | 90.40% | string 25,545 |
| `collection` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `current_url` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `device_id` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `email_address` | 25,545 | 100.00% | 0.00% | 0.00% | 96.19% | string 25,545 |
| `ip` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `local_time` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `option` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | object 25,545 |
| `option.alloy` | 25,545 | 100.00% | 0.00% | 0.00% | 86.92% | string 25,545 |
| `option.diamond` | 25,545 | 100.00% | 0.00% | 0.00% | 78.40% | string 25,545 |
| `option.shapediamond` | 25,545 | 100.00% | 0.00% | 0.00% | 98.54% | string 25,545 |
| `recommendation_clicked_position` | 25,545 | 100.00% | 0.00% | 100.00% | 0.00% | null 25,545 |
| `recommendation_product_id` | 25,545 | 100.00% | 0.00% | 100.00% | 0.00% | null 25,545 |
| `referrer_url` | 25,545 | 100.00% | 0.00% | 0.00% | 2.44% | string 25,545 |
| `resolution` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `show_recommendation` | 25,545 | 100.00% | 0.00% | 0.07% | 0.00% | string 25,526, null 19 |
| `store_id` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `time_stamp` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | int 25,545 |
| `user_agent` | 25,545 | 100.00% | 0.00% | 0.00% | 0.00% | string 25,545 |
| `user_id_db` | 25,545 | 100.00% | 0.00% | 0.00% | 96.19% | string 25,545 |

## `landing_page_recommendation_clicked`

20,128 events (0.05% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 20,128 |
| `api_version` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `collection` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `current_url` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `device_id` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `email_address` | 20,128 | 100.00% | 0.00% | 0.00% | 95.93% | string 20,128 |
| `ip` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `local_time` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `recommendation_product_id` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `recommendation_product_position` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | int 20,128 |
| `referrer_url` | 20,128 | 100.00% | 0.00% | 0.00% | 3.91% | string 20,128 |
| `resolution` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `show_recommendation` | 20,128 | 100.00% | 0.00% | 0.19% | 0.00% | string 20,090, null 38 |
| `store_id` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `time_stamp` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | int 20,128 |
| `user_agent` | 20,128 | 100.00% | 0.00% | 0.00% | 0.00% | string 20,128 |
| `user_id_db` | 20,128 | 100.00% | 0.00% | 0.00% | 95.93% | string 20,128 |

## `product_view_all_recommend_clicked`

16,682 events (0.04% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 16,682 |
| `api_version` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `collection` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `current_url` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `device_id` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `email_address` | 16,682 | 100.00% | 0.00% | 0.00% | 100.00% | string 16,682 |
| `ip` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `local_time` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `recommendation_product_id` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `recommendation_product_position` | 16,682 | 100.00% | 0.00% | 0.00% | 100.00% | string 16,682 |
| `referrer_url` | 16,682 | 100.00% | 0.00% | 0.00% | 2.16% | string 16,682 |
| `resolution` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `show_recommendation` | 16,682 | 100.00% | 0.00% | 0.17% | 0.00% | string 16,653, null 29 |
| `store_id` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `time_stamp` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | int 16,682 |
| `user_agent` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |
| `user_id_db` | 16,682 | 100.00% | 0.00% | 0.00% | 91.84% | string 16,682 |
| `viewing_product_id` | 16,682 | 100.00% | 0.00% | 0.00% | 0.00% | string 16,682 |

## `view_sorting_relevance`

15,284 events (0.04% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 15,284 |
| `api_version` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `collection` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `current_url` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `device_id` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `email_address` | 15,284 | 100.00% | 0.00% | 0.22% | 88.33% | string 15,251, null 33 |
| `ip` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `local_time` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `option` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | object 15,284 |
| `option.alloy` | 15,284 | 100.00% | 0.00% | 0.00% | 77.46% | string 15,284 |
| `option.diamond` | 15,284 | 100.00% | 0.00% | 0.00% | 64.57% | string 15,284 |
| `option.shapediamond` | 15,284 | 100.00% | 0.00% | 0.00% | 95.42% | string 15,284 |
| `referrer_url` | 15,284 | 100.00% | 0.00% | 0.00% | 7.30% | string 15,284 |
| `resolution` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `show_recommendation` | 15,284 | 100.00% | 0.00% | 0.09% | 0.00% | string 15,270, null 14 |
| `store_id` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `time_stamp` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | int 15,284 |
| `user_agent` | 15,284 | 100.00% | 0.00% | 0.00% | 0.00% | string 15,284 |
| `user_id_db` | 15,284 | 100.00% | 0.00% | 0.00% | 88.54% | string 15,284 |

## `sorting_relevance_click_action`

1,713 events (0.0041% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 1,713 |
| `api_version` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `collection` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `current_url` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `device_id` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `email_address` | 1,713 | 100.00% | 0.00% | 0.12% | 93.93% | string 1,711, null 2 |
| `ip` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `local_time` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `recommendation_product_id` | 1,713 | 100.00% | 0.00% | 2.98% | 0.00% | string 1,662, null 51 |
| `recommendation_product_position` | 1,713 | 100.00% | 0.00% | 2.98% | 0.00% | string 1,662, null 51 |
| `referrer_url` | 1,713 | 100.00% | 0.00% | 0.00% | 1.58% | string 1,713 |
| `resolution` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `show_recommendation` | 1,713 | 100.00% | 0.00% | 0.58% | 0.00% | string 1,703, null 10 |
| `store_id` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `time_stamp` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | int 1,713 |
| `user_agent` | 1,713 | 100.00% | 0.00% | 0.00% | 0.00% | string 1,713 |
| `user_id_db` | 1,713 | 100.00% | 0.00% | 0.00% | 94.05% | string 1,713 |

## `back_to_product_action`

561 events (0.0014% of profiled documents).

| Path | Containers | Present | Missing | Null | Empty | BSON types |
|---|---:|---:|---:|---:|---:|---|
| `_id` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | objectId 561 |
| `api_version` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `collection` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `current_url` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `device_id` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `email_address` | 561 | 100.00% | 0.00% | 0.00% | 93.05% | string 561 |
| `ip` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `local_time` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `product_id` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `referrer_url` | 561 | 100.00% | 0.00% | 0.00% | 1.07% | string 561 |
| `resolution` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `show_recommendation` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `store_id` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `time_stamp` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | int 561 |
| `user_agent` | 561 | 100.00% | 0.00% | 0.00% | 0.00% | string 561 |
| `user_id_db` | 561 | 100.00% | 0.00% | 0.00% | 93.05% | string 561 |
