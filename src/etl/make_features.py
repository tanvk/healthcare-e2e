import os, json
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split

SCHEMA_TABLE = "hc_dbt_hc_mart.mart_risk_base"                                                          # CONFIG
EXPORT_DIR = Path("exports")
RANDOM_STATE = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.2 

def main():
    load_dotenv(Path(".") / ".env")
    url = os.getenv("DATABASE_URL")
    assert url, "DATABASE_URL not found in .env"
    eng = create_engine(url)

    with eng.connect() as c:
        df = pd.read_sql(text(f"select * from {SCHEMA_TABLE}"), c)

    label_col = "readmit_30d"                                                                           # BASIC FEATURE SET
    id_cols = ["enc_id", "patient_id", "admit_ts", "discharge_ts"]
    X = df.drop(columns=[label_col] + id_cols, errors="ignore")
    y = df[label_col].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(                                                # TRAIN-TEST STRATIFIED
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=VAL_SIZE, stratify=y_train, random_state=RANDOM_STATE
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    (EXPORT_DIR / "features").mkdir(exist_ok=True)

    X_train.assign(readmit_30d=y_train).to_csv(EXPORT_DIR / "features/train.csv", index=False)          # SAVE CSVs FOR LATER USE
    X_val.assign(readmit_30d=y_val).to_csv(EXPORT_DIR / "features/val.csv", index=False)
    X_test.assign(readmit_30d=y_test).to_csv(EXPORT_DIR / "features/test.csv", index=False)

    meta = {
        "label": label_col,
        "categoricals": ["sex"],
        "numericals": [c for c in X.columns if c not in ["sex"]],
        "rows": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
    }
    (EXPORT_DIR / "features/meta.json").write_text(json.dumps(meta, indent=2))
    print("Wrote features to exports/features/  ->", meta)

if __name__ == "__main__":
    main()