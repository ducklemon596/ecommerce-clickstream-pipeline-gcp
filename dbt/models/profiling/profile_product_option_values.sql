-- Column profile of raw product_option_values. Not on the sample target, which holds events only.
{{ config(enabled=target.name != 'sample') }}
{{ dbt_profiler.get_profile(relation=source('raw', 'product_option_values')) }}
