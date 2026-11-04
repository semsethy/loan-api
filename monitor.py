"""Simulate 14 days of production traffic and log drift metrics to MLflow."""
import mlflow

from data import FEATURES, make_data
from psi import psi

reference = make_data(n=5000, seed=42)                     # what the model was trained on
model = mlflow.pyfunc.load_model("models:/loan-default@champion")

mlflow.set_experiment("loan-default-monitoring")
with mlflow.start_run(run_name="daily-drift-check"):
    for day in range(1, 15):
        # Incomes slowly fall and loan sizes rise over two weeks
        today = make_data(n=400, seed=100 + day, income_mean=400 - 8 * day, amount_high=5001)
        for feature in ["monthly_income_usd", "amount_usd", "late_payments"]:
            mlflow.log_metric(f"psi_{feature}", psi(reference[feature], today[feature]), step=day)
        mean_risk = float(model.predict(today[FEATURES])[:, 1].mean())
        mlflow.log_metric("mean_predicted_default", mean_risk, step=day)
        mlflow.log_metric("actual_default_rate", float(today.defaulted.mean()), step=day)
        print(f"day {day:>2}: income PSI={psi(reference.monthly_income_usd, today.monthly_income_usd):.3f}  "
              f"mean risk={mean_risk:.3f}")
