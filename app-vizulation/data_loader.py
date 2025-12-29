"""Data loader for Streamlit visualization app."""

from pathlib import Path
import pandas as pd


def load_transaction_data(csv_path: str = "data/bi/feat_transactions_risk_bi.csv") -> pd.DataFrame:
    """Load transaction data from BI export CSV."""
    project_root = Path(__file__).parent.parent
    csv_file = project_root / csv_path
    
    if not csv_file.exists():
        return pd.DataFrame(columns=[
            "txn_id_clean", "txn_ts", "txn_date", "amount", "channel_std", "country_std",
            "is_fraud", "is_declined", "txns_last_24h", "amount_vs_card_avg",
            "declined_txns_last_24h", "merchant_id_clean", "merchant_risk_tier",
            "merchant_txn_count_30d", "merchant_fraud_rate_30d",
            "is_high_risk_merchant", "is_emulator_device"
        ])
    
    df = pd.read_csv(csv_file)
    
    if "txn_date" in df.columns:
        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")
    if "txn_ts" in df.columns:
        df["txn_ts"] = pd.to_datetime(df["txn_ts"], errors="coerce")
    
    bool_columns = ["is_fraud", "is_declined", "is_high_risk_merchant", "is_emulator_device"]
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """Extract unique filter options from the dataset."""
    if df.empty:
        return {
            "merchant_risk_tiers": [],
            "channels": [],
            "countries": []
        }
    
    return {
        "merchant_risk_tiers": sorted(df["merchant_risk_tier"].dropna().unique().tolist()) if "merchant_risk_tier" in df.columns else [],
        "channels": sorted(df["channel_std"].dropna().unique().tolist()) if "channel_std" in df.columns else [],
        "countries": sorted(df["country_std"].dropna().unique().tolist()) if "country_std" in df.columns else []
    }

