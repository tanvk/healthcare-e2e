import json, os, joblib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score, accuracy_score,
    confusion_matrix, classification_report
)

EXPORT_DIR = Path("exports")
ART_DIR = Path("artifacts")
RANDOM_STATE = 42

def load_splits():
    feats_dir = EXPORT_DIR / "features"
    train = pd.read_csv(feats_dir / "train.csv")
    val   = pd.read_csv(feats_dir / "val.csv")
    test  = pd.read_csv(feats_dir / "test.csv")

    y_train = train.pop("readmit_30d").astype(int)
    y_val   = val.pop("readmit_30d").astype(int)
    y_test  = test.pop("readmit_30d").astype(int)
    return (train, y_train), (val, y_val), (test, y_test)

def metrics(y_true, prob):
    pred = (prob >= 0.5).astype(int)
    return {
        "auc_roc": float(roc_auc_score(y_true, prob)),
        "avg_precision": float(average_precision_score(y_true, prob)),
        "f1": float(f1_score(y_true, pred)),
        "accuracy": float(accuracy_score(y_true, pred)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
    }

def main():
    (ART_DIR).mkdir(exist_ok=True, parents=True)
    (EXPORT_DIR / "ml").mkdir(exist_ok=True, parents=True)

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_splits()

    meta = json.loads((EXPORT_DIR / "features" / "meta.json").read_text())                                      # BASIC SCHEMA FOR META.JSON
    categoricals = [c for c in meta["categoricals"] if c in X_train.columns]
    numericals = [c for c in meta["numericals"] if c in X_train.columns]

    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")),                                          # PRE-PROCESSES
                         ("scale", StandardScaler())])
    cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                         ("onehot", OneHotEncoder(handle_unknown="ignore"))])

    pre = ColumnTransformer(
        transformers=[
            ("num", num_pipe, numericals),
            ("cat", cat_pipe, categoricals),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=200, class_weight="balanced", random_state=RANDOM_STATE)                   # MODEL - LOGISTIC REGRESSION

    # from xgboost import XGBClassifier                                                                          # MODEL - XG-BOOST
    # clf = XGBClassifier(
    #     n_estimators=300,
    #     max_depth=4,
    #     learning_rate=0.05,
    #     subsample=0.9,
    #     colsample_bytree=0.9,
    #     reg_lambda=1.0,
    #     random_state=RANDOM_STATE,
    #     eval_metric="logloss",
    #     scale_pos_weight=(y_train.value_counts()[0] / y_train.value_counts()[1])
    # )

    pipe = Pipeline([("pre", pre), ("clf", clf)])

    pipe.fit(X_train, y_train)                                                                                  # FIT MODEL ON TRAIN, EARLY SANITY ON VALIDATION
    val_prob = pipe.predict_proba(X_val)[:, 1]
    test_prob = pipe.predict_proba(X_test)[:, 1]

    val_metrics  = metrics(y_val,  val_prob)
    test_metrics = metrics(y_test, test_prob)

    joblib.dump(pipe, ART_DIR / "model_pipeline.pkl")                                                           # PERSIST ATRIFACTS
    (EXPORT_DIR / "ml" / "val_metrics.json").write_text(json.dumps(val_metrics, indent=2))
    (EXPORT_DIR / "ml" / "test_metrics.json").write_text(json.dumps(test_metrics, indent=2))

    print("Saved artifacts: artifacts/model_pipeline.pkl")
    print("Val:", val_metrics)
    print("Test:", test_metrics)

    report = classification_report(y_test, (test_prob>=0.5).astype(int))                                        # REPORT FOR TEST
    (EXPORT_DIR / "ml" / "classification_report.txt").write_text(report)

if __name__ == "__main__":
    main()