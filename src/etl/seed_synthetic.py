import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine,text
from dotenv import load_dotenv

# CONFIG
N_PATIENTS = 200
ENCOUNTERS_PER_PATIENT = (1, 3)
LABS_PER_ENCOUNTER = (3, 10)
RESET_TABLES = True


TESTS = {
    "hemoglobin":  (11.0, 16.0),
    "glucose":     (70, 180),
    "creatinine":  (0.5, 1.6),
    "wbc":         (4.0, 11.0),
    "platelets":   (150, 450),
}

# SETUP ENGINE
ROOT = Path(__file__).resolve().parents[2]      # project root
load_dotenv(ROOT / ".env")
DB_URL = os.getenv("DATABASE_URL")
assert DB_URL, "DATABASE_URL missing in .env"
engine = create_engine(DB_URL)

rng = np.random.default_rng(42)
random.seed(42)

def rand_dt_within(days_back=365):
    """Random UTC timestamp within last `days_back` days."""
    now = datetime.utcnow()
    delta = timedelta(days=int(rng.integers(0, days_back)), hours=int(rng.integers(0, 24)),
                      minutes=int(rng.integers(0, 60)))
    return now - delta

def synth_patients(n):
    rows = []
    for _ in range(n):
        pid = str(uuid.uuid4())[:12]
        sex = random.choice(["M", "F"])
        age = int(rng.integers(18, 90))
        rows.append({"patient_id": pid, "sex": sex, "age": age})
    return pd.DataFrame(rows)

def synth_encounters(patients_df):
    rows = []
    for pid in patients_df["patient_id"]:
        k = int(rng.integers(ENCOUNTERS_PER_PATIENT[0], ENCOUNTERS_PER_PATIENT[1] + 1))
        for _ in range(k):
            enc_id = str(uuid.uuid4())[:12]
            admit = rand_dt_within(365)
            los_days = float(abs(rng.normal(3, 2)))  # ~3 days avg
            discharge = admit + timedelta(days=los_days)
            readmit_prob = 0.15 + 0.002 * (patients_df.loc[patients_df.patient_id == pid, "age"].item() - 40)
            readmit_30d = rng.random() < max(0.05, min(0.5, readmit_prob))
            rows.append({
                "enc_id": enc_id,
                "patient_id": pid,
                "admit_ts": admit,
                "discharge_ts": discharge,
                "readmit_30d": bool(readmit_30d),
            })
    return pd.DataFrame(rows)

def synth_labs(encounters_df):
    rows = []
    for enc_id in encounters_df["enc_id"]:
        k = int(rng.integers(LABS_PER_ENCOUNTER[0], LABS_PER_ENCOUNTER[1] + 1))
        chosen_tests = rng.choice(list(TESTS.keys()), size=k, replace=True)
        admit_ts = encounters_df.loc[encounters_df.enc_id == enc_id, "admit_ts"].item()
        for t in chosen_tests:
            lo, hi = TESTS[t]
            val = rng.uniform(lo, hi)
            taken_offset = timedelta(hours=float(abs(rng.normal(24, 12))))
            rows.append({
                "enc_id": enc_id,
                "test_name": t,
                "value": float(round(val, 2)),
                "taken_ts": admit_ts + taken_offset,
            })
    df = pd.DataFrame(rows)
    # Postgres table has a serial PK (lab_id), so we don't set it here
    return df

def main():
    with engine.begin() as conn:
        if RESET_TABLES:
            conn.execute(text("truncate table hc.labs restart identity cascade;"))
            conn.execute(text("truncate table hc.encounters restart identity cascade;"))
            conn.execute(text("truncate table hc.patients restart identity cascade;"))

    patients = synth_patients(N_PATIENTS)
    encounters = synth_encounters(patients)
    labs = synth_labs(encounters)

    # write to Postgres
    patients.to_sql("patients", engine, schema="hc", if_exists="append", index=False, method="multi", chunksize=1000)
    encounters.to_sql("encounters", engine, schema="hc", if_exists="append", index=False, method="multi", chunksize=1000)
    labs.to_sql("labs", engine, schema="hc", if_exists="append", index=False, method="multi", chunksize=2000)

    # quick counts
    with engine.connect() as conn:
        counts = conn.execute(text("""
            select 'patients' as table, count(*) from hc.patients
            union all
            select 'encounters', count(*) from hc.encounters
            union all
            select 'labs', count(*) from hc.labs
            ;
        """)).fetchall()
        print("Row counts:", counts)

if __name__ == "__main__":
    main()