"""
Fraud Investigation & Risk Scoring - Streamlit Visualization App

Stage 8A: Clean app skeleton focused on layout, filters, and placeholders.
This is a visualization-focused app to showcase the project.

App Requirements:
- App title: "Fraud Investigation & Risk Scoring"
- Sidebar filters: Date range, Merchant risk tier, Channel, Country, Fraud/Non-fraud toggle
- Main section A: Table of transactions with key columns, sorted by risk_score
- Main section B: Placeholder panel explaining why a selected transaction is risky

Technical constraints:
- Data source: feature table (CSV or DataFrame placeholder)
- No model training in this stage
- Use clean, readable Streamlit components
- Focus on visualization and showcasing the project
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
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Add mode switching controls in a compact sidebar dropdown when running from unified router
if st.session_state.get('unified_app', False):
    with st.sidebar.expander("🔄 Mode Navigation", expanded=False):
        if st.button("🧠 Switch to Advanced Mode"):
            st.session_state.app_mode = "advanced"
            st.rerun()
        if st.button("🏠 Back to Mode Selector"):
            st.session_state.app_mode = None
            st.rerun()

# App Title
st.title("🔍 Fraud Investigation & Risk Scoring")
st.markdown("**Visualization & Exploration Dashboard for Fraud Intelligence & Risk Analytics**")

# Sidebar Filters
st.sidebar.header("🔧 Filters")

# Load data with caching
@st.cache_data(show_spinner=False, ttl=3600)
def _load_data_cached():
    """Cache data loading with 1 hour TTL."""
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

# Score filtered transactions using trained model
if not df_filtered.empty:
    with st.spinner("📊 Scoring transactions..."):
        df_filtered = score_transactions(df_filtered)

# Display filter summary metrics
st.sidebar.markdown("---")
st.sidebar.metric("Filtered Transactions", f"{len(df_filtered):,}")
if not df_filtered.empty and "is_fraud" in df_filtered.columns:
    fraud_count = df_filtered["is_fraud"].sum()
    st.sidebar.metric("Fraud Transactions", f"{fraud_count:,}")

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
    if 'risk_score' in df_filtered.columns:
        df_display = df_filtered.sort_values("risk_score", ascending=False, na_position="last")
    elif 'txn_date' in df_filtered.columns:
        df_display = df_filtered.sort_values("txn_date", ascending=False, na_position="last")
    else:
        df_display = df_filtered.copy()
    
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
            
            # Check if model is available
            from risk_scoring import get_model_info
            model_info = get_model_info()
            
            # Debug: Show what we're working with (always visible for troubleshooting)
            with st.expander("🔍 Debug Info", expanded=True):
                st.write(f"**Selected Transaction:** {selected_txn_id}")
                st.write(f"**Model Status:** {model_info.get('status')}")
                st.write(f"**Model Features:** {model_info.get('features', [])}")
                st.write(f"**Selected Row Columns:** {list(selected_row.index)[:10]}")
                st.write(f"**Has risk_score:** {'risk_score' in selected_row.index}")
                st.write(f"**Has risk_band:** {'risk_band' in selected_row.index}")
                st.write(f"**Risk Score Value:** {selected_row.get('risk_score', 'N/A')}")
                st.write(f"**Risk Band Value:** {selected_row.get('risk_band', 'N/A')}")
            
            if model_info.get("status") == "Model trained":
                st.success("🤖 **ML-lite Model Active**: Using Logistic Regression coefficients for explanations")
                
                # Show model info in expander
                with st.expander("📊 Model Information", expanded=False):
                    st.json({
                        "Model Type": "Logistic Regression",
                        "Features": model_info.get("features", []),
                        "Intercept": f"{model_info.get('intercept', 0):.4f}",
                        "Status": "Trained and Ready"
                    })
                
                # Get explanations (try SHAP first, fallback to coefficients)
                explanations = []
                shap_data = None
                try:
                    # Use spinner to show progress
                    with st.spinner("🔄 Generating risk explanation..."):
                        explanations = explain_risk_score(selected_row, use_shap=True)
                    
                    # Get SHAP values for visualization
                    from risk_scoring import get_shap_values, SHAP_AVAILABLE
                    try:
                        shap_data = get_shap_values(selected_row)
                    except Exception as shap_err:
                        st.warning(f"⚠️ SHAP visualization unavailable: {str(shap_err)}")
                        shap_data = None
                    
                    # Debug: Always show what we got
                    if explanations is None:
                        explanations = []
                    st.write(f"**Debug:** Generated {len(explanations)} explanations")
                    
                    # Always display explanations if they exist
                    # Ensure explanations is a list
                    if explanations is None:
                        explanations = []
                    
                    if len(explanations) > 0:
                        if shap_data:
                            st.markdown("**🤖 ML-lite Model Analysis - SHAP-based Feature Contributions:**")
                            st.success("✅ Using SHAP (SHapley Additive exPlanations) for mathematically principled explanations")
                        else:
                            st.markdown("**🤖 ML-lite Model Analysis - Coefficient-based Feature Contributions:**")
                            st.info("ℹ️ Using Logistic Regression coefficients (SHAP not available)")
                        
                        st.markdown("")
                        
                        # Display each explanation
                        for explanation in explanations:
                            st.markdown(explanation)
                        
                        # SHAP visualization
                        if shap_data and SHAP_AVAILABLE:
                            st.markdown("")
                            st.markdown("**📊 SHAP Values Visualization:**")
                            
                            # Create a simple bar chart of SHAP values
                            import plotly.graph_objects as go
                            
                            feature_names = shap_data["feature_names"]
                            shap_vals = shap_data["shap_values"]
                            
                            # Sort by absolute SHAP value
                            sorted_data = sorted(zip(feature_names, shap_vals), key=lambda x: abs(x[1]), reverse=True)
                            sorted_features, sorted_shap = zip(*sorted_data)
                            
                            # Create bar chart
                            fig = go.Figure()
                            colors = ['red' if v > 0 else 'green' for v in sorted_shap]
                            fig.add_trace(go.Bar(
                                x=list(sorted_features),
                                y=list(sorted_shap),
                                marker_color=colors,
                                text=[f"{v:+.3f}" for v in sorted_shap],
                                textposition='outside',
                                name="SHAP Value"
                            ))
                            
                            fig.update_layout(
                                title="Feature Contributions to Fraud Risk (SHAP Values)",
                                xaxis_title="Features",
                                yaxis_title="SHAP Value (Impact on Fraud Probability)",
                                height=400,
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig, width='stretch')
                            
                            st.caption("💡 **SHAP Values**: Positive values (red) increase fraud risk, negative values (green) decrease risk. "
                                     "Magnitude shows the strength of the contribution.")
                        else:
                            st.markdown("")
                            st.caption("💡 **Note**: Coefficients show how each feature contributes to the fraud probability. "
                                     "Positive coefficients increase risk, negative coefficients decrease risk.")
                    else:
                        # Fallback: Show basic info even if no explanations
                        st.warning("⚠️ **No detailed explanations generated.** This might indicate:")
                        st.write("1. Model coefficients are very small")
                        st.write("2. Feature values are missing or invalid")
                        st.write("3. Transaction has no significant risk factors")
                        st.write(f"**Debug:** Explanation count = {len(explanations) if explanations else 0}")
                        
                        st.markdown("---")
                        st.markdown("### 📊 Basic Transaction Information")
                        
                        # Always show risk score and band
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if "risk_score" in selected_row.index:
                                risk_score = selected_row.get("risk_score", 0)
                                st.metric("Risk Score", f"{risk_score*100:.1f}%")
                            else:
                                st.metric("Risk Score", "N/A")
                        with col2:
                            if "risk_band" in selected_row.index:
                                risk_band = selected_row.get("risk_band", "UNKNOWN")
                                band_emoji = "🔴" if risk_band == "HIGH" else ("🟡" if risk_band == "MEDIUM" else "🟢")
                                st.metric("Risk Band", f"{band_emoji} {risk_band}")
                            else:
                                st.metric("Risk Band", "N/A")
                        with col3:
                            is_fraud = selected_row.get("is_fraud", False)
                            fraud_status = "✅ Fraud" if is_fraud else "❌ Legitimate"
                            st.metric("Fraud Status", fraud_status)
                        
                        # Show feature values
                        st.markdown("**📋 Feature Values:**")
                        feature_cols = ["txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d", 
                                       "is_high_risk_merchant", "is_emulator_device"]
                        feature_data = {}
                        for col in feature_cols:
                            if col in selected_row.index:
                                val = selected_row.get(col, "N/A")
                                if pd.notna(val):
                                    if isinstance(val, bool):
                                        feature_data[col] = "Yes" if val else "No"
                                    elif col == "merchant_fraud_rate_30d":
                                        feature_data[col] = f"{val*100:.2f}%"
                                    else:
                                        feature_data[col] = val
                                else:
                                    feature_data[col] = "N/A"
                            else:
                                feature_data[col] = "Not Available"
                        st.json(feature_data)
                except Exception as e:
                    st.error(f"❌ Error generating explanations: {str(e)}")
                    import traceback
                    with st.expander("🔍 Error Details", expanded=True):
                        st.code(traceback.format_exc())
                    
                    # Show fallback info even on error
                    st.info("Showing basic transaction information:")
                    if "risk_score" in selected_row.index:
                        st.metric("Risk Score", f"{selected_row['risk_score']*100:.1f}%")
                    if "risk_band" in selected_row.index:
                        st.metric("Risk Band", selected_row['risk_band'])
            else:
                st.warning("⚠️ **Model Not Trained**: Using fallback rule-based explanations")
                explanations = []
                try:
                    with st.spinner("🔄 Generating rule-based explanations..."):
                        explanations = explain_risk_score(selected_row, use_shap=False)
                    
                    st.write(f"**Debug:** Generated {len(explanations) if explanations else 0} rule-based explanations")
                    
                    if explanations and len(explanations) > 0:
                        st.markdown("**🔍 Risk Factors (Rule-based Analysis):**")
                        for i, explanation in enumerate(explanations, 1):
                            st.markdown(f"{i}. {explanation}")
                    else:
                        st.info("ℹ️ **No significant risk factors identified** for this transaction using rule-based analysis.")
                        
                        # Show feature values even if no explanations
                        st.markdown("**📋 Transaction Features:**")
                        feature_cols = ["txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d", 
                                       "is_high_risk_merchant", "is_emulator_device"]
                        for feat in feature_cols:
                            if feat in selected_row.index:
                                val = selected_row[feat]
                                if pd.notna(val):
                                    if isinstance(val, bool):
                                        val_display = "Yes" if val else "No"
                                    elif feat == "merchant_fraud_rate_30d":
                                        val_display = f"{val*100:.2f}%"
                                    else:
                                        val_display = f"{val:.2f}" if isinstance(val, float) else str(val)
                                    st.write(f"- **{feat.replace('_', ' ').title()}:** {val_display}")
                except Exception as e:
                    st.error(f"❌ **Error generating explanations:** {str(e)}")
                    import traceback
                    with st.expander("🔍 Error Details", expanded=True):
                        st.code(traceback.format_exc())
                    
                    # Always show something even on error
                    st.markdown("**📋 Showing basic transaction information:**")
                    if "risk_score" in selected_row.index:
                        st.metric("Risk Score", f"{selected_row.get('risk_score', 0)*100:.1f}%")
                    if "risk_band" in selected_row.index:
                        st.metric("Risk Band", selected_row.get('risk_band', 'UNKNOWN'))
                
                # Show feature values for this transaction
                st.markdown("---")
                st.markdown("### 📋 Feature Values")
                feature_cols = ["txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d", 
                               "is_high_risk_merchant", "is_emulator_device"]
                feature_data = []
                for feat in feature_cols:
                    if feat in selected_row.index:
                        val = selected_row[feat]
                        if isinstance(val, bool):
                            val = "Yes" if val else "No"
                        elif pd.notna(val) and feat == "merchant_fraud_rate_30d":
                            val = f"{val*100:.2f}%"
                        elif pd.notna(val):
                            val = f"{val:.2f}"
                        else:
                            val = "N/A"
                        feature_data.append({"Feature": feat.replace("_", " ").title(), "Value": val})
                
                if feature_data:
                    feature_df = pd.DataFrame(feature_data)
                    st.dataframe(feature_df, width='stretch', hide_index=True)
    
    # Project Showcase Section
    st.markdown("---")
    st.subheader("📊 Project Showcase")
    st.markdown("**Power BI Integration & Visualizations**")
    
    # Power BI file reference
    pbix_path = project_root / "Fraud_Analytics.pbix"
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
    st.info("💡 **TODO Stage 8B**: Add screenshots of Power BI dashboards here to showcase the project.")
    st.markdown("""
    You can add screenshots using:
    ```python
    st.image("path/to/screenshot.png", caption="Power BI Executive Dashboard")
    ```
    """)
    
    # Stage 8B TODO comments
    st.markdown("---")
    with st.expander("📝 Stage 8B TODO: ML-lite Implementation", expanded=False):
        st.markdown("""
        **Next Steps for Stage 8B:**
        
        1. **ML-lite Model Integration**
           - Replace placeholder scoring with ensemble models (Logistic Regression + Random Forest)
           - Load trained models from `models/` directory
           - Implement proper risk scoring pipeline
        
        2. **SHAP Explanations**
           - Replace text-based explanations with SHAP values
           - Show feature contributions visually
           - Add SHAP waterfall/bar plots for selected transactions
        
        3. **Performance Optimization**
           - Cache model loading
           - Batch scoring for large datasets
           - Lazy loading of SHAP explainers
        
        4. **Enhanced Visualizations**
           - Add Power BI screenshot embeddings
           - Create comparison charts (Streamlit vs Power BI)
           - Add interactive risk score distributions
        """)

# Footer
st.markdown("---")
st.caption("💡 **Stage 8A**: Visualization-focused app skeleton. Risk scoring uses placeholder rule-based logic. ML-lite implementation coming in Stage 8B.")

