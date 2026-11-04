-- Runs once, the first time the database volume is created.
CREATE TABLE IF NOT EXISTS applications (
    id                  SERIAL PRIMARY KEY,
    borrower_id         INTEGER      NOT NULL,
    amount_usd          INTEGER      NOT NULL CHECK (amount_usd BETWEEN 100 AND 5000),
    term_months         INTEGER      NOT NULL CHECK (term_months IN (3, 6, 12, 18, 24)),
    monthly_income_usd  NUMERIC(10,2) NOT NULL CHECK (monthly_income_usd > 0),
    previous_loans      INTEGER      NOT NULL CHECK (previous_loans >= 0),
    late_payments       INTEGER      NOT NULL CHECK (late_payments >= 0),
    status              TEXT         NOT NULL DEFAULT 'pending'
                                     CHECK (status IN ('pending', 'approved', 'rejected')),
    default_probability NUMERIC(4,3),
    risk_band           TEXT CHECK (risk_band IN ('low', 'medium', 'high')),
    model_version       TEXT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);
