"""Train several loan-default models and track every run in MLflow."""
import matplotlib
matplotlib.use("Agg")  # draw charts without a screen

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data import FEATURES, make_data

mlflow.set_experiment("loan-default")  # created on first use

df = make_data()
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURES], df.defaulted, test_size=0.2, random_state=42)

candidates = [
    ("logreg", {"C": 0.1, "class_weight": None}),
    ("logreg", {"C": 0.1, "class_weight": "balanced"}),
    ("forest", {"max_depth": 4, "class_weight": None}),
    ("forest", {"max_depth": 8, "class_weight": "balanced"}),
    ("logreg", {"C": 1.0, "class_weight": "balanced"}),     # weaker regularisation
    ("forest", {"max_depth": 6, "class_weight": "balanced"}),  # between depth 4 and 8
]

for kind, params in candidates:
    if kind == "logreg":
        model = make_pipeline(StandardScaler(), LogisticRegression(**params))
    else:
        model = RandomForestClassifier(n_estimators=200, random_state=42, **params)

    with mlflow.start_run(run_name=f"{kind}-" + "-".join(f"{k}={v}" for k, v in params.items()),
                          tags={"batch": "project"}):  # marks the six runs compared in the project
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        predicted = proba >= 0.5

        mlflow.log_params({"model": kind, **{k: str(v) for k, v in params.items()}})
        mlflow.log_metrics({
            "auc": roc_auc_score(y_test, proba),
            "recall": recall_score(y_test, predicted),        # share of real defaults we catch
            "precision": precision_score(y_test, predicted),  # share of flagged loans that do default
        })
        mlflow.log_figure(RocCurveDisplay.from_predictions(y_test, proba).figure_, "roc_curve.png")
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=infer_signature(X_test, model.predict_proba(X_test)),
            input_example=X_test.head(3),
            pyfunc_predict_fn="predict_proba",  # serving returns probabilities, not 0/1
            # MLflow saves scikit-learn models with skops, which refuses unknown types on load.
            # Tree is the node store inside every random forest; we trust it because we trained this model.
            skops_trusted_types=["sklearn.tree._tree.Tree"] if kind == "forest" else None,
        )
        print(f"{kind:<6} {params}  auc={roc_auc_score(y_test, proba):.3f}  "
              f"recall={recall_score(y_test, predicted):.3f}  precision={precision_score(y_test, predicted):.3f}")
