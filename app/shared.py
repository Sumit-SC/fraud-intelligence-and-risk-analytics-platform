"""Shared utilities for multi-page Streamlit app."""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.data_loader import get_filter_options, load_transaction_data
from app.risk_scoring import score_transactions, _load_models
from app.utils import apply_filters


@st.cache_data(show_spinner=False, ttl=3600)
def _load_cached_data():
    """Cache data loading with 1 hour TTL to reduce memory usage."""
    try:
        return load_transaction_data()
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def _get_filter_options_cached(df_hash):
    """Cache filter options calculation."""
    df_full = _load_cached_data()
    if df_full.empty:
        return {
            "merchant_risk_tiers": [],
            "channels": [],
            "countries": []
        }
    return get_filter_options(df_full)


def get_filtered_data(skip_scoring=False):
    """Load data and apply filters from session state.
    
    Args:
        skip_scoring: If True, skip risk scoring for faster loading
    Returns:
        Tuple of (df_full, df_filtered)
    """
    df_full = _load_cached_data()
    
    if df_full.empty:
        return df_full, df_full
    
    if "date_start" not in st.session_state:
        if "txn_date" in df_full.columns:
            date_min = df_full["txn_date"].min()
            date_max = df_full["txn_date"].max()
            st.session_state["date_start"] = pd.Timestamp(date_min)
            st.session_state["date_end"] = pd.Timestamp(date_max)
        else:
            st.session_state["date_start"] = None
            st.session_state["date_end"] = None
    
    date_start = st.session_state.get("date_start")
    date_end = st.session_state.get("date_end")
    merchant_risk_tier = st.session_state.get("merchant_risk_filter", "All")
    channel = st.session_state.get("channel_filter", "All")
    country = st.session_state.get("country_filter", "All")
    fraud_filter = st.session_state.get("fraud_filter", "All")
    
    # Apply filters
    df_filtered = apply_filters(
        df_full,
        date_start=date_start,
        date_end=date_end,
        merchant_risk_tier=merchant_risk_tier,
        channel=channel,
        country=country,
        fraud_filter=fraud_filter
    )
    
    if not df_filtered.empty and not skip_scoring:
        feature_columns = [
            "txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d",
            "is_high_risk_merchant", "is_emulator_device"
        ]
        available_features = [col for col in feature_columns if col in df_full.columns]
        
        # Limit scoring to prevent resource exhaustion on free tier
        max_initial_score = 3000
        try:
            if len(df_filtered) > max_initial_score:
                df_to_score = df_filtered.head(max_initial_score).copy()
                df_scored = score_transactions(df_to_score)
                df_remaining = df_filtered.iloc[max_initial_score:].copy()
                df_remaining['risk_score'] = 0.5
                df_remaining['risk_band'] = 'MEDIUM'
                df_filtered = pd.concat([df_scored, df_remaining], ignore_index=True)
            else:
                df_filtered = score_transactions(df_filtered)
        except Exception:
            if 'risk_score' not in df_filtered.columns:
                df_filtered['risk_score'] = 0.5
            if 'risk_band' not in df_filtered.columns:
                df_filtered['risk_band'] = 'MEDIUM'
    elif skip_scoring:
        # Add placeholder scores if skipping scoring (for pages that don't need real scores)
        if 'risk_score' not in df_filtered.columns:
            df_filtered['risk_score'] = 0.5
        if 'risk_band' not in df_filtered.columns:
            df_filtered['risk_band'] = 'MEDIUM'
    # If df_filtered is empty, add placeholder columns
    elif df_filtered.empty:
        df_filtered['risk_score'] = 0.5
        df_filtered['risk_band'] = 'MEDIUM'
    
    return df_full, df_filtered


def setup_sidebar_filters():
    """Setup sidebar filters using cached data."""
    df_full = _load_cached_data()
    
    if df_full.empty:
        st.sidebar.error("⚠️ No data available")
        return df_full
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Date range filter
    if "txn_date" in df_full.columns:
        date_min = df_full["txn_date"].min()
        date_max = df_full["txn_date"].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
            key="date_range_filter"
        )
        
        date_start = pd.Timestamp(date_range[0]) if len(date_range) > 0 else None
        date_end = pd.Timestamp(date_range[1]) if len(date_range) > 1 else None
    else:
        date_start = None
        date_end = None
    
    # Get filter options (use cached version)
    filter_options = _get_filter_options_cached(hash(tuple(df_full.columns)))
    
    # Merchant risk tier filter
    merchant_risk_tier = st.sidebar.selectbox(
        "Merchant Risk Tier",
        options=["All"] + filter_options["merchant_risk_tiers"],
        key="merchant_risk_filter"
    )
    
    # Channel filter
    channel = st.sidebar.selectbox(
        "Channel",
        options=["All"] + filter_options["channels"],
        key="channel_filter"
    )
    
    # Country filter
    country = st.sidebar.selectbox(
        "Country",
        options=["All"] + filter_options["countries"],
        key="country_filter"
    )
    
    # Fraud filter
    fraud_filter = st.sidebar.selectbox(
        "Fraud Status",
        options=["All", "Fraud Only", "Non-Fraud Only"],
        key="fraud_filter"
    )
    
    # Store processed date range in session state (widgets auto-store their values)
    # Date range needs processing from tuple to timestamps
    st.session_state["date_start"] = date_start
    st.session_state["date_end"] = date_end
    # Selectbox values are automatically stored in session state with their keys
    
    # Display filter status
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Filter Status")
    
    if date_start or date_end:
        date_str = f"{date_start.strftime('%Y-%m-%d') if date_start else 'Start'} to {date_end.strftime('%Y-%m-%d') if date_end else 'End'}"
        st.sidebar.markdown(f"**📅 Date Range:** {date_str}")
    else:
        st.sidebar.markdown("**📅 Date Range:** All")
    
    st.sidebar.markdown(f"**🏪 Merchant Risk:** {merchant_risk_tier}")
    st.sidebar.markdown(f"**📱 Channel:** {channel}")
    st.sidebar.markdown(f"**🌍 Country:** {country}")
    st.sidebar.markdown(f"**⚠️ Fraud Status:** {fraud_filter}")
    
    return df_full

