with src as (
  select patient_id, sex, age
  from hc.patients
)
select
  patient_id,
  upper(sex) as sex,
  cast(age as int) as age
from src