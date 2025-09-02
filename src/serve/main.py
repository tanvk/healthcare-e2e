import os
import joblib
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

ART_DIR = Path("artifacts")                                                                     # CONFIG
MODEL_PATH = ART_DIR / "model_pipeline.pkl"

app = FastAPI(title="Healthcare Readmission API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    sex: str = Field(..., description="M or F")
    age: int = Field(..., ge=0, le=120)
    length_of_stay_days: float
    avg_hemo: Optional[float] = None
    avg_glucose: Optional[float] = None
    avg_creatinine: Optional[float] = None
    avg_wbc: Optional[float] = None
    avg_platelets: Optional[float] = None

class PredictResponse(BaseModel):
    probability: float
    label: int

@app.on_event("startup")                                                                        # LOAD MODEL ON STARTUP
def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found at {MODEL_PATH}. Train first.")
    app.state.model = joblib.load(MODEL_PATH)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    row = {
        "sex": req.sex,
        "age": req.age,
        "length_of_stay_days": req.length_of_stay_days,
        "avg_hemo": req.avg_hemo,
        "avg_glucose": req.avg_glucose,
        "avg_creatinine": req.avg_creatinine,
        "avg_wbc": req.avg_wbc,
        "avg_platelets": req.avg_platelets,
    }
    import pandas as pd
    X = pd.DataFrame([row])
    prob = app.state.model.predict_proba(X)[:, 1][0]
    label = int(prob >= 0.5)
    return {"probability": float(prob), "label": label}