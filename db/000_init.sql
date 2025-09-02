-- Schema
create schema if not exists hc;

-- Core tables
create table if not exists hc.patients (
  patient_id text primary key,
  sex        text check (sex in ('M','F')),
  age        int  check (age between 0 and 120)
);

create table if not exists hc.encounters (
  enc_id        text primary key,
  patient_id    text references hc.patients(patient_id),
  admit_ts      timestamptz,
  discharge_ts  timestamptz,
  readmit_30d   boolean
);

create table if not exists hc.labs (
  lab_id    bigserial primary key,
  enc_id    text references hc.encounters(enc_id),
  test_name text,
  value     numeric,
  taken_ts  timestamptz
);

-- Helpful indexes
create index if not exists ix_encounters_patient on hc.encounters(patient_id);
create index if not exists ix_labs_enc on hc.labs(enc_id);
create index if not exists ix_labs_test on hc.labs(test_name);