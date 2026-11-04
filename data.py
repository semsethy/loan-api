"""Synthetic loan data shared by training and monitoring, so both use identical data."""
import numpy as np
import pandas as pd

FEATURES = ["amount_usd", "term_months", "monthly_income_usd", "previous_loans", "late_payments"]


def make_data(n=5000, seed=42, income_mean=400, amount_high=5001):
    """Synthetic loan histories: larger repayments relative to income and late payments raise default risk.

    income_mean and amount_high default to the training values. Lesson 5.6 changes them
    to simulate borrowers becoming poorer (for example, a flood season).
    """
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "amount_usd": rng.integers(100, amount_high, n),
        "term_months": rng.choice([3, 6, 12, 18, 24], n),
        "monthly_income_usd": rng.normal(income_mean, 150, n).clip(80, 2000).round(),
        "previous_loans": rng.poisson(1.2, n),
        "late_payments": rng.poisson(0.4, n),
    })
    monthly_repayment = df.amount_usd / df.term_months
    logit = (-5 + 3 * (monthly_repayment / df.monthly_income_usd)
             + 0.9 * df.late_payments - 0.15 * df.previous_loans)
    df["defaulted"] = rng.random(n) < 1 / (1 + np.exp(-logit))
    return df
