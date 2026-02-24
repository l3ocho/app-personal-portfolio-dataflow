select
  club_id,
  club_name,
  country,
  club_slug,
  logo_url,
  source_url
from {{ source('raw_football', 'dim_club') }}
where club_id is not null
