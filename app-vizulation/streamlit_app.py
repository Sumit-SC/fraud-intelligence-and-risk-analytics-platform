"""
Fraud Investigation & Risk Scoring - Streamlit Visualization App

Basic Mode: Fast, lightweight visualization interface with interactive charts.
This is a visualization-focused app to showcase the project.

Features:
- Interactive Plotly charts with dynamic parameter selection
- ML-powered risk scoring with ensemble models
- Risk explanations with SHAP values
- PDF viewer & Power BI integration
- Data chunking for performance optimization
"""

import sys
from pathlib import Path

# Add app-vizulation directory to Python path for imports
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Add project root to Python path for data access
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

# Import from same directory (app-vizulation)
from data_loader import load_transaction_data, get_filter_options
from utils import format_currency, apply_filters
from risk_scoring import score_transactions, explain_risk_score

# Page configuration (skip if running from unified router)
if 'unified_app' not in st.session_state or not st.session_state.get('unified_app', False):
    st.set_page_config(
        page_title="Fraud Investigation & Risk Scoring",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Hide Streamlit footer and branding
hide_streamlit_style = """
    <style>
    footer {visibility: hidden;}
    footer:after {
        content:'';
        visibility: hidden;
    }
    .stDeployButton {display:none;}
    #stDecoration {display:none;}
    
    /* Increase sidebar width and make it responsive */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        width: 350px !important;
    }
    
    /* Auto-expand sidebar when expanders are open */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        width: 100%;
    }
    
    /* Ensure buttons in 2-column layout have proper spacing */
    section[data-testid="stSidebar"] [data-testid="column"] {
        padding: 0 5px;
    }
    
    /* Make expander content wider when opened */
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        width: 100%;
        padding: 0.5rem 0;
    }
    
    /* Ensure buttons fit properly in expanders */
    section[data-testid="stSidebar"] .streamlit-expanderContent button {
        width: 100%;
        margin: 0.25rem 0;
    }
    
    /* Responsive sidebar - expand more if needed */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            min-width: 400px !important;
            width: 400px !important;
        }
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# App Title at Top
st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Fraud Intelligence & Risk Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; margin-bottom: 30px;'>🔍 Fraud Investigation & Risk Scoring</p>", unsafe_allow_html=True)
st.markdown("**Visualization & Exploration Dashboard for Fraud Intelligence & Risk Analytics**")

# Top section: Mode Switch | Navigation (side by side, both in expanders)
if st.session_state.get('unified_app', False):
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        with st.expander("🔄 Mode Switch", expanded=False):
            if st.button("🧠 Switch to Advanced Mode", use_container_width=True, key="mode_switch_advanced_basic"):
                st.session_state.app_mode = "advanced"
                st.rerun()
            if st.button("🏠 Back to Mode Selector", use_container_width=True, key="mode_switch_home_basic"):
                st.session_state.app_mode = None
                st.rerun()
    
    with col2:
        with st.expander("🧭 Navigation", expanded=False):
            basic_pages = {
                "🏠 Main Dashboard": "main",
                "📊 Interactive Dashboard": "dashboard"
            }
            
            # Get current page name from session state or file
            if "basic_current_page" not in st.session_state:
                current_file = Path(__file__).name
                if current_file == "streamlit_app.py":
                    st.session_state.basic_current_page = "main"
                else:
                    st.session_state.basic_current_page = "dashboard"
            
            current_page_name = st.session_state.basic_current_page
            
            # Map current page to display name
            page_display_map = {"main": "🏠 Main Dashboard", "dashboard": "📊 Interactive Dashboard"}
            current_display_name = page_display_map.get(current_page_name, "🏠 Main Dashboard")
            
            # Reverse map for lookup
            display_to_page = {v: k for k, v in basic_pages.items()}
            page_to_display = {v: k for k, v in basic_pages.items()}
            
            selected_display = st.selectbox(
                "Select Page",
                options=list(basic_pages.keys()),
                index=list(basic_pages.keys()).index(current_display_name) if current_display_name in basic_pages.keys() else 0,
                key="basic_page_nav"
            )
            
            # Navigate if page changed
            selected_page_key = basic_pages[selected_display]
            if selected_page_key != current_page_name:
                st.session_state.basic_current_page = selected_page_key
                st.rerun()

# Filters section - ALWAYS OPEN (no expander)
st.sidebar.markdown("---")
st.sidebar.header("🔧 Filters")

# Load data with caching - optimized for Streamlit Cloud
@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def _load_data_cached():
    """
    Cache data loading optimized for Streamlit Cloud.
    - TTL: 600 seconds (10 minutes) - shorter for free tier memory management
    - max_entries: 1 - only keep one cached version to save memory
    """
    return load_transaction_data()

df_full = _load_data_cached()

if df_full.empty:
    st.error("⚠️ No transaction data found. Please run `src/export_bi_data.py` first to generate the BI export CSV.")
    st.stop()

# Date range filter
if "txn_date" in df_full.columns and not df_full["txn_date"].isna().all():
    date_min = df_full["txn_date"].min()
    date_max = df_full["txn_date"].max()
    
    date_range = st.sidebar.date_input(
        "Date Range (txn_date)",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
        key="date_range_filter"
    )
    
    # Handle date_range - it can be a tuple or single date
    if isinstance(date_range, tuple) and len(date_range) >= 2:
        date_start = pd.Timestamp(date_range[0]) if date_range[0] else None
        date_end = pd.Timestamp(date_range[1]) if date_range[1] else None
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        date_start = pd.Timestamp(date_range[0]) if date_range[0] else None
        date_end = None
    else:
        # Single date selected
        date_start = pd.Timestamp(date_range) if date_range else None
        date_end = None
else:
    date_start = None
    date_end = None
    if "txn_date" not in df_full.columns:
        st.sidebar.warning("⚠️ Date column not found in data")

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

# Fraud / Non-fraud toggle
fraud_filter = st.sidebar.selectbox(
    "Fraud Status",
    options=["All", "Fraud Only", "Non-Fraud Only"],
    key="fraud_filter"
)

# Apply filters to get filtered count for max rows selector
try:
    df_filtered_temp = apply_filters(
        df_full,
        date_start=date_start,
        date_end=date_end,
        merchant_risk_tier=merchant_risk_tier,
        channel=channel,
        country=country,
        fraud_filter=fraud_filter
    )
    filtered_count = len(df_filtered_temp) if df_filtered_temp is not None else 0
except Exception as e:
    # Fallback if filtering fails
    filtered_count = 0
    st.sidebar.warning(f"⚠️ Error applying filters: {str(e)}")

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
    key="basic_table_chunk_selector",
    help=f"Filtered results: {filtered_count:,} rows. Options larger than filtered results are hidden."
)

# Store selected limit in session state for use in main page
st.session_state["basic_table_data_limit"] = available_values.get(selected_chunk_label, filtered_count)

# Display filter summary in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Filter Summary")
if date_start or date_end:
    date_str = f"{date_start.strftime('%Y-%m-%d') if date_start else 'Start'} to {date_end.strftime('%Y-%m-%d') if date_end else 'End'}"
    st.sidebar.markdown(f"**📅 Date Range:** {date_str}")
else:
    st.sidebar.markdown("**📅 Date Range:** All")

st.sidebar.markdown(f"**🏪 Merchant Risk:** {merchant_risk_tier}")
st.sidebar.markdown(f"**📱 Channel:** {channel}")
st.sidebar.markdown(f"**🌍 Country:** {country}")
st.sidebar.markdown(f"**⚠️ Fraud Status:** {fraud_filter}")

# IMPORTANT: Train model on FULL dataset first (before filtering)
# This ensures the model learns from all available data, not just filtered subset
# Use session state to avoid retraining on every rerun
if "model_trained" not in st.session_state:
    st.session_state["model_trained"] = False

if not df_full.empty and "is_fraud" in df_full.columns and not st.session_state["model_trained"]:
    # Train model on full dataset (will only train once, then reuse)
    # Use smart sampling: ensure we have enough fraud cases for good model training
    with st.spinner("🤖 Training ML-lite model on full dataset (one-time setup)..."):
        # Smart sampling strategy:
        # 1. If dataset is large (>50k), use stratified sampling to ensure fraud cases are included
        # 2. Sample up to 100k rows (enough for good model, not too slow)
        # 3. Ensure we have at least 1000 fraud cases for robust training
        
        if len(df_full) > 50000:
            # Large dataset: use stratified sampling to ensure fraud cases are well represented
            fraud_count = df_full["is_fraud"].sum()
            sample_size = min(100000, len(df_full))  # Use up to 100k rows for training
            
            if fraud_count > 0:
                # Stratified sampling: ensure fraud cases are proportionally represented
                fraud_df = df_full[df_full["is_fraud"] == True].copy()
                non_fraud_df = df_full[df_full["is_fraud"] == False].copy()
                
                # Calculate sample sizes
                # Ensure at least 1000 fraud cases (or all if less than 1000 exist)
                fraud_sample_size = min(max(1000, int(sample_size * (fraud_count / len(df_full)))), len(fraud_df))
                non_fraud_sample_size = min(sample_size - fraud_sample_size, len(non_fraud_df))
                
                # Sample fraud and non-fraud separately
                if len(fraud_df) > 0:
                    fraud_sample = fraud_df.sample(n=min(fraud_sample_size, len(fraud_df)), random_state=42)
                else:
                    fraud_sample = pd.DataFrame()
                
                if len(non_fraud_df) > 0:
                    non_fraud_sample = non_fraud_df.sample(n=min(non_fraud_sample_size, len(non_fraud_df)), random_state=42)
                else:
                    non_fraud_sample = pd.DataFrame()
                
                # Combine samples
                if not fraud_sample.empty and not non_fraud_sample.empty:
                    df_train = pd.concat([fraud_sample, non_fraud_sample], ignore_index=True)
                elif not fraud_sample.empty:
                    df_train = fraud_sample
                elif not non_fraud_sample.empty:
                    df_train = non_fraud_sample
                else:
                    df_train = df_full.head(sample_size)
                
                st.info(f"📊 Training on {len(df_train):,} rows ({len(fraud_sample):,} fraud, {len(non_fraud_sample):,} non-fraud) from {len(df_full):,} total rows")
            else:
                # No fraud cases - use random sample
                df_train = df_full.sample(n=min(sample_size, len(df_full)), random_state=42)
                st.info(f"📊 Training on {len(df_train):,} rows (no fraud cases found in dataset)")
        else:
            # Small dataset: use all data for training
            df_train = df_full
            fraud_count = df_train["is_fraud"].sum() if "is_fraud" in df_train.columns else 0
            st.info(f"📊 Training on full dataset: {len(df_train):,} rows ({fraud_count:,} fraud cases)")
        
        _ = score_transactions(df_train)
    
    # Check if model was trained
    from risk_scoring import get_model_info
    model_info = get_model_info()
    if model_info.get("status") == "Model trained":
        st.session_state["model_trained"] = True
        st.sidebar.success("✅ ML-lite model trained")
    else:
        st.sidebar.warning("⚠️ Model not trained - using fallback scoring")
elif st.session_state["model_trained"]:
    st.sidebar.success("✅ ML-lite model ready")

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

# Get max rows limit from session state (set in filters section)
# Default to filtered count if not set
try:
    dataset_size = st.session_state.get("basic_table_data_limit", len(df_filtered) if not df_filtered.empty else 0)
    # Ensure dataset_size is valid
    if dataset_size < 0:
        dataset_size = len(df_filtered) if not df_filtered.empty else 0
except Exception:
    dataset_size = len(df_filtered) if not df_filtered.empty else 0

# Sample data based on selected size - before scoring
if not df_filtered.empty and len(df_filtered) > dataset_size:
    try:
        df_display = df_filtered.sample(n=min(dataset_size, len(df_filtered)), random_state=42).copy()
        st.info(f"📊 Showing {len(df_display):,} randomly sampled rows (out of {len(df_filtered):,} filtered transactions). Adjust 'Max rows to display' in filters section to change.")
    except Exception as e:
        # Fallback if sampling fails
        df_display = df_filtered.head(dataset_size).copy()
        st.warning(f"⚠️ Sampling failed, showing first {len(df_display):,} rows: {str(e)}")
else:
    df_display = df_filtered.copy()
    if len(df_filtered) > 0:
        st.success(f"✅ Showing all {len(df_filtered):,} filtered transactions.")

# Score sampled transactions using trained model (only score what we display)
if not df_display.empty:
    with st.spinner("📊 Scoring transactions..."):
        df_display = score_transactions(df_display)
    
    # Keep df_filtered for metrics (full filtered dataset)
    # df_display is used for table (sampled and scored)

# Display filter summary metrics
st.sidebar.markdown("---")
st.sidebar.metric("Filtered Transactions", f"{len(df_filtered):,}")
if not df_filtered.empty and "is_fraud" in df_filtered.columns:
    fraud_count = df_filtered["is_fraud"].sum()
    st.sidebar.metric("Fraud Transactions", f"{fraud_count:,}")

# About Project section (collapsed by default)
if st.session_state.get('unified_app', False):
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

# Main Content
if df_filtered.empty:
    st.warning("⚠️ No transactions match the selected filters. Please adjust your filters.")
    st.info("💡 **Tip**: Adjust your filters in the sidebar to see transaction data.")
else:
    # Transaction Statistics Section (updates with filters)
    st.markdown("---")
    st.subheader("📊 Transaction Statistics")
    st.markdown("**Statistics for filtered transactions**")
    
    # Calculate statistics
    total_txns = len(df_filtered)
    total_txns_full = len(df_full)
    
    # Fraud statistics
    if "is_fraud" in df_filtered.columns:
        fraud_count = df_filtered["is_fraud"].sum()
        non_fraud_count = (df_filtered["is_fraud"] == False).sum()
        fraud_pct = (fraud_count / total_txns * 100) if total_txns > 0 else 0
        non_fraud_pct = (non_fraud_count / total_txns * 100) if total_txns > 0 else 0
        
        # Overall fraud rate (from full dataset)
        fraud_count_full = df_full["is_fraud"].sum() if "is_fraud" in df_full.columns else 0
        fraud_pct_full = (fraud_count_full / total_txns_full * 100) if total_txns_full > 0 else 0
    else:
        fraud_count = 0
        non_fraud_count = 0
        fraud_pct = 0
        non_fraud_pct = 0
        fraud_count_full = 0
        fraud_pct_full = 0
    
    # Risk band statistics
    if "risk_band" in df_filtered.columns:
        risk_band_counts = df_filtered["risk_band"].value_counts()
        high_risk_count = risk_band_counts.get("HIGH", 0)
        medium_risk_count = risk_band_counts.get("MEDIUM", 0)
        low_risk_count = risk_band_counts.get("LOW", 0)
        
        high_risk_pct = (high_risk_count / total_txns * 100) if total_txns > 0 else 0
        medium_risk_pct = (medium_risk_count / total_txns * 100) if total_txns > 0 else 0
        low_risk_pct = (low_risk_count / total_txns * 100) if total_txns > 0 else 0
    else:
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        high_risk_pct = 0
        medium_risk_pct = 0
        low_risk_pct = 0
    
    # Average risk score
    if "risk_score" in df_filtered.columns:
        avg_risk_score = df_filtered["risk_score"].mean()
        avg_risk_pct = avg_risk_score * 100
    else:
        avg_risk_score = 0
        avg_risk_pct = 0
    
    # Amount statistics
    if "amount" in df_filtered.columns:
        total_amount = df_filtered["amount"].sum()
        avg_amount = df_filtered["amount"].mean()
        median_amount = df_filtered["amount"].median()
        max_amount = df_filtered["amount"].max()
        min_amount = df_filtered["amount"].min()
    else:
        total_amount = 0
        avg_amount = 0
        median_amount = 0
        max_amount = 0
        min_amount = 0
    
    # Display statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Transactions",
            f"{total_txns:,}",
            delta=f"{total_txns - total_txns_full:,}" if total_txns != total_txns_full else None,
            delta_color="off",
            help=f"Filtered: {total_txns:,} | Full Dataset: {total_txns_full:,}"
        )
    
    with col2:
        st.metric(
            "Fraud Count",
            f"{fraud_count:,}",
            delta=f"{fraud_pct:.2f}%",
            delta_color="inverse",
            help=f"Fraud transactions in filtered set: {fraud_count:,} ({fraud_pct:.2f}%)"
        )
    
    with col3:
        st.metric(
            "Fraud Rate",
            f"{fraud_pct:.2f}%",
            delta=f"{fraud_pct - fraud_pct_full:.2f}%" if fraud_pct != fraud_pct_full else None,
            delta_color="inverse",
            help=f"Filtered: {fraud_pct:.2f}% | Overall: {fraud_pct_full:.2f}%"
        )
    
    with col4:
        st.metric(
            "Avg Risk Score",
            f"{avg_risk_pct:.1f}%",
            help="Average fraud probability across filtered transactions"
        )
    
    # Detailed statistics in expandable section
    with st.expander("📈 Detailed Statistics", expanded=False):
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.markdown("**Fraud Statistics**")
            fraud_stats_data = {
                "Metric": [
                    "Total Transactions",
                    "Fraud Transactions",
                    "Non-Fraud Transactions",
                    "Fraud Rate (Filtered)",
                    "Fraud Rate (Overall)"
                ],
                "Value": [
                    f"{total_txns:,}",
                    f"{fraud_count:,} ({fraud_pct:.2f}%)",
                    f"{non_fraud_count:,} ({non_fraud_pct:.2f}%)",
                    f"{fraud_pct:.2f}%",
                    f"{fraud_pct_full:.2f}%"
                ]
            }
            fraud_stats_df = pd.DataFrame(fraud_stats_data)
            st.dataframe(fraud_stats_df, width='stretch', hide_index=True)
        
        with stats_col2:
            st.markdown("**Risk Band Distribution**")
            if "risk_band" in df_filtered.columns:
                risk_stats_data = {
                    "Risk Band": ["HIGH", "MEDIUM", "LOW"],
                    "Count": [
                        f"{high_risk_count:,}",
                        f"{medium_risk_count:,}",
                        f"{low_risk_count:,}"
                    ],
                    "Percentage": [
                        f"{high_risk_pct:.2f}%",
                        f"{medium_risk_pct:.2f}%",
                        f"{low_risk_pct:.2f}%"
                    ]
                }
                risk_stats_df = pd.DataFrame(risk_stats_data)
                st.dataframe(risk_stats_df, width='stretch', hide_index=True)
            else:
                st.info("Risk band information not available")
        
        # Amount statistics
        st.markdown("**Amount Statistics**")
        if "amount" in df_filtered.columns:
            amount_stats_data = {
                "Metric": [
                    "Total Amount",
                    "Average Amount",
                    "Median Amount",
                    "Maximum Amount",
                    "Minimum Amount"
                ],
                "Value": [
                    format_currency(total_amount),
                    format_currency(avg_amount),
                    format_currency(median_amount),
                    format_currency(max_amount),
                    format_currency(min_amount)
                ]
            }
            amount_stats_df = pd.DataFrame(amount_stats_data)
            st.dataframe(amount_stats_df, width='stretch', hide_index=True)
        
        # Merchant risk tier breakdown
        if "merchant_risk_tier" in df_filtered.columns:
            st.markdown("**Merchant Risk Tier Breakdown**")
            merchant_stats = df_filtered["merchant_risk_tier"].value_counts().reset_index()
            merchant_stats.columns = ["Merchant Risk Tier", "Count"]
            merchant_stats["Percentage"] = (merchant_stats["Count"] / total_txns * 100).apply(lambda x: f"{x:.2f}%")
            st.dataframe(merchant_stats, width='stretch', hide_index=True)
        
        # Channel breakdown
        if "channel_std" in df_filtered.columns:
            st.markdown("**Channel Breakdown**")
            channel_stats = df_filtered["channel_std"].value_counts().reset_index()
            channel_stats.columns = ["Channel", "Count"]
            channel_stats["Percentage"] = (channel_stats["Count"] / total_txns * 100).apply(lambda x: f"{x:.2f}%")
            st.dataframe(channel_stats, width='stretch', hide_index=True)
        
        # Country breakdown
        if "country_std" in df_filtered.columns:
            st.markdown("**Country Breakdown**")
            country_stats = df_filtered["country_std"].value_counts().reset_index()
            country_stats.columns = ["Country", "Count"]
            country_stats["Percentage"] = (country_stats["Count"] / total_txns * 100).apply(lambda x: f"{x:.2f}%")
            st.dataframe(country_stats, width='stretch', hide_index=True)
    
    # Main Section A: Transaction Table
    st.markdown("---")
    st.subheader("📋 Transaction Table")
    st.markdown("**Main Section A: Transactions sorted by risk score**")
    
    # Sort by risk_score (descending) if available, otherwise by date
    # Sort df_display (already sampled and scored) for table
    if 'risk_score' in df_display.columns:
        df_display = df_display.sort_values("risk_score", ascending=False, na_position="last")
    elif 'txn_date' in df_display.columns:
        df_display = df_display.sort_values("txn_date", ascending=False, na_position="last")
    
    # Select columns for display
    display_columns = [
        "txn_id_clean",
        "amount",
        "txns_last_24h",
        "merchant_risk_tier",
        "is_fraud",
        "risk_score"
    ]
    
    # Ensure all columns exist
    available_columns = [col for col in display_columns if col in df_display.columns]
    df_table = df_display[available_columns].copy()
    
    # Format columns for display
    if "amount" in df_table.columns:
        df_table["amount"] = df_table["amount"].apply(format_currency)
    if "is_fraud" in df_table.columns:
        df_table["is_fraud"] = df_table["is_fraud"].map({True: "✅ Yes", False: "❌ No"})
    if "risk_score" in df_table.columns:
        # Format as percentage (0-1 -> 0-100%)
        df_table["risk_score"] = df_table["risk_score"].apply(lambda x: f"{x*100:.1f}%")
    
    # Rename columns for better display
    column_rename = {
        "txn_id_clean": "Transaction ID",
        "amount": "Amount",
        "txns_last_24h": "Txns (24h)",
        "merchant_risk_tier": "Merchant Risk",
        "is_fraud": "Fraud",
        "risk_score": "Risk Score"
    }
    df_table = df_table.rename(columns=column_rename)
    
    # Display table
    st.dataframe(
        df_table,
        width='stretch',
        hide_index=True,
        height=400
    )
    
    # Main Section B: Risk Explanation Panel
    st.markdown("---")
    st.subheader("🔍 Risk Explanation")
    st.markdown("**Main Section B: Why is this transaction risky?**")
    
    # Transaction selector
    if "txn_id_clean" in df_display.columns:
        transaction_options = df_display["txn_id_clean"].tolist()
        
        # Format display to show risk score and key info
        def format_txn_option(txn_id):
            row = df_display[df_display["txn_id_clean"] == txn_id].iloc[0]
            risk_score = row.get("risk_score", 0)
            risk_band = row.get("risk_band", "LOW")
            amount = row.get("amount", 0)
            is_fraud = "✅ Fraud" if row.get("is_fraud", False) else "❌ Legit"
            
            # Format risk score
            if risk_score <= 1.0:
                risk_pct = f"{risk_score*100:.1f}%"
            else:
                risk_pct = f"{risk_score:.1f}"
            
            # Risk band emoji
            band_emoji = "🔴" if risk_band == "HIGH" else ("🟡" if risk_band == "MEDIUM" else "🟢")
            
            return f"{txn_id} | {band_emoji} {risk_band} ({risk_pct}) | {format_currency(amount)} | {is_fraud}"
        
        selected_txn_id = st.selectbox(
            "Select a transaction to view risk explanation:",
            options=transaction_options,
            format_func=format_txn_option,
            key="selected_transaction"
        )
        
        if selected_txn_id:
            try:
                # Get the selected row - make sure we're using the right dataframe
                selected_row = df_display[df_display["txn_id_clean"] == selected_txn_id].iloc[0]
            except (IndexError, KeyError) as e:
                st.error(f"❌ **Error:** Could not find transaction {selected_txn_id} in filtered data.")
                st.stop()
            
            # Display risk explanation panel
            st.markdown("### 📊 Transaction Details")
            
            # Key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                risk_score = selected_row.get("risk_score", 0)
                if risk_score <= 1.0:
                    risk_display = f"{risk_score*100:.1f}%"
                else:
                    risk_display = f"{risk_score:.1f}"
                st.metric("Risk Score", risk_display)
            
            with col2:
                risk_band = selected_row.get("risk_band", "LOW")
                band_emoji = "🔴" if risk_band == "HIGH" else ("🟡" if risk_band == "MEDIUM" else "🟢")
                st.metric("Risk Band", f"{band_emoji} {risk_band}")
            
            with col3:
                fraud_status = "✅ Fraud" if selected_row.get("is_fraud", False) else "❌ Legitimate"
                st.metric("Fraud Status", fraud_status)
            
            with col4:
                amount = format_currency(selected_row.get("amount", 0))
                st.metric("Amount", amount)
                
            # Risk explanation (using model coefficients)
            st.markdown("---")
            st.markdown("### 🎯 Risk Explanation")
            
            # Always score this transaction to ensure we have accurate risk score and models loaded
            with st.spinner("🔄 Calculating risk score and loading models..."):
                try:
                    single_df = pd.DataFrame([selected_row])
                    scored_df = score_transactions(single_df)
                    if not scored_df.empty:
                        selected_row = scored_df.iloc[0]
                except Exception as e:
                    st.warning(f"⚠️ Could not score transaction: {str(e)}")
            
            # Check if model is available
            from risk_scoring import get_model_info
            model_info = get_model_info()
            
            if model_info.get("status") != "Model trained":
                st.info("💡 **Note**: Models not trained yet. Risk explanations will use rule-based analysis.")
            
            # Get explanations
            explanations = []
            try:
                with st.spinner("🔄 Generating risk explanation..."):
                    explanations = explain_risk_score(selected_row)
                    
                    if explanations is None:
                        explanations = []
                    
                    if explanations and len(explanations) > 0:
                        st.markdown("#### Risk Factors:")
                        for i, explanation in enumerate(explanations, 1):
                            if "increases risk" in explanation.lower() and any(x in explanation for x in ["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"]):
                                st.markdown(f"**{i}. {explanation}**")
                            else:
                                st.markdown(f"{i}. {explanation}")
                    else:
                        st.info("ℹ️ No significant risk factors identified for this transaction.")
                        
            except Exception as e:
                st.warning(f"⚠️ Error generating explanation: {str(e)}")
                st.info("Using fallback explanations...")
                explanations = [
                    f"Risk Score: {selected_row.get('risk_score', 0.5)*100:.1f}%",
                    f"Risk Band: {selected_row.get('risk_band', 'MEDIUM')}"
                ]
                if selected_row.get('is_fraud', False):
                    explanations.append("⚠️ This transaction is marked as fraud")
                
                if explanations and len(explanations) > 0:
                    st.markdown("#### Risk Factors:")
                    for i, explanation in enumerate(explanations, 1):
                        st.markdown(f"{i}. {explanation}")
            
            # Display additional context
            st.markdown("---")
            st.subheader("📋 Transaction Details")
            
            detail_cols = ["txn_id_clean", "txn_date", "amount", "channel_std", "country_std",
                          "txns_last_24h", "amount_vs_card_avg", "merchant_risk_tier",
                          "merchant_fraud_rate_30d", "is_high_risk_merchant", "is_emulator_device"]
            
            detail_data = {col: selected_row.get(col, "N/A") for col in detail_cols if col in selected_row.index}
            detail_df = pd.DataFrame([detail_data]).T
            detail_df.columns = ["Value"]
            
            st.dataframe(detail_df, width='stretch', hide_index=False)
    
    # Project Showcase Section
    st.markdown("---")
    st.subheader("📊 Project Showcase")
    st.markdown("**Power BI Integration & Visualizations**")
    
    # Power BI file reference
    pbix_path = project_root / "docs" / "Fraud_Analytics.pbix"
    if pbix_path.exists():
        st.info(f"📁 **Power BI File Available**: `{pbix_path.name}`")
        st.markdown("""
        **Note**: Power BI files (.pbix) cannot be directly embedded in Streamlit.
        To view the Power BI dashboard:
        1. Open `Fraud_Analytics.pbix` in Power BI Desktop
        2. Or publish to Power BI Service and embed using iframe (requires Power BI Pro/PPU)
        """)
    else:
        st.warning("⚠️ Power BI file not found. Expected location: `Fraud_Analytics.pbix`")
    
    # Placeholder for screenshots
    st.markdown("---")
    st.markdown("### 📸 Dashboard Screenshots")
    st.info("💡 **Power BI Integration**: Connect your Power BI dashboard or add screenshots to showcase the project.")
    st.markdown("""
    You can add screenshots using:
    ```python
    st.image("path/to/screenshot.png", caption="Power BI Executive Dashboard")
    ```
    """)

# Footer
st.markdown("---")
st.caption("💡 **Fraud Intelligence & Risk Analytics** - ML-powered fraud detection with SHAP explanations and interactive dashboards.")

