{#
  Prints a docs block that renders a stored profile as a Markdown table, for dbt docs.

  It reads the materialized profile_<table> model, not the source, so regenerating
  the docs costs a few KB instead of a new profiling scan. Run it after the profiling
  models were built on the same target:

    dbt -q run-operation print_profile_doc --args '{table: events}' --target prod \
      > models/profiling/docs/events.md
#}
{% macro print_profile_doc(table) %}
  {%- set query -%}
    select
      column_name,
      data_type,
      row_count,
      not_null_proportion,
      distinct_count,
      is_unique,
      cast(min as string) as min_value,
      cast(max as string) as max_value
    from {{ ref('profile_' ~ table) }}
  {%- endset -%}
  {%- set by_name = {} -%}
  {%- for r in run_query(query).rows -%}{%- do by_name.update({r['column_name']: r}) -%}{%- endfor -%}
  {#- Keep the source's column order; the profile table has none. -#}
  {%- set rows = [] -%}
  {%- for c in adapter.get_columns_in_relation(source('raw', table)) if c.name in by_name -%}
    {%- do rows.append(by_name[c.name]) -%}
  {%- endfor -%}
  {%- set lines = [
    "{" ~ "% docs profile_" ~ table ~ " %" ~ "}",
    "Profile of `" ~ table ~ "` on target `" ~ target.name ~ "`, " ~ (rows[0]['row_count'] if rows else 0) ~ " rows.",
    "",
    "| Column | Type | Not null | Distinct | Unique | Min | Max |",
    "| --- | --- | ---: | ---: | :---: | --- | --- |",
  ] -%}
  {%- for r in rows -%}
    {%- set data_type = r['data_type'] if r['data_type'][:6] != 'struct' else 'struct' -%}
    {%- set distinct = '' if r['distinct_count'] is none else r['distinct_count'] -%}
    {%- set unique = 'yes' if r['is_unique'] else '' -%}
    {%- do lines.append("| `" ~ r['column_name'] ~ "` | " ~ data_type ~ " | "
        ~ "%.2f%%" | format(r['not_null_proportion'] * 100) ~ " | " ~ distinct ~ " | " ~ unique ~ " | "
        ~ (r['min_value'] or '') ~ " | " ~ (r['max_value'] or '') ~ " |") -%}
  {%- endfor -%}
  {%- do lines.append("{" ~ "% enddocs %" ~ "}") -%}
  {%- do print(lines | join('\n')) -%}
{% endmacro %}
