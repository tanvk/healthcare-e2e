import os, json
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import joblib

ROOT = Path(".")
EXPORT_DIR = ROOT / "exports" / "bi"
MART = "hc_dbt_hc_mart.mart_risk_base"   # where dbt wrote the table

def export_cohort(eng):
    q = f"""
    with base as (
      select *
      from {MART}
    )
    select
      count(*)::int as encounters,
      sum(case when readmit_30d then 1 else 0 end)::int as readmits,
      round(100.0*avg(case when readmit_30d then 1 else 0 end),2) as readmit_rate_pct,
      round(avg(age),2) as avg_age,
      round(avg(length_of_stay_days),2) as avg_los
    from base;
    """
    with eng.connect() as c:
        row = c.execute(text(q)).mappings().first()
    pd.DataFrame([row]).to_csv(EXPORT_DIR / "cohort_overview.csv", index=False)

def export_model_performance():
    ml_dir = ROOT / "exports" / "ml"
    val = json.loads((ml_dir / "val_metrics.json").read_text())
    test = json.loads((ml_dir / "test_metrics.json").read_text())

    df = pd.DataFrame([
        {"split":"val",  **val},
        {"split":"test", **test},
    ])
    df.to_csv(EXPORT_DIR / "model_performance.csv", index=False)

def _get_feature_names_from_pipeline(pipe):
    """Reconstruct final feature names after ColumnTransformer + OneHotEncoder."""
    pre = pipe.named_steps["pre"]
    num_names, cat_names = [], []
    # numeric transformer
    try:
        num_selector = pre.transformers_[0][2]
        num_names = list(num_selector)
    except Exception:
        pass
    # categorical transformer
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    cat_cols = []
    for name, trans, cols in pre.transformers_:
        if name == "cat":
            cat_cols = list(cols)
            ohe: OneHotEncoder = trans.named_steps["onehot"]
            cats = ohe.categories_
            expanded = []
            for col, levels in zip(cat_cols, cats):
                expanded += [f"{col}__{lvl}" for lvl in levels]
            cat_names = expanded
    return num_names + cat_names

def export_feature_importance():
    model_path = ROOT / "artifacts" / "model_pipeline.pkl"
    pipe = joblib.load(model_path)

    # use absolute coefficients for Logistic Regression
    model = pipe.named_steps["clf"]
    if hasattr(model, "coef_"):
        feats = _get_feature_names_from_pipeline(pipe)
        coefs = model.coef_.ravel()
        # Guard length mismatch
        n = min(len(feats), len(coefs))
        df = pd.DataFrame({
            "feature": feats[:n],
            "importance": np.abs(coefs[:n]),
            "raw_weight": coefs[:n]
        }).sort_values("importance", ascending=False)
    else:
        # Fallback for tree models (e.g., XGBoost)
        try:
            feats = _get_feature_names_from_pipeline(pipe)
            importances = model.feature_importances_
            n = min(len(feats), len(importances))
            df = pd.DataFrame({
                "feature": feats[:n],
                "importance": importances[:n]
            }).sort_values("importance", ascending=False)
        except Exception:
            df = pd.DataFrame(columns=["feature","importance"])

    df.to_csv(EXPORT_DIR / "feature_importance.csv", index=False)

def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    load_dotenv(ROOT / ".env")
    eng = create_engine(os.environ["DATABASE_URL"])

    export_cohort(eng)
    export_model_performance()
    export_feature_importance()

    print("✅ Wrote CSVs to exports/bi/:")
    for f in ["cohort_overview.csv","model_performance.csv","feature_importance.csv"]:
        print(" -", f)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    main()