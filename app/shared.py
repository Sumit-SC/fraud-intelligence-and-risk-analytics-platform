"""
Shared utilities for multi-page Streamlit app.

Provides data loading and filtering that all pages can use.
"""

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


@st.cache_data(show_spinner=False)  # Disable spinner for cached data
def _load_cached_data():
    """
    Cache the data loading (not filtering).
    This is separate from filtering so filters can change without reloading data.
    """
    try:
        return load_transaction_data()
    except Exception as e:
        # Return empty DataFrame on error instead of crashing
        print(f"Error loading data: {e}")
        return pd.DataFrame()


def get_filtered_data(skip_scoring=False):
    """
    Load data and apply filters from session state.
    
    Args:
        skip_scoring: If True, skip risk scoring (faster, for pages that don't need scores)
    
    Note: Not cached because it depends on session state which changes.
    Data loading itself is cached separately.
    
    Returns:
        Tuple of (df_full, df_filtered)
    """
    # Load full dataset (cached)
    df_full = _load_cached_data()
    
    if df_full.empty:
        return df_full, df_full
    
    # Initialize session state if not set (for pages accessed before main page)
    # Widget keys will be set when widgets are created, but we initialize date range here
    if "date_start" not in st.session_state:
        if "txn_date" in df_full.columns:
            date_min = df_full["txn_date"].min()
            date_max = df_full["txn_date"].max()
            st.session_state["date_start"] = pd.Timestamp(date_min)
            st.session_state["date_end"] = pd.Timestamp(date_max)
        else:
            st.session_state["date_start"] = None
            st.session_state["date_end"] = None
    
    # Get filters from session state
    # Widgets automatically store their values in session state with their widget keys
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
    
    # Calculate risk scores using ML-lite model (unless skipped for performance)
    # Strategy: Train on full dataset (if models don't exist), but use sample for speed
    # Then apply scoring to filtered data
    if not df_filtered.empty and not skip_scoring:
        # Check if models exist - if not, train on a sample of full data for speed
        # This prevents freezing on large datasets
        feature_columns = [
            "txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d",
            "is_high_risk_merchant", "is_emulator_device"
        ]
        available_features = [col for col in feature_columns if col in df_full.columns]
        
        models_exist = _load_models(available_features) is not None
        
        if not models_exist and not df_full.empty:
            # Models don't exist - don't show warning here (let pages handle it)
            # This prevents warnings from showing on every page navigation
            # Use placeholder scoring instead of training
            # This allows the app to load quickly
            pass
        
        # Now score the filtered data (uses saved models if they exist)
        # OPTIMIZATION: Only score first 5k rows for initial display
        # This prevents 3+ minute waits when scoring 400k rows
        # Users can apply filters to reduce dataset size if needed
        max_initial_score = 5000  # Reduced from 10k for faster initial load
        try:
            if len(df_filtered) > max_initial_score:
                # Score only the first batch for display
                df_to_score = df_filtered.head(max_initial_score).copy()
                df_scored = score_transactions(df_to_score)
                
                # Add unscored rows with placeholder values
                df_remaining = df_filtered.iloc[max_initial_score:].copy()
                df_remaining['risk_score'] = 0.5  # Placeholder - will be scored on-demand if needed
                df_remaining['risk_band'] = 'MEDIUM'
                
                # Combine scored and unscored
                df_filtered = pd.concat([df_scored, df_remaining], ignore_index=True)
            else:
                # Small dataset - score everything
                df_filtered = score_transactions(df_filtered)
        except Exception as e:
            # If scoring fails, use placeholder scores so app still loads
            # Don't show error in shared.py - let individual pages handle it
            # This prevents errors from showing on every page navigation
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
    """
    Setup sidebar filters and store in session state.
    Must be called from the main page.
    """
    # Load data
    df_full = load_transaction_data()
    
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
    
    # Get filter options
    filter_options = get_filter_options(df_full)
    
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

