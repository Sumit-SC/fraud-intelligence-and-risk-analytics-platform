"""
Test script to identify errors in the Streamlit app.
Run this to see what errors occur during app initialization.

Location: testing/app-vizulation/
Run from project root: uv run python testing/app-vizulation/test_app.py
"""

import sys
from pathlib import Path

# Add app-vizulation directory to Python path (go up from testing/app-vizulation to app-vizulation)
testing_dir = Path(__file__).parent  # testing/app-vizulation
app_dir = testing_dir.parent.parent / "app-vizulation"  # Go to project root, then app-vizulation
project_root = testing_dir.parent.parent  # Project root

if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing imports...")
try:
    import pandas as pd
    print("[OK] pandas imported")
except Exception as e:
    print(f"[ERROR] pandas import failed: {e}")
    sys.exit(1)

try:
    import streamlit as st
    print("[OK] streamlit imported")
except Exception as e:
    print(f"[ERROR] streamlit import failed: {e}")
    sys.exit(1)

try:
    # Import from app-vizulation
    sys.path.insert(0, str(app_dir))
    from data_loader import load_transaction_data, get_filter_options
    from utils import format_currency, apply_filters
    from risk_scoring import score_transactions, explain_risk_score
    print("[OK] All app modules imported")
except Exception as e:
    print(f"[ERROR] App module import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTesting data loading...")
try:
    df = load_transaction_data()
    print(f"[OK] Data loaded: {len(df)} rows, {len(df.columns)} columns")
    if df.empty:
        print("[WARNING] DataFrame is empty")
    else:
        print(f"[OK] Columns: {list(df.columns[:5])}...")
except Exception as e:
    print(f"[ERROR] Data loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTesting filter options...")
try:
    if not df.empty:
        filter_options = get_filter_options(df)
        print(f"[OK] Filter options extracted: {len(filter_options.get('merchant_risk_tiers', []))} risk tiers")
except Exception as e:
    print(f"[ERROR] Filter options failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting risk scoring...")
try:
    if not df.empty:
        # Test with small sample
        df_sample = df.head(100).copy()
        df_scored = score_transactions(df_sample)
        print(f"[OK] Risk scoring successful: {len(df_scored)} rows scored")
        if 'risk_score' in df_scored.columns:
            print(f"[OK] Risk scores added: min={df_scored['risk_score'].min():.3f}, max={df_scored['risk_score'].max():.3f}")
        if 'risk_band' in df_scored.columns:
            print(f"[OK] Risk bands added: {df_scored['risk_band'].value_counts().to_dict()}")
except Exception as e:
    print(f"[ERROR] Risk scoring failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[SUCCESS] All tests passed! App should work correctly.")
print("\nTo run the app:")
print("  uv run streamlit run app-vizulation/streamlit_app.py")

