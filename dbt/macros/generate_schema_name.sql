-- Override dbt default schema name generation.
-- Use the custom schema name directly instead of
-- concatenating with the target schema.
-- See: https://docs.getdbt.com/docs/build/custom-schemas
{% macro generate_schema_name(custom_schema_name, node) %}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{% endmacro %}
