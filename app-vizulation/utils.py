"""
Utility functions for Streamlit visualization app.
"""

from typing import Optional
import pandas as pd


def format_currency(amount: float) -> str:
    """
    Format amount as currency string.

    Args:
        amount: Transaction amount

    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    if pd.isna(amount):
        return "N/A"
    return f"${amount:,.2f}"


def apply_filters(
    df: pd.DataFrame,
    date_start: Optional[pd.Timestamp],
    date_end: Optional[pd.Timestamp],
    merchant_risk_tier: Optional[str],
    channel: Optional[str],
    country: Optional[str],
    fraud_filter: Optional[str]
) -> pd.DataFrame:
    """
    Apply sidebar filters to transaction DataFrame.

    Args:
        df: Full transaction DataFrame
        date_start: Start date filter
        date_end: End date filter
        merchant_risk_tier: Merchant risk tier filter
        channel: Channel filter
        country: Country filter
        fraud_filter: "All", "Fraud Only", or "Non-Fraud Only"

    Returns:
        Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # Date range filter
    if "txn_date" in filtered_df.columns:
        if date_start:
            filtered_df = filtered_df[filtered_df["txn_date"] >= date_start]
        if date_end:
            filtered_df = filtered_df[filtered_df["txn_date"] <= date_end]
    
    # Merchant risk tier filter
    if merchant_risk_tier and merchant_risk_tier != "All":
        if "merchant_risk_tier" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["merchant_risk_tier"] == merchant_risk_tier]
    
    # Channel filter
    if channel and channel != "All":
        if "channel_std" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["channel_std"] == channel]
    
    # Country filter
    if country and country != "All":
        if "country_std" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["country_std"] == country]
    
    # Fraud filter
    if fraud_filter and fraud_filter != "All":
        if "is_fraud" in filtered_df.columns:
            if fraud_filter == "Fraud Only":
                filtered_df = filtered_df[filtered_df["is_fraud"] == True]
            elif fraud_filter == "Non-Fraud Only":
                filtered_df = filtered_df[filtered_df["is_fraud"] == False]
    
    return filtered_df

