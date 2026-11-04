"""Loan Application Service: stores loan applications and scores their default risk."""
from contextlib import asynccontextmanager
import os

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from schemas import Application, ApplicationCreate, LoanFeatures, Prediction

ml = {}            # filled at start-up: {"predict_proba": ..., "version": ..., "features": [...]}
APPLICATIONS = {}  # in-memory store; resets when the server restarts
MODEL_PATH = os.getenv("MODEL_PATH", "model.joblib")
MODEL_NAME = os.getenv("MODEL_NAME", "loan-default")
MODEL_ALIAS = os.getenv("MODEL_ALIAS", "champion")
FEATURES = ["amount_usd", "term_months", "monthly_income_usd", "previous_loans", "late_payments"]


def load_from_registry():
    """Module 5: the champion from the MLflow registry (needs MLFLOW_TRACKING_URI)."""
    import mlflow  # imported only here, so the production image does not need MLflow
    from mlflow import MlflowClient

    model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@{MODEL_ALIAS}")
    version = MlflowClient().get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS).version
    return {"predict_proba": model.predict, "version": version, "features": FEATURES}


def load_from_file():
    """Modules 4 and 6: the model file trained into the image (or by train.py)."""
    bundle = joblib.load(MODEL_PATH)
    return {"predict_proba": bundle["model"].predict_proba, "version": bundle["version"],
            "features": bundle["features"]}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A tracking server is configured: use the registry. Otherwise (CI, Render): use the file.
    ml.update(load_from_registry() if os.getenv("MLFLOW_TRACKING_URI") else load_from_file())
    yield
    ml.clear()


app = FastAPI(title="Loan Application Service", version="1.0.0", lifespan=lifespan)


def score(features: LoanFeatures) -> Prediction:
    X = pd.DataFrame([features.model_dump()])[ml["features"]]
    probability = float(ml["predict_proba"](X)[0, 1])
    band = "low" if probability < 0.2 else "medium" if probability < 0.5 else "high"
    return Prediction(default_probability=round(probability, 3), risk_band=band, model_version=ml["version"])


@app.get("/health")
def health():
    return {"status": "ok", "model_version": ml.get("version")}


@app.post("/api/v1/predictions", response_model=Prediction)
def predict(features: LoanFeatures):
    return score(features)


@app.post("/api/v1/applications", response_model=Application, status_code=201)
def create_application(body: ApplicationCreate):
    new = Application(id=7781 + len(APPLICATIONS), status="pending",
                      prediction=score(body), **body.model_dump())
    APPLICATIONS[new.id] = new
    return new


@app.get("/api/v1/applications", response_model=list[Application])
def list_applications():
    return list(APPLICATIONS.values())


@app.get("/api/v1/applications/{application_id}", response_model=Application)
def get_application(application_id: int):
    if application_id not in APPLICATIONS:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    return APPLICATIONS[application_id]
