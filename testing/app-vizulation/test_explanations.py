"""Test explanations functionality

Location: testing/app-vizulation/
Run from project root: uv run python testing/app-vizulation/test_explanations.py
"""

import sys
from pathlib import Path

# Add paths (go up from testing/app-vizulation to app-vizulation)
testing_dir = Path(__file__).parent  # testing/app-vizulation
app_dir = testing_dir.parent.parent / "app-vizulation"  # Go to project root, then app-vizulation
project_root = testing_dir.parent.parent  # Project root

sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

from risk_scoring import score_transactions, explain_risk_score, get_model_info
from data_loader import load_transaction_data
import pandas as pd

print("=" * 60)
print("TESTING EXPLANATIONS")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
df = load_transaction_data()
print(f"  Loaded {len(df)} rows")

# Train model
print("\n[2] Training model...")
df_sample = df.head(5000)
df_scored = score_transactions(df_sample)
model_info = get_model_info()
print(f"  Model status: {model_info.get('status')}")
print(f"  Features: {model_info.get('features', [])}")

# Test explanations on multiple rows
print("\n[3] Testing explanations...")
for i in [0, 10, 50, 100]:
    if i < len(df_scored):
        row = df_scored.iloc[i]
        explanations = explain_risk_score(row)
        print(f"\n  Row {i}:")
        print(f"    Risk Score: {row.get('risk_score', 'N/A')}")
        print(f"    Risk Band: {row.get('risk_band', 'N/A')}")
        print(f"    Explanations: {len(explanations)}")
        if explanations:
            for j, exp in enumerate(explanations[:3], 1):
                print(f"      {j}. {exp[:80]}...")
        else:
            print("      [NO EXPLANATIONS GENERATED]")
            # Debug: Check feature values
            print(f"      Features: txns_last_24h={row.get('txns_last_24h', 'N/A')}, "
                  f"declined_txns_last_24h={row.get('declined_txns_last_24h', 'N/A')}, "
                  f"merchant_fraud_rate_30d={row.get('merchant_fraud_rate_30d', 'N/A')}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

