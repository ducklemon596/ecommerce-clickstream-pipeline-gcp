{% docs profile_ip_locations %}
Profile of `ip_locations` on target `prod`, 3239627 rows.

| Column | Type | Not null | Distinct | Unique | Min | Max |
| --- | --- | ---: | ---: | :---: | --- | --- |
| `ip_hash` | string | 100.00% | 3239627 | yes |  |  |
| `ip_version` | int64 | 100.00% | 2 |  | 4 | 6 |
| `status` | string | 100.00% | 4 |  |  |  |
| `country_code` | string | 98.82% | 219 |  |  |  |
| `country_name` | string | 98.82% | 219 |  |  |  |
| `region` | string | 98.76% | 2245 |  |  |  |
| `city` | string | 98.76% | 49340 |  |  |  |
| `database_id` | string | 100.00% | 1 |  |  |  |
{% enddocs %}
