{{
  config(
    tags=['football', 'dimension']
  )
}}

select
  club_id,
  club_name,
  club_code,
  country,
  founded_year,
  city,
from {{ source('raw_football', 'dim_club') }}
where club_id is not null
