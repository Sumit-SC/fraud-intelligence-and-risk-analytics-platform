"""Data loader for Streamlit app.

This module is optimized for Streamlit Community Cloud:
- avoid loading multi-million row CSVs into RAM
- use Polars lazy scanning for filters/aggregations
- only collect small, UI-needed subsets
"""

from pathlib import Path

import pandas as pd
import polars as pl


DEFAULT_BI_CSV = "data/bi/feat_transactions_risk_bi.csv"


def _resolve_csv(csv_path: str) -> Path:
    project_root = Path(__file__).parent.parent
    return project_root / csv_path


def _scan_transactions(csv_path: str = DEFAULT_BI_CSV) -> pl.LazyFrame:
    csv_file = _resolve_csv(csv_path)
    # ignore_errors=True helps when columns have occasional bad values (messy data vibe)
    return pl.scan_csv(
        csv_file,
        infer_schema_length=1000,
        ignore_errors=True,
    )


def load_transaction_data(
    csv_path: str = DEFAULT_BI_CSV,
    usecols: list[str] | None = None,
    n_rows: int | None = None,
) -> pd.DataFrame:
    """
    Legacy helper (pandas) kept for compatibility.
    Prefer `load_transactions_filtered()` for the Streamlit UI.
    """
    csv_file = _resolve_csv(csv_path)
    if not csv_file.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_file, usecols=usecols, nrows=n_rows)
    if "txn_date" in df.columns:
        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")
    if "txn_ts" in df.columns:
        df["txn_ts"] = pd.to_datetime(df["txn_ts"], errors="coerce")

    for col in ["is_fraud", "is_declined", "is_high_risk_merchant", "is_emulator_device"]:
        if col in df.columns:
            # keep as best-effort bool; do not enforce strict typing
            df[col] = df[col].astype(bool, errors="ignore")
    return df


def get_dataset_stats(csv_path: str = DEFAULT_BI_CSV) -> dict:
    """Return dataset-level stats without loading full CSV into memory."""
    csv_file = _resolve_csv(csv_path)
    if not csv_file.exists():
        return {"total_rows": 0, "date_min": None, "date_max": None}

    lf = _scan_transactions(csv_path)
    # Parse txn_date for bounds. Keep parsing tolerant.
    txn_date = pl.col("txn_date").cast(pl.Utf8).str.strptime(pl.Date, strict=False)
    out = (
        lf.select(
            pl.len().alias("total_rows"),
            txn_date.min().alias("date_min"),
            txn_date.max().alias("date_max"),
        )
        .collect(streaming=True)
        .to_dicts()
    )[0]
    return out


def get_filter_options(csv_path: str = DEFAULT_BI_CSV) -> dict:
    """Extract unique filter options with Polars (low-memory)."""
    csv_file = _resolve_csv(csv_path)
    if not csv_file.exists():
        return {"merchant_risk_tiers": [], "channels": [], "countries": []}

    lf = _scan_transactions(csv_path)

    def _unique_sorted(col: str) -> list:
        if col not in lf.collect_schema().names():
            return []
        vals = (
            lf.select(pl.col(col))
            .drop_nulls()
            .unique()
            .collect(streaming=True)
            .get_column(col)
            .to_list()
        )
        try:
            return sorted(vals)
        except Exception:
            return vals

    return {
        "merchant_risk_tiers": _unique_sorted("merchant_risk_tier"),
        "channels": _unique_sorted("channel_std"),
        "countries": _unique_sorted("country_std"),
    }


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


def compute_filtered_summary(
    date_start,
    date_end,
    merchant_risk_tier: str,
    channel: str,
    country: str,
    fraud_filter: str,
    csv_path: str = DEFAULT_BI_CSV,
) -> dict:
    """Compute filtered counts + basic stats without collecting all rows."""
    csv_file = _resolve_csv(csv_path)
    if not csv_file.exists():
        return {
            "filtered_rows": 0,
            "fraud_rows": 0,
            "date_min": None,
            "date_max": None,
            "amount_sum": None,
            "amount_avg": None,
        }

    lf = _scan_transactions(csv_path)
    schema = lf.collect_schema().names()

    # Build filter expression
    filters = []

    if "txn_date" in schema and (date_start is not None or date_end is not None):
        txn_date = pl.col("txn_date").cast(pl.Utf8).str.strptime(pl.Date, strict=False)
        if date_start is not None:
            filters.append(txn_date >= pl.lit(date_start))
        if date_end is not None:
            filters.append(txn_date <= pl.lit(date_end))

    if merchant_risk_tier and merchant_risk_tier != "All" and "merchant_risk_tier" in schema:
        filters.append(pl.col("merchant_risk_tier") == merchant_risk_tier)
    if channel and channel != "All" and "channel_std" in schema:
        filters.append(pl.col("channel_std") == channel)
    if country and country != "All" and "country_std" in schema:
        filters.append(pl.col("country_std") == country)

    if fraud_filter and fraud_filter != "All" and "is_fraud" in schema:
        is_fraud_bool = pl.col("is_fraud").cast(pl.Boolean, strict=False)
        if fraud_filter == "Fraud Only":
            filters.append(is_fraud_bool == True)
        elif fraud_filter == "Non-Fraud Only":
            filters.append(is_fraud_bool == False)

    if filters:
        combined = filters[0]
        for f in filters[1:]:
            combined = combined & f
        lf = lf.filter(combined)

    # Aggregations
    selects = [pl.len().alias("filtered_rows")]

    if "is_fraud" in schema:
        is_fraud_bool = pl.col("is_fraud").cast(pl.Boolean, strict=False)
        selects.append(is_fraud_bool.sum().alias("fraud_rows"))
    else:
        selects.append(pl.lit(0).alias("fraud_rows"))

    if "txn_date" in schema:
        txn_date = pl.col("txn_date").cast(pl.Utf8).str.strptime(pl.Date, strict=False)
        selects.append(txn_date.min().alias("date_min"))
        selects.append(txn_date.max().alias("date_max"))
    else:
        selects.append(pl.lit(None).alias("date_min"))
        selects.append(pl.lit(None).alias("date_max"))

    if "amount" in schema:
        amt = pl.col("amount").cast(pl.Float64, strict=False)
        selects.append(amt.sum().alias("amount_sum"))
        selects.append(amt.mean().alias("amount_avg"))
    else:
        selects.append(pl.lit(None).alias("amount_sum"))
        selects.append(pl.lit(None).alias("amount_avg"))

    out = lf.select(*selects).collect(streaming=True).to_dicts()[0]
    return out


def load_transactions_filtered(
    date_start,
    date_end,
    merchant_risk_tier: str,
    channel: str,
    country: str,
    fraud_filter: str,
    limit_rows: int,
    csv_path: str = DEFAULT_BI_CSV,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Load ONLY the rows needed for the UI (filtered + limited).
    This avoids loading the full dataset into memory.
    """
    csv_file = _resolve_csv(csv_path)
    if not csv_file.exists():
        return pd.DataFrame()

    lf = _scan_transactions(csv_path)
    schema = lf.collect_schema().names()

    # Columns needed by UI pages (subset)
    desired_cols = [
        "txn_id_clean",
        "txn_ts",
        "txn_date",
        "amount",
        "channel_std",
        "country_std",
        "is_fraud",
        "is_declined",
        "txns_last_24h",
        "amount_vs_card_avg",
        "declined_txns_last_24h",
        "merchant_id_clean",
        "merchant_risk_tier",
        "merchant_txn_count_30d",
        "merchant_fraud_rate_30d",
        "is_high_risk_merchant",
        "is_emulator_device",
        "risk_score",
        "risk_band",
    ]
    use_cols = [c for c in desired_cols if c in schema]
    lf = lf.select(use_cols)

    filters = []
    if "txn_date" in use_cols and (date_start is not None or date_end is not None):
        txn_date = pl.col("txn_date").cast(pl.Utf8).str.strptime(pl.Date, strict=False)
        if date_start is not None:
            filters.append(txn_date >= pl.lit(date_start))
        if date_end is not None:
            filters.append(txn_date <= pl.lit(date_end))

    if merchant_risk_tier and merchant_risk_tier != "All" and "merchant_risk_tier" in use_cols:
        filters.append(pl.col("merchant_risk_tier") == merchant_risk_tier)
    if channel and channel != "All" and "channel_std" in use_cols:
        filters.append(pl.col("channel_std") == channel)
    if country and country != "All" and "country_std" in use_cols:
        filters.append(pl.col("country_std") == country)

    if fraud_filter and fraud_filter != "All" and "is_fraud" in use_cols:
        is_fraud_bool = pl.col("is_fraud").cast(pl.Boolean, strict=False)
        if fraud_filter == "Fraud Only":
            filters.append(is_fraud_bool == True)
        elif fraud_filter == "Non-Fraud Only":
            filters.append(is_fraud_bool == False)

    if filters:
        combined = filters[0]
        for f in filters[1:]:
            combined = combined & f
        lf = lf.filter(combined)

    # Hard cap to protect Community Cloud
    # 20K rows is usually plenty for UI/analytics while keeping memory safe
    hard_cap = 20_000
    limit_rows = min(int(limit_rows), hard_cap)
    lf = lf.sample(n=limit_rows, with_replacement=False, seed=seed) if limit_rows > 0 else lf.head(0)

    df = lf.collect(streaming=True).to_pandas()

    # Light parsing (still no “cleaning”, just types for UI widgets)
    if "txn_date" in df.columns:
        df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")
    if "txn_ts" in df.columns:
        df["txn_ts"] = pd.to_datetime(df["txn_ts"], errors="coerce")
    for col in ["is_fraud", "is_declined", "is_high_risk_merchant", "is_emulator_device"]:
        if col in df.columns:
            df[col] = df[col].astype(bool, errors="ignore")
    return df

