-- Column profile of raw ip_locations. Not on the sample target, which holds events only.
{{ config(enabled=target.name != 'sample') }}
{{ dbt_profiler.get_profile(relation=source('raw', 'ip_locations')) }}
