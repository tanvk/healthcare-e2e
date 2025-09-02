import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Healthcare Readmission", page_icon="🩺", layout="centered")
st.title("🩺 Readmission Risk Predictor")

st.markdown("Enter encounter details and get an estimated 30-day readmission probability.")

with st.form("predict_form"):
    col1, col2 = st.columns(2)
    with col1:
        sex = st.selectbox("Sex", ["F", "M"])
        age = st.number_input("Age", min_value=0, max_value=120, value=65)
        los = st.number_input("Length of stay (days)", min_value=0.0, value=3.2, step=0.1)
    with col2:
        avg_hemo = st.number_input("Avg Hemoglobin", value=12.5, step=0.1)
        avg_glucose = st.number_input("Avg Glucose", value=140.0, step=1.0)
        avg_creatinine = st.number_input("Avg Creatinine", value=1.0, step=0.1)
        avg_wbc = st.number_input("Avg WBC", value=8.0, step=0.1)
        avg_platelets = st.number_input("Avg Platelets", value=230.0, step=1.0)

    submitted = st.form_submit_button("Predict")

if submitted:
    payload = {
        "sex": sex,
        "age": int(age),
        "length_of_stay_days": float(los),
        "avg_hemo": float(avg_hemo),
        "avg_glucose": float(avg_glucose),
        "avg_creatinine": float(avg_creatinine),
        "avg_wbc": float(avg_wbc),
        "avg_platelets": float(avg_platelets),
    }
    try:
        res = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        prob = data["probability"]
        label = data["label"]
        st.metric("Readmission probability", f"{prob:.2%}")
        st.success("Prediction: HIGH RISK" if label == 1 else "Prediction: LOW RISK")
        st.code(payload, language="json")
    except Exception as e:
        st.error(f"Request failed: {e}")
        st.info(f"Is the API running at {API_URL}? Try: curl {API_URL}/health")