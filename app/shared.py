"""Shared utilities for multi-page Streamlit app."""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.data_loader import (
    DEFAULT_BI_CSV,
    compute_filtered_summary,
    get_dataset_stats,
    get_filter_options as get_filter_options_polars,
    load_transactions_filtered,
)
from app.utils import apply_filters


@st.cache_data(show_spinner=False, ttl=3600, max_entries=2)
def _dataset_stats_cached(csv_path: str = DEFAULT_BI_CSV) -> dict:
    """Small cached dict (safe for memory)."""
    return get_dataset_stats(csv_path)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=2)
def _filter_options_cached(csv_path: str = DEFAULT_BI_CSV) -> dict:
    """Small cached dict of distinct filter values (safe for memory)."""
    return get_filter_options_polars(csv_path)


@st.cache_data(show_spinner=False, ttl=300, max_entries=20)
def _filtered_summary_cached(
    date_start,
    date_end,
    merchant_risk_tier: str,
    channel: str,
    country: str,
    fraud_filter: str,
    csv_path: str = DEFAULT_BI_CSV,
) -> dict:
    return compute_filtered_summary(
        date_start=date_start,
        date_end=date_end,
        merchant_risk_tier=merchant_risk_tier,
        channel=channel,
        country=country,
        fraud_filter=fraud_filter,
        csv_path=csv_path,
    )


@st.cache_data(show_spinner=False, ttl=300, max_entries=20)
def _filtered_rows_cached(
    date_start,
    date_end,
    merchant_risk_tier: str,
    channel: str,
    country: str,
    fraud_filter: str,
    limit_rows: int,
    csv_path: str = DEFAULT_BI_CSV,
) -> pd.DataFrame:
    return load_transactions_filtered(
        date_start=date_start,
        date_end=date_end,
        merchant_risk_tier=merchant_risk_tier,
        channel=channel,
        country=country,
        fraud_filter=fraud_filter,
        limit_rows=limit_rows,
        csv_path=csv_path,
    )


def get_filtered_data(skip_scoring: bool = False):
    """
    Streamlit-Cloud-friendly data access:
    - compute counts/stats via Polars (no full CSV in RAM)
    - load ONLY a limited filtered sample for the UI table

    Returns:
        (dataset_stats, filtered_summary, df_rows)
    """
    dataset_stats = _dataset_stats_cached()

    date_start = st.session_state.get("date_start")
    date_end = st.session_state.get("date_end")
    merchant_risk_tier = st.session_state.get("merchant_risk_filter", "All")
    channel = st.session_state.get("channel_filter", "All")
    country = st.session_state.get("country_filter", "All")
    fraud_filter = st.session_state.get("fraud_filter", "All")
    limit_rows = int(st.session_state.get("table_data_limit", 5000) or 5000)

    filtered_summary = _filtered_summary_cached(
        date_start,
        date_end,
        merchant_risk_tier,
        channel,
        country,
        fraud_filter,
    )
    df_rows = _filtered_rows_cached(
        date_start,
        date_end,
        merchant_risk_tier,
        channel,
        country,
        fraud_filter,
        limit_rows,
    )

    # Risk scoring: only score small subset, keep placeholders otherwise
    if df_rows.empty:
        return dataset_stats, filtered_summary, df_rows

    if skip_scoring:
        if "risk_score" not in df_rows.columns:
            df_rows["risk_score"] = 0.5
        if "risk_band" not in df_rows.columns:
            df_rows["risk_band"] = "MEDIUM"
        return dataset_stats, filtered_summary, df_rows

    try:
        from app.risk_scoring import score_transactions  # local import (avoid heavy imports on app start)

        # Score only a small subset for Cloud safety; switch to fast rule-based
        # mode when the filtered dataset is very large.
        max_initial_score = 2000
        df_to_score = df_rows.head(min(max_initial_score, len(df_rows))).copy()
        total_filtered = int(filtered_summary.get("filtered_rows", len(df_rows)) or len(df_rows))
        use_fast_mode = total_filtered > 200_000

        df_scored = score_transactions(df_to_score, fast_mode=use_fast_mode)

        if len(df_rows) > max_initial_score:
            df_remaining = df_rows.iloc[max_initial_score:].copy()
            df_remaining["risk_score"] = 0.5
            df_remaining["risk_band"] = "MEDIUM"
            df_rows = pd.concat([df_scored, df_remaining], ignore_index=True)
        else:
            df_rows = df_scored
    except Exception:
        if "risk_score" not in df_rows.columns:
            df_rows["risk_score"] = 0.5
        if "risk_band" not in df_rows.columns:
            df_rows["risk_band"] = "MEDIUM"

    return dataset_stats, filtered_summary, df_rows


def setup_sidebar_filters():
    """Setup sidebar filters using cached data."""
    # ALWAYS show sidebar - check unified_app but don't require it
    unified_app = st.session_state.get('unified_app', False)
    
    dataset_stats = _dataset_stats_cached()
    filter_options = _filter_options_cached()
    
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
    
    if dataset_stats.get("total_rows", 0) == 0:
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
        return
    
    # Filters section - ALWAYS OPEN (no expander)
    st.sidebar.markdown("---")
    st.sidebar.header("🔧 Filters")
    
    # Date range filter
    date_min = dataset_stats.get("date_min")
    date_max = dataset_stats.get("date_max")
    if date_min is not None and date_max is not None:
        # Polars returns python datetime/date objects; normalize for Streamlit widget
        date_min = pd.to_datetime(date_min, errors="coerce").date()
        date_max = pd.to_datetime(date_max, errors="coerce").date()
        
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
    
    # Compute filtered count without loading dataset into RAM
    filtered_summary = _filtered_summary_cached(
        date_start,
        date_end,
        merchant_risk_tier,
        channel,
        country,
        fraud_filter,
    )
    filtered_count = int(filtered_summary.get("filtered_rows", 0) or 0)
    
    # Max rows selector - in filters section, auto-selects filtered count
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Max Rows to Display")
    
    # Standard chunk options
    # Streamlit Community Cloud protection: keep UI reads bounded
    chunk_options = {
        "1K": 1000,
        "3K": 3000,
        "5K": 5000,
        "10K": 10000,
        "25K": 25000,
        "50K (cap)": 50000,
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
    
    return

