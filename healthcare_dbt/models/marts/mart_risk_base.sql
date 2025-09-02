with labs_agg as (
  select
    enc_id,
    avg(case when test_name = 'hemoglobin' then value end)  as avg_hemo,
    avg(case when test_name = 'glucose'   then value end)   as avg_glucose,
    avg(case when test_name = 'creatinine' then value end)  as avg_creatinine,
    avg(case when test_name = 'wbc'        then value end)  as avg_wbc,
    avg(case when test_name = 'platelets'  then value end)  as avg_platelets
  from {{ ref('stg_labs') }}
  group by enc_id
),
enc_stats as (
  select
    enc_id, patient_id, admit_ts, discharge_ts, length_of_stay_days, readmit_30d
  from {{ ref('stg_encounters') }}
),
patient_features as (
  select patient_id, sex, age
  from {{ ref('stg_patients') }}
)
select
  es.enc_id,
  es.patient_id,
  pf.sex,
  pf.age,
  es.admit_ts,
  es.discharge_ts,
  es.length_of_stay_days,
  la.avg_hemo,
  la.avg_glucose,
  la.avg_creatinine,
  la.avg_wbc,
  la.avg_platelets,
  es.readmit_30d
from enc_stats es
join patient_features pf on pf.patient_id = es.patient_id
left join labs_agg la on la.enc_id = es.enc_id