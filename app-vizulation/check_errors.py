"""
Quick error check script for the Streamlit app.
Run this to identify any import or runtime errors.
"""

import sys
from pathlib import Path

# Add paths
app_dir = Path(__file__).parent
project_root = app_dir.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

print("=" * 60)
print("ERROR CHECK FOR STREAMLIT APP")
print("=" * 60)

# Test 1: Basic imports
print("\n[1] Testing basic imports...")
try:
    import pandas as pd
    import streamlit as st
    print("  OK: pandas and streamlit imported")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Test 2: App module imports
print("\n[2] Testing app module imports...")
try:
    from data_loader import load_transaction_data, get_filter_options
    from utils import format_currency, apply_filters
    from risk_scoring import score_transactions, explain_risk_score, get_model_info
    print("  OK: All app modules imported")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Data loading
print("\n[3] Testing data loading...")
try:
    df = load_transaction_data()
    print(f"  OK: Data loaded - {len(df)} rows")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Model training
print("\n[4] Testing model training...")
try:
    if not df.empty and "is_fraud" in df.columns:
        df_sample = df.head(1000)
        df_scored = score_transactions(df_sample)
        model_info = get_model_info()
        print(f"  OK: Model status - {model_info.get('status')}")
    else:
        print("  WARNING: No fraud labels in data")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Risk explanation
print("\n[5] Testing risk explanation...")
try:
    if not df_scored.empty:
        row = df_scored.iloc[0]
        explanations = explain_risk_score(row)
        print(f"  OK: Generated {len(explanations)} explanations")
        if explanations:
            print(f"  Sample: {explanations[0][:80]}...")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Streamlit components (simulated)
print("\n[6] Testing Streamlit component usage...")
try:
    # Simulate what the app does
    if "model_trained" not in st.session_state:
        st.session_state["model_trained"] = False
    print("  OK: Session state works")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL CHECKS PASSED - APP SHOULD WORK!")
print("=" * 60)
print("\nTo run the app:")
print("  uv run streamlit run app-vizulation/streamlit_app.py")

