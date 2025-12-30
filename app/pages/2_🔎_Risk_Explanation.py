"""
Risk Explanation Page

View detailed risk explanations for individual transactions.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st

from app.shared import get_filtered_data
from app.risk_scoring import explain_risk_score
from app.utils import format_currency

# Page config - skip if running from unified router
if 'unified_app' not in st.session_state or not st.session_state.get('unified_app', False):
    st.set_page_config(
        page_title="Risk Explanation",
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Hide Streamlit branding
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

# IMPORTANT: Setup sidebar FIRST before any main content
from app.shared import setup_sidebar_filters
df_full_filters = setup_sidebar_filters()

st.title("🔎 Risk Explanation")

# Get filtered data (skip scoring for faster load - we'll score selected transaction only)
try:
    with st.spinner("🔄 Loading transactions..."):
        df_full, df_filtered = get_filtered_data(skip_scoring=True)
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

if df_full.empty:
    st.error("⚠️ No transaction data found. Please run `src/export_bi_data.py` first to generate the BI export CSV.")
    st.stop()

if df_filtered.empty:
    st.warning("⚠️ No transactions match the selected filters. Please adjust your filters on the main page.")
    st.info("💡 **Tip**: Go to the Transaction Overview page to set filters.")
    st.stop()

# Ensure risk_score and risk_band columns exist
if 'risk_score' not in df_filtered.columns:
    df_filtered['risk_score'] = 0.5
if 'risk_band' not in df_filtered.columns:
    df_filtered['risk_band'] = 'MEDIUM'

# Pre-load models to ensure SHAP can work (if models exist)
from app.risk_scoring import _load_models, score_transactions
feature_columns = [
    "txns_last_24h", "declined_txns_last_24h", "merchant_fraud_rate_30d",
    "is_high_risk_merchant", "is_emulator_device"
]
available_features = [col for col in feature_columns if col in df_filtered.columns]
models_loaded = _load_models(available_features)

if models_loaded is None:
    st.info("💡 **Note**: Models not trained yet. Risk explanations will use rule-based analysis. Train models using `notebooks/07_model_training_experimentation.ipynb` for SHAP-based explanations.")

# Allow user to select a transaction
if "txn_id_clean" in df_filtered.columns:
    transaction_ids = df_filtered["txn_id_clean"].tolist()
    if transaction_ids:
        # Safe format function that handles missing data
        def format_txn_option(txn_id):
            try:
                row = df_filtered[df_filtered['txn_id_clean'] == txn_id]
                if not row.empty:
                    risk_score = row.iloc[0].get('risk_score', 0.5)
                    if risk_score <= 1.0:
                        return f"{txn_id} (Risk: {risk_score*100:.1f}%)"
                    else:
                        return f"{txn_id} (Risk: {risk_score:.1f})"
                return str(txn_id)
            except Exception:
                return str(txn_id)
        
        selected_txn_id = st.selectbox(
            "Select a transaction to view risk explanation:",
            options=transaction_ids[:1000],  # Limit to first 1000 for performance
            format_func=format_txn_option,
            key="risk_explanation_txn_selector"
        )
        
        if selected_txn_id:
            try:
                # Get the selected transaction row
                selected_row = df_filtered[df_filtered["txn_id_clean"] == selected_txn_id].iloc[0].copy()
                
                # Always score this transaction to ensure we have accurate risk score and models loaded
                with st.spinner("🔄 Calculating risk score and loading models..."):
                    single_df = pd.DataFrame([selected_row])
                    scored_df = score_transactions(single_df)
                    if not scored_df.empty:
                        selected_row = scored_df.iloc[0]
                
                # Display transaction details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_score = selected_row.get('risk_score', 0)
                    # Format as percentage if 0-1, otherwise as-is
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
                
                # Add amount in a new row
                st.markdown("---")
                col_amount = st.columns(1)[0]
                with col_amount:
                    amount = format_currency(selected_row.get("amount", 0))
                    st.metric("Transaction Amount", amount)
                
                st.markdown("---")
                
                # Display risk explanation
                st.subheader("🔍 Why is this transaction risky?")
                st.caption("💡 **SHAP-based explanations**: Feature contributions are calculated using SHapley Additive exPlanations, providing mathematically principled feature importance.")
                
                # Generate explanations
                with st.spinner("🔄 Generating risk explanation..."):
                    try:
                        explanations = explain_risk_score(selected_row)
                    except Exception as e:
                        st.warning(f"⚠️ Error generating explanation: {str(e)}")
                        st.info("Using fallback explanation...")
                        # explain_risk_score already has fallback logic, but if it fails completely, show basic info
                        explanations = [
                            f"Risk Score: {selected_row.get('risk_score', 0.5)*100:.1f}%",
                            f"Risk Band: {selected_row.get('risk_band', 'MEDIUM')}"
                        ]
                        if selected_row.get('is_fraud', False):
                            explanations.append("⚠️ This transaction is marked as fraud")
                
                if explanations:
                    st.markdown("#### Risk Factors:")
                    for i, explanation in enumerate(explanations, 1):
                        # Style high-impact explanations
                        if "increases risk" in explanation.lower() and any(x in explanation for x in ["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"]):
                            st.markdown(f"**{i}. {explanation}**")
                        else:
                            st.markdown(f"{i}. {explanation}")
                else:
                    st.info("ℹ️ No significant risk factors identified for this transaction.")
                
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
            except Exception as e:
                st.error(f"❌ Error processing transaction: {str(e)}")
                st.exception(e)
                st.info("💡 **Tip**: Try selecting a different transaction or check if models are trained.")
        else:
            st.info("ℹ️ Please select a transaction from the dropdown above to view risk explanation.")
    else:
        st.info("ℹ️ No transactions available for risk explanation.")
else:
    st.info("ℹ️ Transaction ID column not available. Risk explanation requires transaction identifiers.")

