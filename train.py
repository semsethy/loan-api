"""Train the loan default model and save it to a file the API loads at start-up.

Usage:
    python train.py                                         # version 1.0.0 -> model.joblib
    python train.py --version 1.1.0 --out models/model.joblib
"""
import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["amount_usd", "term_months", "monthly_income_usd", "previous_loans", "late_payments"]


def make_data(n=5000, seed=42):
    """Synthetic loan histories: larger repayments relative to income and late payments raise default risk."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "amount_usd": rng.integers(100, 5001, n),
        "term_months": rng.choice([3, 6, 12, 18, 24], n),
        "monthly_income_usd": rng.normal(400, 150, n).clip(80, 2000).round(),
        "previous_loans": rng.poisson(1.2, n),
        "late_payments": rng.poisson(0.4, n),
    })
    monthly_repayment = df.amount_usd / df.term_months
    logit = (-5 + 3 * (monthly_repayment / df.monthly_income_usd)
             + 0.9 * df.late_payments - 0.15 * df.previous_loans)
    df["defaulted"] = rng.random(n) < 1 / (1 + np.exp(-logit))
    return df


def main():
    parser = argparse.ArgumentParser(description="Train the loan default model.")
    parser.add_argument("--version", default="1.0.0", help="Version label stored with the model")
    parser.add_argument("--out", default="model.joblib", help="Where to save the model file")
    args = parser.parse_args()

    df = make_data()
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df.defaulted, test_size=0.2, random_state=42)
    model = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, class_weight="balanced"))
    model.fit(X_train, y_train)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "version": args.version, "features": FEATURES}, args.out)
    print(f"Saved model {args.version} to {args.out} (test AUC {auc:.3f})")


if __name__ == "__main__":
    main()
