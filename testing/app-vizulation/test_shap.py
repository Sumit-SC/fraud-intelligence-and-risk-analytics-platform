"""Test SHAP explanations

Location: testing/app-vizulation/
Run from project root: uv run python testing/app-vizulation/test_shap.py
"""

import sys
from pathlib import Path

# Add paths (go up from testing/app-vizulation to app-vizulation)
testing_dir = Path(__file__).parent  # testing/app-vizulation
app_dir = testing_dir.parent.parent / "app-vizulation"  # Go to project root, then app-vizulation
project_root = testing_dir.parent.parent  # Project root

sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

from risk_scoring import score_transactions, explain_risk_score, get_shap_values, SHAP_AVAILABLE
from data_loader import load_transaction_data

print("=" * 60)
print("TESTING SHAP EXPLANATIONS")
print("=" * 60)

print(f"\nSHAP Available: {SHAP_AVAILABLE}")

# Load and train
df = load_transaction_data().head(50000)
df_scored = score_transactions(df)

# Test explanations
row = df_scored.iloc[0]
print(f"\nTesting transaction: {row.get('txn_id_clean', 'N/A')}")
print(f"Risk Score: {row.get('risk_score', 0):.3f}")
print(f"Risk Band: {row.get('risk_band', 'N/A')}")

# Get SHAP values
shap_data = get_shap_values(row)
print(f"\nSHAP Data Available: {shap_data is not None}")

if shap_data:
    print(f"Features: {shap_data['feature_names']}")
    print(f"SHAP Values: {shap_data['shap_values']}")
    print(f"Base Value: {shap_data['base_value']}")

# Get explanations
explanations = explain_risk_score(row, use_shap=True)
print(f"\nExplanations ({len(explanations)}):")
for i, exp in enumerate(explanations, 1):
    print(f"  {i}. {exp}")

print("\n" + "=" * 60)

