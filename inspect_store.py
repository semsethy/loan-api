"""Look inside MLflow's backend store (a SQLite file) and artifact store (a folder)."""
import sqlite3
from pathlib import Path

db = sqlite3.connect("mlflow.db")
tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
print(len(tables), "tables, including:", [t for t in tables if t in ("experiments", "runs", "params", "latest_metrics", "registered_models", "model_versions")])

# Best run by AUC, straight from SQL: the same data the UI shows
for name, auc in db.execute("""
    SELECT r.name, ROUND(m.value, 3)
    FROM runs AS r JOIN latest_metrics AS m ON m.run_uuid = r.run_uuid
    WHERE m.key = 'auc'
    ORDER BY m.value DESC"""):
    print(f"{auc}  {name}")

# The artifact store is just files: every logged ROC chart
for png in sorted(Path("mlartifacts").rglob("roc_curve.png")):
    print(png)
