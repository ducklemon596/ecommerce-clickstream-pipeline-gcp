-- Column profile of raw events: null and distinct counts for every top-level column,
-- min/max for numbers and times. The ARRAY columns are profiled in profile_events_arrays,
-- because dbt_profiler would run count(distinct) on them, which BigQuery rejects.
{{ dbt_profiler.get_profile(
    relation=source('raw', 'events'),
    exclude_columns=['option', 'cart_products']
) }}
