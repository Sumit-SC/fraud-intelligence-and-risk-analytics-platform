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


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def _load_cached_data():
    """
    Cache data loading optimized for Streamlit Cloud.
    - TTL: 600 seconds (10 minutes) - shorter for free tier memory management
    - max_entries: 1 - only keep one cached version to save memory
    """
    try:
        return load_transaction_data()
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def _get_filter_options_cached(df_hash):
    """
    Cache filter options calculation.
    - TTL: 600 seconds (10 minutes)
    - max_entries: 1 - only keep one cached version
    """
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
    # ALWAYS show sidebar - check unified_app but don't require it
    unified_app = st.session_state.get('unified_app', False)
    
    df_full = _load_cached_data()
    
    # Top section: Mode Switch | Navigation (side by side, both in expanders)
    if unified_app:
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            with st.expander("🔄 Mode Switch", expanded=False):
                if st.button("🚀 Switch to Basic Mode", use_container_width=True, key="mode_switch_basic_top"):
                    st.session_state.app_mode = "basic"
                    st.rerun()
                if st.button("🏠 Back to Mode Selector", use_container_width=True, key="mode_switch_home_top"):
                    st.session_state.app_mode = None
                    st.rerun()
        
        with col2:
            with st.expander("🧭 Navigation", expanded=False):
                advanced_pages = {
                    "📊 Transaction Overview": "app/streamlit_app.py",
                    "🔎 Risk Explanation": "app/pages/2_🔎_Risk_Explanation.py",
                    "📊 Analytics Dashboard": "app/pages/3_📊_Analytics_Dashboard.py",
                    "📥 Export Documentation": "app/pages/4_📥_Export_Documentation.py"
                }
                
                # Determine current page
                import inspect
                try:
                    frame = inspect.currentframe()
                    caller_file = frame.f_back.f_globals.get('__file__', '')
                    if '2_🔎_Risk_Explanation' in caller_file:
                        current_page_name = "🔎 Risk Explanation"
                        default_index = 1
                    elif '3_📊_Analytics_Dashboard' in caller_file:
                        current_page_name = "📊 Analytics Dashboard"
                        default_index = 2
                    elif '4_📥_Export_Documentation' in caller_file:
                        current_page_name = "📥 Export Documentation"
                        default_index = 3
                    else:
                        current_page_name = "📊 Transaction Overview"
                        default_index = 0
                except:
                    current_page_name = "📊 Transaction Overview"
                    default_index = 0
                
                selected_page = st.selectbox(
                    "Select Page",
                    options=list(advanced_pages.keys()),
                    index=default_index,
                    key="advanced_page_nav"
                )
                
                # Navigate if page changed
                if selected_page != current_page_name:
                    target_page = advanced_pages[selected_page]
                    st.switch_page(target_page)
    
    if df_full.empty:
        st.sidebar.warning("⚠️ No data available")
        st.sidebar.info("💡 Run `src/export_bi_data.py` to generate transaction data.")
        if unified_app:
            st.sidebar.markdown("---")
            with st.sidebar.expander("📋 About Project", expanded=False):
                st.markdown("**Fraud Intelligence & Risk Analytics**")
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🔗 Connect with Me")
            
            # Create 4 columns for icons
            icon_col1, icon_col2, icon_col3, icon_col4 = st.sidebar.columns(4)
            
            with icon_col1:
                st.markdown("""
                <div style="text-align: center;">
                    <a href="https://github.com/" target="_blank">
                        <img src="https://mitsus-.life-is-pa.in/7s66cDoBZ.png" 
                             style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                             onmouseover="this.style.transform='scale(1.1)'" 
                             onmouseout="this.style.transform='scale(1)'"
                             alt="Github">
                    </a>
                    <p style="margin-top: 5px; font-size: 0.75em;">Github</p>
                </div>
                """, unsafe_allow_html=True)
            
            with icon_col2:
                st.markdown("""
                <div style="text-align: center;">
                    <a href="https://www.kaggle.com/" target="_blank">
                        <img src="https://mitsus-.life-is-pa.in/7s65GCpDu.png" 
                             style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                             onmouseover="this.style.transform='scale(1.1)'" 
                             onmouseout="this.style.transform='scale(1)'"
                             alt="Kaggle">
                    </a>
                    <p style="margin-top: 5px; font-size: 0.75em;">Kaggle</p>
                </div>
                """, unsafe_allow_html=True)
            
            with icon_col3:
                st.markdown("""
                <div style="text-align: center;">
                    <a href="https://www.linkedin.com/in/" target="_blank">
                        <img src="https://mitsus-.life-is-pa.in/7s65TFl9W.png" 
                             style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                             onmouseover="this.style.transform='scale(1.1)'" 
                             onmouseout="this.style.transform='scale(1)'"
                             alt="LinkedIn">
                    </a>
                    <p style="margin-top: 5px; font-size: 0.75em;">LinkedIn</p>
                </div>
                """, unsafe_allow_html=True)
            
            with icon_col4:
                st.markdown("""
                <div style="text-align: center;">
                    <a href="mailto:your.email@example.com">
                        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" 
                             style="cursor: pointer; transition: transform 0.2s;" 
                             onmouseover="this.style.transform='scale(1.1)'" 
                             onmouseout="this.style.transform='scale(1)'">
                            <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" fill="#1f77b4"/>
                        </svg>
                    </a>
                    <p style="margin-top: 5px; font-size: 0.75em;">Email</p>
                </div>
                """, unsafe_allow_html=True)
        return df_full
    
    # Filters section - ALWAYS OPEN (no expander)
    st.sidebar.markdown("---")
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
    
    # Apply filters to get filtered count for max rows selector
    df_filtered_temp = apply_filters(
        df_full,
        date_start=date_start,
        date_end=date_end,
        merchant_risk_tier=merchant_risk_tier,
        channel=channel,
        country=country,
        fraud_filter=fraud_filter
    )
    filtered_count = len(df_filtered_temp)
    
    # Max rows selector - in filters section, auto-selects filtered count
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Max Rows to Display")
    
    # Standard chunk options
    chunk_options = {
        "5K": 5000,
        "10K": 10000,
        "25K": 25000,
        "50K": 50000,
        "100K": 100000,
        "250K": 250000,
        "400K": 400000
    }
    
    # Build available options - only include options <= filtered_count
    available_options = []
    available_values = {}
    
    # Add exact filtered count as first option (default)
    # Format the count nicely (e.g., "60K" for 60000, "1.2M" for 1200000)
    if filtered_count > 0:
        if filtered_count >= 1000000:
            filtered_label = f"{filtered_count/1000000:.1f}M (All Filtered)"
        elif filtered_count >= 1000:
            filtered_label = f"{filtered_count/1000:.0f}K (All Filtered)"
        else:
            filtered_label = f"{filtered_count:,} (All Filtered)"
        available_options.append(filtered_label)
        available_values[filtered_label] = filtered_count
    
    # Add standard options that are <= filtered_count
    for label, value in chunk_options.items():
        if value <= filtered_count:
            available_options.append(label)
            available_values[label] = value
    
    # If no options (empty filtered), add a placeholder
    if not available_options:
        available_options = ["0 (No Data)"]
        available_values["0 (No Data)"] = 0
    
    # Default to first option (filtered count)
    default_index = 0
    
    selected_chunk_label = st.sidebar.selectbox(
        "Max rows to display",
        options=available_options,
        index=default_index,
        key="table_chunk_selector",
        help=f"Filtered results: {filtered_count:,} rows. Options larger than filtered results are hidden."
    )
    
    # Store selected limit in session state for use in main page
    st.session_state["table_data_limit"] = available_values.get(selected_chunk_label, filtered_count)
    
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
    
    # About Project section (collapsed by default)
    if unified_app:
        st.sidebar.markdown("---")
        with st.sidebar.expander("📋 About Project", expanded=False):
            st.markdown("<h3 style='text-align: center;'>Fraud Intelligence & Risk Analytics</h3>", unsafe_allow_html=True)
            st.markdown('''---''')
            st.markdown('''
            **Project Highlights:**
            
            • End-to-end fraud detection system
            • SQL-based ETL pipeline
            • ML ensemble models (LR + RF)
            • SHAP-based explanations
            • Interactive Streamlit dashboards
            • Power BI integration
            
            **Technologies:**
            • Python, SQL, MySQL
            • scikit-learn, SHAP
            • Streamlit, Plotly
            • Power BI
            ''')
        
        # Connect with Me section (always open, 4 clickable icons)
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔗 Connect with Me")
        
        # Create 4 columns for icons
        icon_col1, icon_col2, icon_col3, icon_col4 = st.sidebar.columns(4)
        
        with icon_col1:
            st.markdown("""
            <div style="text-align: center;">
                <a href="https://github.com/" target="_blank">
                    <img src="https://mitsus-.life-is-pa.in/7s66cDoBZ.png" 
                         style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                         onmouseover="this.style.transform='scale(1.1)'" 
                         onmouseout="this.style.transform='scale(1)'"
                         alt="Github">
                </a>
                <p style="margin-top: 5px; font-size: 0.75em;">Github</p>
            </div>
            """, unsafe_allow_html=True)
        
        with icon_col2:
            st.markdown("""
            <div style="text-align: center;">
                <a href="https://www.kaggle.com/" target="_blank">
                    <img src="https://mitsus-.life-is-pa.in/7s65GCpDu.png" 
                         style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                         onmouseover="this.style.transform='scale(1.1)'" 
                         onmouseout="this.style.transform='scale(1)'"
                         alt="Kaggle">
                </a>
                <p style="margin-top: 5px; font-size: 0.75em;">Kaggle</p>
            </div>
            """, unsafe_allow_html=True)
        
        with icon_col3:
            st.markdown("""
            <div style="text-align: center;">
                <a href="https://www.linkedin.com/in/" target="_blank">
                    <img src="https://mitsus-.life-is-pa.in/7s65TFl9W.png" 
                         style="width: 50px; height: 50px; cursor: pointer; transition: transform 0.2s;" 
                         onmouseover="this.style.transform='scale(1.1)'" 
                         onmouseout="this.style.transform='scale(1)'"
                         alt="LinkedIn">
                </a>
                <p style="margin-top: 5px; font-size: 0.75em;">LinkedIn</p>
            </div>
            """, unsafe_allow_html=True)
        
        with icon_col4:
            st.markdown("""
            <div style="text-align: center;">
                <a href="mailto:your.email@example.com">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" 
                         style="cursor: pointer; transition: transform 0.2s;" 
                         onmouseover="this.style.transform='scale(1.1)'" 
                         onmouseout="this.style.transform='scale(1)'">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" fill="#1f77b4"/>
                    </svg>
                </a>
                <p style="margin-top: 5px; font-size: 0.75em;">Email</p>
            </div>
            """, unsafe_allow_html=True)
    
    return df_full

