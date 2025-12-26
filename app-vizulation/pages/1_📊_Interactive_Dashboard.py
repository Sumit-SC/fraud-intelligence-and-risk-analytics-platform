"""
Interactive Dashboard Page

Features:
- Interactive Plotly charts that update with filters
- PDF viewer for reports/presentations
- Power BI iframe embedding
"""

import sys
from pathlib import Path

# Add paths
app_dir = Path(__file__).parent.parent
project_root = app_dir.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_transaction_data, get_filter_options
from utils import format_currency, apply_filters
from risk_scoring import score_transactions

# Page config
st.set_page_config(
    page_title="Interactive Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Interactive Analytics Dashboard")
st.markdown("**Dynamic visualizations, reports, and Power BI integration**")

# Load data
df_full = load_transaction_data()

if df_full.empty:
    st.error("⚠️ No transaction data found. Please run `src/export_bi_data.py` first.")
    st.stop()

# Sidebar filters (same as main page)
st.sidebar.header("🔧 Filters")

# Date range filter
if "txn_date" in df_full.columns and not df_full["txn_date"].isna().all():
    date_min = df_full["txn_date"].min()
    date_max = df_full["txn_date"].max()
    
    date_range = st.sidebar.date_input(
        "Date Range (txn_date)",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
        key="dashboard_date_range"
    )
    
    if isinstance(date_range, tuple) and len(date_range) >= 2:
        date_start = pd.Timestamp(date_range[0]) if date_range[0] else None
        date_end = pd.Timestamp(date_range[1]) if date_range[1] else None
    else:
        date_start = None
        date_end = None
else:
    date_start = None
    date_end = None

# Get filter options
filter_options = get_filter_options(df_full)

# Other filters
merchant_risk_tier = st.sidebar.selectbox(
    "Merchant Risk Tier",
    options=["All"] + filter_options["merchant_risk_tiers"],
    key="dashboard_merchant_risk"
)

channel = st.sidebar.selectbox(
    "Channel",
    options=["All"] + filter_options["channels"],
    key="dashboard_channel"
)

country = st.sidebar.selectbox(
    "Country",
    options=["All"] + filter_options["countries"],
    key="dashboard_country"
)

fraud_filter = st.sidebar.selectbox(
    "Fraud Status",
    options=["All", "Fraud Only", "Non-Fraud Only"],
    key="dashboard_fraud"
)

# Apply filters
from utils import apply_filters
df_filtered = apply_filters(
    df_full,
    date_start=date_start,
    date_end=date_end,
    merchant_risk_tier=merchant_risk_tier,
    channel=channel,
    country=country,
    fraud_filter=fraud_filter
)

# Score transactions
if not df_filtered.empty:
    df_filtered = score_transactions(df_filtered)

# Sidebar metrics
st.sidebar.markdown("---")
st.sidebar.metric("Filtered Transactions", f"{len(df_filtered):,}")
if not df_filtered.empty and "is_fraud" in df_filtered.columns:
    fraud_count = df_filtered["is_fraud"].sum()
    st.sidebar.metric("Fraud Transactions", f"{fraud_count:,}")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📈 Interactive Charts", "📄 Reports & Presentations", "🔗 Power BI Integration"])

with tab1:
    st.header("📈 Interactive Visualizations")
    st.markdown("Charts update automatically based on your filter selections")
    
    if df_filtered.empty:
        st.warning("⚠️ No data to display. Adjust your filters.")
    else:
        # Chart 1: Fraud Rate Over Time
        st.subheader("📅 Fraud Rate Over Time")
        if "txn_date" in df_filtered.columns and "is_fraud" in df_filtered.columns:
            daily_fraud = df_filtered.groupby(df_filtered["txn_date"].dt.date).agg({
                "is_fraud": ["sum", "count"]
            }).reset_index()
            daily_fraud.columns = ["Date", "Fraud_Count", "Total_Count"]
            daily_fraud["Fraud_Rate"] = (daily_fraud["Fraud_Count"] / daily_fraud["Total_Count"] * 100).round(2)
            
            fig1 = px.line(
                daily_fraud,
                x="Date",
                y="Fraud_Rate",
                title="Daily Fraud Rate (%)",
                labels={"Fraud_Rate": "Fraud Rate (%)", "Date": "Date"},
                markers=True
            )
            fig1.update_traces(line_color='red', line_width=2)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Date or fraud data not available")
        
        # Chart 2: Risk Band Distribution
        st.subheader("🎯 Risk Band Distribution")
        if "risk_band" in df_filtered.columns:
            risk_dist = df_filtered["risk_band"].value_counts().reset_index()
            risk_dist.columns = ["Risk_Band", "Count"]
            risk_dist = risk_dist.sort_values("Count", ascending=False)
            
            colors_map = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green"}
            fig2 = px.bar(
                risk_dist,
                x="Risk_Band",
                y="Count",
                title="Transaction Count by Risk Band",
                color="Risk_Band",
                color_discrete_map=colors_map,
                labels={"Count": "Number of Transactions", "Risk_Band": "Risk Band"}
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Risk band data not available")
        
        # Chart 3: Fraud by Merchant Risk Tier
        st.subheader("🏪 Fraud by Merchant Risk Tier")
        if "merchant_risk_tier" in df_filtered.columns and "is_fraud" in df_filtered.columns:
            merchant_fraud = df_filtered.groupby("merchant_risk_tier").agg({
                "is_fraud": ["sum", "count"]
            }).reset_index()
            merchant_fraud.columns = ["Merchant_Risk_Tier", "Fraud_Count", "Total_Count"]
            merchant_fraud["Fraud_Rate"] = (merchant_fraud["Fraud_Count"] / merchant_fraud["Total_Count"] * 100).round(2)
            merchant_fraud = merchant_fraud.sort_values("Fraud_Rate", ascending=False)
            
            fig3 = px.bar(
                merchant_fraud,
                x="Merchant_Risk_Tier",
                y="Fraud_Rate",
                title="Fraud Rate by Merchant Risk Tier (%)",
                labels={"Fraud_Rate": "Fraud Rate (%)", "Merchant_Risk_Tier": "Merchant Risk Tier"},
                color="Merchant_Risk_Tier",
                color_discrete_map={"HIGH": "red", "MEDIUM": "orange", "LOW": "green"}
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Merchant risk tier or fraud data not available")
        
        # Chart 4: Transaction Amount Distribution
        st.subheader("💰 Transaction Amount Distribution")
        if "amount" in df_filtered.columns:
            fig4 = px.histogram(
                df_filtered,
                x="amount",
                nbins=50,
                title="Distribution of Transaction Amounts",
                labels={"amount": "Transaction Amount ($)", "count": "Frequency"},
                color_discrete_sequence=['blue']
            )
            fig4.update_layout(showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Amount data not available")
        
        # Chart 5: Fraud by Channel
        st.subheader("📱 Fraud by Channel")
        if "channel_std" in df_filtered.columns and "is_fraud" in df_filtered.columns:
            channel_fraud = df_filtered.groupby("channel_std").agg({
                "is_fraud": ["sum", "count"]
            }).reset_index()
            channel_fraud.columns = ["Channel", "Fraud_Count", "Total_Count"]
            channel_fraud["Fraud_Rate"] = (channel_fraud["Fraud_Count"] / channel_fraud["Total_Count"] * 100).round(2)
            channel_fraud = channel_fraud.sort_values("Fraud_Rate", ascending=False)
            
            fig5 = px.bar(
                channel_fraud,
                x="Channel",
                y="Fraud_Rate",
                title="Fraud Rate by Channel (%)",
                labels={"Fraud_Rate": "Fraud Rate (%)", "Channel": "Channel"},
                color="Fraud_Rate",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Channel or fraud data not available")
        
        # Chart 6: Risk Score Distribution
        st.subheader("📊 Risk Score Distribution")
        if "risk_score" in df_filtered.columns:
            fig6 = px.histogram(
                df_filtered,
                x="risk_score",
                nbins=50,
                title="Distribution of ML-lite Risk Scores",
                labels={"risk_score": "Risk Score (0-1)", "count": "Frequency"},
                color_discrete_sequence=['purple']
            )
            fig6.update_layout(showlegend=False)
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("Risk score data not available")

with tab2:
    st.header("📄 Reports & Presentations")
    st.markdown("Upload and view PDF reports, presentations, and documentation")
    
    # PDF uploader
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=['pdf'],
        help="Upload a PDF file to view it in the browser"
    )
    
    if uploaded_file is not None:
        # Display PDF
        st.subheader(f"📄 {uploaded_file.name}")
        
        # Save uploaded file temporarily
        import tempfile
        import base64
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        # Display PDF using iframe
        with open(tmp_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Cleanup
        import os
        os.unlink(tmp_path)
    else:
        st.info("💡 Upload a PDF file to view it here. Supported formats: Reports, Presentations, Documentation")
        
        # Instructions
        with st.expander("📋 How to use PDF viewer", expanded=True):
            st.markdown("""
            **Steps:**
            1. Click "Browse files" above
            2. Select a PDF file from your computer
            3. The PDF will be displayed in the viewer below
            
            **Supported content:**
            - Project reports
            - Presentation slides
            - Documentation
            - Analysis summaries
            """)

with tab3:
    st.header("🔗 Power BI Integration")
    st.markdown("Embed Power BI dashboards from Power BI Service")
    
    # Power BI embed URL input
    powerbi_url = st.text_input(
        "Power BI Embed URL",
        placeholder="https://app.powerbi.com/view?r=...",
        help="Paste your Power BI shared link or embed URL here"
    )
    
    if powerbi_url:
        st.subheader("📊 Power BI Dashboard")
        
        # Convert Power BI URL to embed format if needed
        # Power BI URLs need to be in embed format: https://app.powerbi.com/view?r=...
        if "app.powerbi.com" in powerbi_url:
            # Extract the report ID if it's a share link
            if "/view?" in powerbi_url:
                embed_url = powerbi_url
            else:
                # Try to convert share link to embed link
                embed_url = powerbi_url.replace("/reportEmbed", "/view")
            
            # Display Power BI iframe
            powerbi_iframe = f'<iframe src="{embed_url}" width="100%" height="800px" frameborder="0" allowFullScreen="true"></iframe>'
            st.markdown(powerbi_iframe, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please enter a valid Power BI URL (should contain 'app.powerbi.com')")
    else:
        st.info("💡 Enter a Power BI embed URL to display the dashboard")
        
        # Instructions
        with st.expander("📋 How to get Power BI embed URL", expanded=True):
            st.markdown("""
            **Option 1: Power BI Service (Recommended)**
            1. Open your dashboard in Power BI Service
            2. Click "Share" → "Embed" → "Website or portal"
            3. Copy the embed URL
            4. Paste it above
            
            **Option 2: Direct Link**
            1. In Power BI Service, click "Share" → "Get a link"
            2. Copy the link (format: `https://app.powerbi.com/view?r=...`)
            3. Paste it above
            
            **Note:** 
            - You need Power BI Pro or Premium Per User (PPU) license
            - The dashboard must be published to Power BI Service
            - Make sure the link has appropriate permissions
            """)
        
        # Local Power BI file info
        pbix_path = project_root / "Fraud_Analytics.pbix"
        if pbix_path.exists():
            st.markdown("---")
            st.info(f"📁 **Local Power BI File Found**: `{pbix_path.name}`")
            st.markdown("""
            **To view locally:**
            1. Open `Fraud_Analytics.pbix` in Power BI Desktop
            2. Or publish to Power BI Service and use the embed URL above
            """)

# Footer
st.markdown("---")
st.caption("💡 **Interactive Dashboard**: All charts update automatically when you change filters in the sidebar. Upload PDFs and embed Power BI dashboards for a complete analytics experience.")

