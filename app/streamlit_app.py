"""
Fraud Investigation & Risk Scoring - Main Page

Transaction Overview page with filters.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.shared import setup_sidebar_filters, get_filtered_data
from app.utils import format_currency

# Note: Removed atexit handler - Streamlit handles cleanup automatically
# Adding atexit handlers can cause delays and errors during shutdown


def _generate_risk_assessment(row: pd.Series) -> str:
    """
    Generate a one-liner risk assessment for a transaction.
    
    Args:
        row: Transaction row (Series)
        
    Returns:
        One-liner risk assessment string
    """
    risk_score = row.get("risk_score", 0)
    risk_band = row.get("risk_band", "LOW")
    is_fraud = row.get("is_fraud", False)
    
    # Normalize risk score to 0-1 if needed
    if risk_score > 1.0:
        risk_score = risk_score / 100.0
    
    # Build assessment based on risk level and key factors
    if risk_band == "HIGH" or risk_score >= 0.6:
        if is_fraud:
            assessment = "🚨 **HIGH RISK FRAUDSTER** - Confirmed fraud with multiple high-risk indicators"
        else:
            factors = []
            if row.get("txns_last_24h", 0) > 10:
                factors.append("high velocity")
            if row.get("declined_txns_last_24h", 0) > 2:
                factors.append("multiple declines")
            if row.get("is_high_risk_merchant", False):
                factors.append("high-risk merchant")
            if row.get("is_emulator_device", False):
                factors.append("emulator device")
            if row.get("merchant_fraud_rate_30d", 0) > 0.1:
                factors.append("elevated merchant fraud rate")
            
            if factors:
                factor_str = ", ".join(factors)
                assessment = f"🚨 **HIGH RISK** - Strong fraud signals detected: {factor_str}"
            else:
                assessment = "🚨 **HIGH RISK** - Elevated fraud probability based on ensemble model"
    
    elif risk_band == "MEDIUM" or risk_score >= 0.3:
        factors = []
        if row.get("txns_last_24h", 0) > 5:
            factors.append("moderate velocity")
        if row.get("is_high_risk_merchant", False):
            factors.append("high-risk merchant")
        
        if factors:
            factor_str = ", ".join(factors)
            assessment = f"⚠️ **MEDIUM RISK** - Review recommended due to: {factor_str}"
        else:
            assessment = "⚠️ **MEDIUM RISK** - Moderate fraud probability, manual review suggested"
    
    else:
        if is_fraud:
            assessment = "✅ **LOW RISK (False Negative)** - Legitimate-looking but confirmed fraud (model miss)"
        else:
            assessment = "✅ **LOW RISK** - Transaction appears legitimate with minimal risk indicators"
    
    return assessment

# Page configuration (skip if running from unified router)
if 'unified_app' not in st.session_state or not st.session_state.get('unified_app', False):
    st.set_page_config(
        page_title="Transaction Overview",
        page_icon="📊",
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

# IMPORTANT: Setup sidebar FIRST before any main content (ensures sidebar renders)
setup_sidebar_filters()

# App Title at Top
st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Fraud Intelligence & Risk Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; margin-bottom: 10px;'>📊 Transaction Overview</p>", unsafe_allow_html=True)

# Lightweight view mode selector – lets us run a cheaper, aggregate-first view
view_mode = st.radio(
    "View mode",
    options=["🚀 Lite (fast, aggregate)", "🔬 Detailed (full scoring)"],
    horizontal=True,
    key="overview_view_mode",
    help="Lite mode is optimized for Streamlit Community Cloud and large datasets; Detailed mode adds ML scoring detail."
)

skip_scoring = view_mode.startswith("🚀")

try:
    # Cloud-friendly: compute stats via Polars, load only a limited filtered sample
    # In Lite mode we skip ML scoring to save memory/CPU on large datasets
    dataset_stats, filtered_summary, df_filtered = get_filtered_data(skip_scoring=skip_scoring)
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.exception(e)
    st.stop()

if dataset_stats.get("total_rows", 0) == 0:
    st.error("⚠️ No transaction data found. Please run `src/export_bi_data.py` first to generate the BI export CSV.")
    st.stop()

# Get max rows limit from session state (set in filters section)
# Default to filtered count if not set
table_data_limit = st.session_state.get("table_data_limit", len(df_filtered) if not df_filtered.empty else 0)

# Display filter summary in sidebar
st.sidebar.markdown("---")
st.sidebar.metric("Filtered Transactions", f"{int(filtered_summary.get('filtered_rows', 0) or 0):,}")
st.sidebar.metric("Fraud Transactions", f"{int(filtered_summary.get('fraud_rows', 0) or 0):,}")

# Main content
if df_filtered.empty:
    st.warning("⚠️ No transactions match the selected filters. Please adjust your filters.")
    st.info("💡 **Tip**: Adjust your filters in the sidebar to see transaction data.")
else:
    # Dataset Overview Section (before transaction table)
    st.markdown("---")
    st.subheader("📊 Dataset Overview")
    
    # Create overview metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Dataset", f"{int(dataset_stats.get('total_rows', 0) or 0):,}")
    
    with col2:
        st.metric("Filtered Transactions", f"{int(filtered_summary.get('filtered_rows', 0) or 0):,}")
    
    with col3:
        filtered_rows = int(filtered_summary.get("filtered_rows", 0) or 0)
        fraud_rows = int(filtered_summary.get("fraud_rows", 0) or 0)
        fraud_pct = (fraud_rows / filtered_rows * 100) if filtered_rows > 0 else 0
        st.metric("Fraud Rate", f"{fraud_pct:.2f}%")
    
    with col4:
        dmin = filtered_summary.get("date_min")
        dmax = filtered_summary.get("date_max")
        if dmin is not None and dmax is not None:
            date_range = f"{pd.to_datetime(dmin).date()} to {pd.to_datetime(dmax).date()}"
            st.metric("Date Range", date_range[:20] + "..." if len(date_range) > 20 else date_range)
        else:
            st.metric("Date Range", "N/A")
    
    # Additional stats in expandable section + Plotly-style aggregate visuals
    with st.expander("📈 Detailed Dataset Statistics & Aggregates", expanded=False):
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.markdown("**Dataset Information**")
            stats_data = []
            stats_data.append({"Metric": "Total Rows (Full Dataset)", "Value": f"{int(dataset_stats.get('total_rows', 0) or 0):,}"})
            stats_data.append({"Metric": "Filtered Rows", "Value": f"{int(filtered_summary.get('filtered_rows', 0) or 0):,}"})
            stats_data.append({"Metric": "Total Columns", "Value": f"{len(df_filtered.columns)}"})
            
            if 'amount' in df_filtered.columns:
                stats_data.append({"Metric": "Avg Transaction Amount", "Value": format_currency(df_filtered['amount'].mean())})
                stats_data.append({"Metric": "Total Transaction Amount", "Value": format_currency(df_filtered['amount'].sum())})
            
            if 'txn_date' in df_filtered.columns and not df_filtered['txn_date'].isna().all():
                stats_data.append({"Metric": "Date Range (sample)", "Value": f"{df_filtered['txn_date'].min().date()} to {df_filtered['txn_date'].max().date()}"})
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, width='stretch', hide_index=True)
        
        with stats_col2:
            st.markdown("**Fraud Statistics (Aggregated)**")
            fraud_stats = []
            filtered_rows = int(filtered_summary.get("filtered_rows", 0) or 0)
            fraud_count = int(filtered_summary.get("fraud_rows", 0) or 0)
            non_fraud_count = max(filtered_rows - fraud_count, 0)
            fraud_pct = (fraud_count / filtered_rows * 100) if filtered_rows > 0 else 0
            
            fraud_stats.append({"Metric": "Fraud Transactions", "Value": f"{fraud_count:,}"})
            fraud_stats.append({"Metric": "Non-Fraud Transactions", "Value": f"{non_fraud_count:,}"})
            fraud_stats.append({"Metric": "Fraud Rate", "Value": f"{fraud_pct:.2f}%"})
            
            if 'merchant_risk_tier' in df_filtered.columns:
                fraud_stats.append({"Metric": "Merchant Risk Tiers (sample)", "Value": f"{df_filtered['merchant_risk_tier'].nunique()}"})
            
            if 'channel_std' in df_filtered.columns:
                fraud_stats.append({"Metric": "Channels (sample)", "Value": f"{df_filtered['channel_std'].nunique()}"})
            
            if 'country_std' in df_filtered.columns:
                fraud_stats.append({"Metric": "Countries (sample)", "Value": f"{df_filtered['country_std'].nunique()}"})
            
            fraud_stats_df = pd.DataFrame(fraud_stats)
            st.dataframe(fraud_stats_df, width='stretch', hide_index=True)
        
        # Optional: lightweight Plotly-style breakdowns using the sampled df
        try:
            import plotly.express as px
            
            plot_col1, plot_col2 = st.columns(2)
            with plot_col1:
                if 'merchant_risk_tier' in df_filtered.columns and 'is_fraud' in df_filtered.columns:
                    tmp = (
                        df_filtered
                        .groupby(['merchant_risk_tier', 'is_fraud'])
                        .size()
                        .reset_index(name='count')
                    )
                    fig = px.bar(
                        tmp,
                        x="merchant_risk_tier",
                        y="count",
                        color="is_fraud",
                        barmode="group",
                        title="Fraud vs Non-Fraud by Merchant Risk Tier (sample)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with plot_col2:
                if 'channel_std' in df_filtered.columns and 'is_fraud' in df_filtered.columns:
                    tmp = (
                        df_filtered
                        .groupby(['channel_std', 'is_fraud'])
                        .size()
                        .reset_index(name='count')
                    )
                    fig = px.bar(
                        tmp,
                        x="channel_std",
                        y="count",
                        color="is_fraud",
                        barmode="group",
                        title="Fraud vs Non-Fraud by Channel (sample)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
        except Exception:
            # If Plotly isn't available, silently skip interactive charts
            pass
    
    st.markdown("---")
    st.subheader("📋 Transaction Overview")
    
    # Check if we have unscored rows (placeholders) - show helpful message
    if 'risk_score' in df_filtered.columns:
        from app.risk_scoring import _load_models
        feature_columns = [
            "txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d",
            "is_high_risk_merchant", "is_emulator_device"
        ]
        available_features = [col for col in feature_columns if col in df_filtered.columns]
        models_exist = _load_models(available_features) is not None
        
        if models_exist:
            unscored_count = len(df_filtered[df_filtered['risk_score'] == 0.5])
            if unscored_count > 0 and len(df_filtered) > 5000:
                st.info(
                    f"ℹ️ **Performance Note**: Showing first 5,000 scored transactions. "
                    f"{unscored_count:,} additional transactions are available but not yet scored. "
                    f"Apply filters to reduce dataset size for full scoring."
                )
        else:
            st.info(
                "💡 **Note**: Models not trained yet. Showing transactions with placeholder risk scores. "
                "Train models using `notebooks/07_model_training_experimentation.ipynb` for accurate risk scores."
            )
    
    # Sort by risk score (descending) if available, otherwise by date
    if 'risk_score' in df_filtered.columns:
        df_display = df_filtered.sort_values("risk_score", ascending=False, na_position="last")
    elif 'txn_date' in df_filtered.columns:
        df_display = df_filtered.sort_values("txn_date", ascending=False, na_position="last")
    else:
        df_display = df_filtered.copy()
    
    # NOTE: df_filtered is already a limited sample (hard-capped) for cloud safety.
    df_display = df_filtered.copy()
    
    # Select columns for display
    display_columns = [
        "txn_id_clean",
        "txn_date",
        "amount",
        "txns_last_24h",
        "merchant_risk_tier",
        "is_fraud",
        "risk_score",
        "risk_band"
    ]
    
    # Ensure all columns exist
    available_columns = [col for col in display_columns if col in df_display.columns]
    
    if not available_columns:
        st.error("❌ No displayable columns found in data")
        st.stop()
    
    df_table = df_display[available_columns].copy()
    
    # Format columns for display
    if "amount" in df_table.columns:
        df_table["amount"] = df_table["amount"].apply(format_currency)
    if "is_fraud" in df_table.columns:
        df_table["is_fraud"] = df_table["is_fraud"].map({True: "✅ Yes", False: "❌ No"})
    if "risk_score" in df_table.columns:
        # Format as percentage (0-1 -> 0-100%)
        df_table["risk_score"] = df_table["risk_score"].apply(lambda x: f"{x*100:.1f}%" if x <= 1.0 else f"{x:.1f}%")
    if "risk_band" in df_table.columns:
        # Add emoji indicators for risk bands
        df_table["risk_band"] = df_table["risk_band"].apply(
            lambda x: f"🔴 {x}" if x == "HIGH" else (f"🟡 {x}" if x == "MEDIUM" else f"🟢 {x}")
        )
    
    # Rename columns for better display
    column_rename = {
        "txn_id_clean": "Transaction ID",
        "txn_date": "Date",
        "amount": "Amount",
        "txns_last_24h": "Txns (24h)",
        "merchant_risk_tier": "Merchant Risk",
        "is_fraud": "Fraud",
        "risk_score": "Risk Score",
        "risk_band": "Risk Band"
    }
    df_table = df_table.rename(columns=column_rename)
    
    # Transaction Selection & Quick Analysis
    st.markdown("---")
    st.subheader("🔍 Transaction Quick Analysis")
    
    # Create transaction selector with formatted display
    if "txn_id_clean" in df_display.columns:
        # Get all transaction IDs (show all, not limited)
        transaction_options = df_display["txn_id_clean"].unique().tolist()
        
        if transaction_options:
            # Format display to show risk score and key info
            def format_txn_option(txn_id):
                try:
                    row = df_display[df_display["txn_id_clean"] == txn_id]
                    if not row.empty:
                        row_data = row.iloc[0]
                        risk_score = row_data.get("risk_score", 0.5)
                        risk_band = row_data.get("risk_band", "MEDIUM")
                        amount = row_data.get("amount", 0)
                        is_fraud = "✅ Fraud" if row_data.get("is_fraud", False) else "❌ Legit"
                        
                        # Format risk score
                        if risk_score <= 1.0:
                            risk_pct = f"{risk_score*100:.1f}%"
                        else:
                            risk_pct = f"{risk_score:.1f}"
                        
                        # Risk band emoji
                        band_emoji = "🔴" if risk_band == "HIGH" else ("🟡" if risk_band == "MEDIUM" else "🟢")
                        
                        return f"{txn_id} | {band_emoji} {risk_band} ({risk_pct}) | {format_currency(amount)} | {is_fraud}"
                    return str(txn_id)
                except Exception:
                    return str(txn_id)
            
            selected_txn_id = st.selectbox(
                "Select a transaction to view detailed analysis:",
                options=transaction_options,
                format_func=format_txn_option,
                key="selected_transaction_quick"
            )
            
            if selected_txn_id:
                try:
                    selected_row = df_display[df_display["txn_id_clean"] == selected_txn_id].iloc[0]
                    
                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        risk_score = selected_row.get('risk_score', 0)
                        if risk_score <= 1.0:
                            st.metric("Risk Score", f"{risk_score*100:.1f}%")
                        else:
                            st.metric("Risk Score", f"{risk_score:.1f}/100")
                    
                    with col2:
                        fraud_status = "✅ Fraud" if selected_row.get("is_fraud", False) else "❌ Non-Fraud"
                        st.metric("Fraud Status", fraud_status)
                    
                    with col3:
                        risk_band = selected_row.get("risk_band", "LOW")
                        band_emoji = "🔴" if risk_band == "HIGH" else ("🟡" if risk_band == "MEDIUM" else "🟢")
                        st.metric("Risk Band", f"{band_emoji} {risk_band}")
                    
                    with col4:
                        amount = format_currency(selected_row.get("amount", 0))
                        st.metric("Transaction Amount", amount)
                    
                    # One-liner risk assessment
                    st.markdown("---")
                    assessment = _generate_risk_assessment(selected_row)
                    st.markdown(f"**Risk Assessment:** {assessment}")
                    
                    # Key risk parameters
                    st.markdown("---")
                    st.subheader("Key Risk Parameters")
                    
                    param_col1, param_col2 = st.columns(2)
                    
                    with param_col1:
                        st.markdown("**Transaction Behavior:**")
                        if "txns_last_24h" in selected_row.index:
                            st.write(f"• Transactions (24h): **{selected_row['txns_last_24h']:.0f}**")
                        if "declined_txns_last_24h" in selected_row.index:
                            st.write(f"• Declined (24h): **{selected_row['declined_txns_last_24h']:.0f}**")
                        if "amount_vs_card_avg" in selected_row.index:
                            ratio = selected_row["amount_vs_card_avg"]
                            if pd.notna(ratio):
                                st.write(f"• Amount vs Card Avg: **{ratio:.2f}x**")
                    
                    with param_col2:
                        st.markdown("**Merchant & Device:**")
                        if "merchant_risk_tier" in selected_row.index:
                            tier = selected_row["merchant_risk_tier"]
                            st.write(f"• Merchant Risk: **{tier}**")
                        if "merchant_fraud_rate_30d" in selected_row.index:
                            rate = selected_row["merchant_fraud_rate_30d"]
                            if pd.notna(rate):
                                st.write(f"• Merchant Fraud Rate (30d): **{rate*100:.1f}%**")
                        if "is_emulator_device" in selected_row.index:
                            emulator = "Yes" if selected_row["is_emulator_device"] else "No"
                            st.write(f"• Emulator Device: **{emulator}**")
                    
                    # Quick action buttons
                    st.markdown("---")
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button("🔎 View Full Explanation", key="view_full_explanation"):
                            st.session_state["navigate_to_explanation"] = selected_txn_id
                            st.info("💡 Navigate to 'Risk Explanation' page for detailed SHAP-based analysis")
                    with action_col2:
                        st.caption("💡 Use the Risk Explanation page for detailed feature contributions")
                except Exception as e:
                    st.error(f"Error loading transaction: {str(e)}")
                    st.exception(e)
        else:
            st.info("No transactions available for quick analysis.")
    else:
        st.info("Transaction ID column not available.")
    
    # Display table - ALWAYS show, even if empty or has issues
    st.markdown("---")
    st.subheader("📊 Transaction Table")
    
    if df_table.empty:
        st.warning("⚠️ No transactions to display. Please check your filters.")
    else:
        st.dataframe(
            df_table,
            width='stretch',
            hide_index=True,
            height=400
        )
    
    # Risk Scoring Metrics (Prominent, separate section)
    st.markdown("---")
    st.subheader("🎯 Risk Scoring Metrics")
    
    if "risk_score" in df_filtered.columns and "risk_band" in df_filtered.columns:
        # Calculate metrics
        avg_risk = df_filtered["risk_score"].mean()
        risk_band_counts = df_filtered["risk_band"].value_counts().to_dict()
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Average Risk Score",
                value=f"{avg_risk*100:.1f}%" if avg_risk <= 1.0 else f"{avg_risk:.1f}%",
                help="Average fraud probability across all transactions"
            )
        
        with col2:
            high_risk_count = risk_band_counts.get("HIGH", 0)
            st.metric(
                label="High Risk Transactions",
                value=f"{high_risk_count:,}",
                help="Transactions with ≥60% fraud probability"
            )
        
        with col3:
            medium_risk_count = risk_band_counts.get("MEDIUM", 0)
            st.metric(
                label="Medium Risk Transactions",
                value=f"{medium_risk_count:,}",
                help="Transactions with 30-60% fraud probability"
            )
        
        with col4:
            low_risk_count = risk_band_counts.get("LOW", 0)
            st.metric(
                label="Low Risk Transactions",
                value=f"{low_risk_count:,}",
                help="Transactions with <30% fraud probability"
            )
        
        # Risk distribution visualization
        st.markdown("#### Risk Band Distribution")
        risk_dist_df = pd.DataFrame({
            "Risk Band": ["LOW", "MEDIUM", "HIGH"],
            "Count": [
                risk_band_counts.get("LOW", 0),
                risk_band_counts.get("MEDIUM", 0),
                risk_band_counts.get("HIGH", 0)
            ],
            "Percentage": [
                (risk_band_counts.get("LOW", 0) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0,
                (risk_band_counts.get("MEDIUM", 0) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0,
                (risk_band_counts.get("HIGH", 0) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
            ]
        })
        risk_dist_df["Percentage"] = risk_dist_df["Percentage"].round(1)
        
        st.bar_chart(risk_dist_df.set_index("Risk Band")["Count"])
        st.dataframe(risk_dist_df, width='stretch', hide_index=True)
    else:
        st.info("Risk scoring metrics not available. Train models to see risk distribution.")
    
    # Footer
    st.markdown("---")
    st.caption("💡 **ML-lite Risk Scoring**: Uses ensemble of Logistic Regression and Random Forest models. Risk scores are probabilities (0-1) indicating fraud likelihood.")
