with src as (
  select enc_id, patient_id, admit_ts, discharge_ts, readmit_30d
  from hc.encounters
)
select
  enc_id,
  patient_id,
  admit_ts,
  discharge_ts,
  (extract(epoch from (discharge_ts - admit_ts))/86400.0) as length_of_stay_days,
  readmit_30d::boolean as readmit_30d
from src