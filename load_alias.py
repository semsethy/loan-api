"""Load whichever model version the 'champion' alias points to, and score two applicants."""
import mlflow
import pandas as pd
from mlflow import MlflowClient

NAME, ALIAS = "loan-default", "champion"

model = mlflow.pyfunc.load_model(f"models:/{NAME}@{ALIAS}")
version = MlflowClient().get_model_version_by_alias(NAME, ALIAS).version

applicants = pd.DataFrame([
    {"amount_usd": 1500, "term_months": 12, "monthly_income_usd": 350.0, "previous_loans": 1, "late_payments": 0},
    {"amount_usd": 4800, "term_months": 6, "monthly_income_usd": 250.0, "previous_loans": 0, "late_payments": 3},
])
probabilities = model.predict(applicants)[:, 1]  # column 1 = probability of default
print(f"{NAME} version {version} ({ALIAS}): {probabilities.round(3)}")
