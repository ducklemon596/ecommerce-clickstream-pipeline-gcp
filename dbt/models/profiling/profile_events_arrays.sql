-- Profile of the two ARRAY columns of raw events, which dbt_profiler cannot profile.
-- One row per array (field = '(array)') with array-length statistics, then one row per
-- element field with its null and distinct counts. Reads only the two columns.
with events as (
    select option, cart_products
    from {{ source('raw', 'events') }}
),

array_level as (
    select 'option' as array_column, array_length(option) as n from events
    union all
    select 'cart_products', array_length(cart_products) from events
),

option_elements as (
    select o.* from events, unnest(option) as o
),

cart_elements as (
    select c.* from events, unnest(cart_products) as c
),

field_level as (
    {%- set fields = {
        'option': ['option_label', 'option_id', 'value_label', 'value_id', 'quality', 'quality_label'],
        'cart_products': ['product_id', 'amount', 'price', 'currency'],
    } %}
    {%- for array, columns in fields.items() %}
    {%- set elements = 'option_elements' if array == 'option' else 'cart_elements' %}
    {%- for column in columns %}
    select
        '{{ array }}' as array_column,
        '{{ column }}' as field,
        count(*) as elements,
        safe_divide(countif({{ column }} is not null), count(*)) as not_null_proportion,
        count(distinct {{ column }}) as distinct_count
    from {{ elements }}
    {%- if not loop.last %} union all{% endif %}
    {%- endfor %}
    {%- if not loop.last %} union all{% endif %}
    {%- endfor %}
)

select
    array_column,
    '(array)' as field,
    count(*) as rows_profiled,
    countif(n > 0) as rows_non_empty,
    safe_divide(countif(n > 0), count(*)) as non_empty_proportion,
    min(n) as min_length,
    max(n) as max_length,
    avg(n) as avg_length,
    sum(n) as elements,
    cast(null as float64) as not_null_proportion,
    cast(null as int64) as distinct_count
from array_level
group by array_column

union all

select
    array_column,
    field,
    cast(null as int64),
    cast(null as int64),
    cast(null as float64),
    cast(null as int64),
    cast(null as int64),
    cast(null as float64),
    elements,
    not_null_proportion,
    distinct_count
from field_level
