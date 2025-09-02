with src as (
  select enc_id, test_name, value, taken_ts
  from hc.labs
)
select
  enc_id,
  lower(test_name) as test_name,
  cast(value as numeric) as value,
  taken_ts
from src