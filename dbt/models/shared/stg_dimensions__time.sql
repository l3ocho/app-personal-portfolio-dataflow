-- Staged time dimension
-- Source: shared.dim_time table
-- Grain: One row per month
-- Note: Shared dimension used across all dashboard projects

with source as (
    select * from {{ source('shared', 'dim_time') }}
),

staged as (
    select
        date_key,
        full_date,
        year,
        month,
        quarter,
        month_name,
        is_month_start
    from source
)

select * from staged
