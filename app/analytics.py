"""Analytics functions for fraud investigation."""

import pandas as pd


def get_fraud_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate fraud trends over time."""
    if df.empty or "txn_date" not in df.columns or "is_fraud" not in df.columns:
        return pd.DataFrame()

    daily_stats = df.groupby("txn_date").agg({
        "is_fraud": ["sum", "count"]
    }).reset_index()

    daily_stats.columns = ["date", "fraud_count", "total_count"]
    daily_stats["fraud_rate"] = (daily_stats["fraud_count"] / daily_stats["total_count"] * 100).round(2)
    daily_stats["non_fraud_count"] = daily_stats["total_count"] - daily_stats["fraud_count"]

    return daily_stats.sort_values("date")


def get_geographic_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze fraud by country."""
    if df.empty or "country_std" not in df.columns or "is_fraud" not in df.columns:
        return pd.DataFrame()

    geo_stats = df.groupby("country_std").agg({
        "is_fraud": ["sum", "count"]
    }).reset_index()

    geo_stats.columns = ["country", "fraud_count", "total_count"]
    geo_stats["fraud_rate"] = (geo_stats["fraud_count"] / geo_stats["total_count"] * 100).round(2)
    geo_stats = geo_stats.sort_values("fraud_rate", ascending=False)

    return geo_stats


def get_top_risky_merchants(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Get top N merchants by fraud count."""
    if df.empty or "merchant_id_clean" not in df.columns or "is_fraud" not in df.columns:
        return pd.DataFrame()

    merchant_stats = df.groupby(["merchant_id_clean", "merchant_risk_tier"]).agg({
        "is_fraud": ["sum", "count"]
    }).reset_index()

    merchant_stats.columns = ["merchant_id", "risk_tier", "fraud_count", "total_count"]
    merchant_stats["fraud_rate"] = (merchant_stats["fraud_count"] / merchant_stats["total_count"] * 100).round(2)
    merchant_stats = merchant_stats.sort_values("fraud_count", ascending=False).head(top_n)

    return merchant_stats


def get_top_risky_cards(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Get top N cards by fraud count or risk score."""
    if df.empty or "is_fraud" not in df.columns:
        return pd.DataFrame()

    # If card_id_clean exists, group by card; otherwise show high-risk transactions
    if "card_id_clean" in df.columns:
        agg_dict = {
            "is_fraud": ["sum", "count"],
            "amount": "sum"
        }
        # Only include risk_score if it exists
        if "risk_score" in df.columns:
            agg_dict["risk_score"] = "mean"
        
        card_stats = df.groupby("card_id_clean").agg(agg_dict).reset_index()
        
        if "risk_score" in df.columns:
            card_stats.columns = ["card_id", "fraud_count", "total_count", "avg_risk_score", "total_amount"]
        else:
            card_stats.columns = ["card_id", "fraud_count", "total_count", "total_amount"]
            card_stats["avg_risk_score"] = 0.5
        
        card_stats["fraud_rate"] = (card_stats["fraud_count"] / card_stats["total_count"] * 100).round(2)
        card_stats = card_stats.sort_values("fraud_count", ascending=False).head(top_n)
    else:
        if "risk_score" in df.columns and "txn_id_clean" in df.columns:
            high_risk = df.nlargest(top_n, "risk_score")[["txn_id_clean", "risk_score", "is_fraud", "amount"]].copy()
            high_risk.columns = ["transaction_id", "risk_score", "is_fraud", "amount"]
            return high_risk
        return pd.DataFrame()

    return card_stats


def get_channel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze fraud by channel."""
    if df.empty or "channel_std" not in df.columns or "is_fraud" not in df.columns:
        return pd.DataFrame()

    channel_stats = df.groupby("channel_std").agg({
        "is_fraud": ["sum", "count"]
    }).reset_index()

    channel_stats.columns = ["channel", "fraud_count", "total_count"]
    channel_stats["fraud_rate"] = (channel_stats["fraud_count"] / channel_stats["total_count"] * 100).round(2)
    channel_stats = channel_stats.sort_values("fraud_rate", ascending=False)

    return channel_stats


def get_hourly_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze fraud patterns by hour of day."""
    if df.empty or "is_fraud" not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    
    if "txn_ts" in df_copy.columns:
        df_copy["hour"] = pd.to_datetime(df_copy["txn_ts"], errors="coerce").dt.hour
    elif "txn_date" in df_copy.columns:
        return pd.DataFrame()
    else:
        return pd.DataFrame()

    df_copy = df_copy.dropna(subset=["hour"])

    if df_copy.empty:
        return pd.DataFrame()

    hourly_stats = df_copy.groupby("hour").agg({
        "is_fraud": ["sum", "count"]
    }).reset_index()

    hourly_stats.columns = ["hour", "fraud_count", "total_count"]
    hourly_stats["fraud_rate"] = (hourly_stats["fraud_count"] / hourly_stats["total_count"] * 100).round(2)
    hourly_stats = hourly_stats.sort_values("hour")

    return hourly_stats

