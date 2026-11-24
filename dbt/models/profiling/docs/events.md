{% docs profile_events %}
Profile of `events` on target `prod`, 41432473 rows.

| Column | Type | Not null | Distinct | Unique | Min | Max |
| --- | --- | ---: | ---: | :---: | --- | --- |
| `_id` | string | 100.00% | 41432473 | yes |  |  |
| `collection` | string | 100.00% | 27 |  |  |  |
| `time_stamp` | timestamp | 100.00% | 5492095 |  | 2020-04-01 00:00:01+00 | 2020-06-04 10:21:32+00 |
| `api_version` | string | 100.00% | 1 |  |  |  |
| `store_id` | string | 100.00% | 86 |  |  |  |
| `current_url` | string | 100.00% | 16151626 |  |  |  |
| `referrer_url` | string | 100.00% | 3578384 |  |  |  |
| `ip_hash` | string | 100.00% | 3239628 |  |  |  |
| `device_id_hash` | string | 100.00% | 7691556 |  |  |  |
| `user_id_hash` | string | 100.00% | 31128 |  |  |  |
| `user_agent` | string | 100.00% | 207463 |  |  |  |
| `local_time` | string | 100.00% | 3132309 |  |  |  |
| `resolution` | string | 100.00% | 6230 |  |  |  |
| `email_hash` | string | 100.00% | 31188 |  |  |  |
| `show_recommendation` | string | 81.25% | 142 |  |  |  |
| `product_id` | string | 53.68% | 19417 |  |  |  |
| `viewing_product_id` | string | 4.80% | 16981 |  |  |  |
| `recommendation_product_id` | string | 0.53% | 9695 |  |  |  |
| `recommendation_clicked_position` | int64 | 0.43% | 1 |  | 0 | 0 |
| `recommendation_product_position` | string | 0.09% | 165 |  |  |  |
| `recommendation` | bool | 26.41% | 1 |  |  |  |
| `utm_source` | string | 26.41% | 7 |  |  |  |
| `utm_medium` | string | 26.41% | 82 |  |  |  |
| `cat_id` | string | 0.00% | 37 |  |  |  |
| `collect_id` | string | 29.07% | 62 |  |  |  |
| `key_search` | string | 0.18% | 31946 |  |  |  |
| `price` | string | 0.45% | 28611 |  |  |  |
| `currency` | string | 0.45% | 85 |  |  |  |
| `is_paypal` | bool | 0.00% | 1 |  |  |  |
| `order_id` | string | 0.28% | 26032 |  |  |  |
| `option_filter` | struct | 29.18% |  |  |  |  |
{% enddocs %}
