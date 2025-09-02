# Healthcare Predictive Analytics (End-to-End ML Project)

🚀 **End-to-end machine learning pipeline** for predicting healthcare outcomes using synthetic patient data.  
This project demonstrates skills in **data engineering, ML modeling, APIs, dashboards, and MLOps**.

---

## 📂 Project Structure
db/ # Database schema & seed scripts
dbt/ # dbt models for transformations
src/etl/ # ETL & feature engineering
src/ml/ # Model training & evaluation
src/serve/ # FastAPI app for model serving
app/ # Streamlit UI
exports/ # CSVs for Tableau Public dashboards
ops/ # CI/CD configs, Dockerfiles
tests/ # Unit tests

---

## 🛠️ Tech Stack
- **Database:** PostgreSQL (Neon/Supabase free-tier)
- **Transforms:** dbt Core
- **ML:** Python (scikit-learn, XGBoost, SHAP, MLflow)
- **API:** FastAPI
- **UI:** Streamlit
- **Analytics:** Tableau Public (via CSV extracts)
- **CI/CD:** GitHub Actions
- **Containerization:** Docker (optional)

---

## ✅ Features
- Synthetic healthcare dataset loaded into Postgres  
- dbt models for clean, analytics-ready tables  
- ML pipeline with explainability (SHAP)  
- REST API for real-time predictions  
- Interactive Streamlit web app  
- Tableau dashboard for stakeholders  
- CI/CD with linting, testing, and automated exports  

---

## 🔗 Links (will be added)
- **Live Streamlit App:** [coming soon]  
- **FastAPI Endpoint:** [coming soon]  
- **Tableau Dashboard:** [coming soon]

---

## ⚠️ Data Privacy
No PHI is included. All datasets are synthetic and for demo purposes only.