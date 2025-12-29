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
    st.markdown("**Select chart type and parameters to explore your data dynamically**")
    
    if df_filtered.empty:
        st.warning("⚠️ No data to display. Adjust your filters.")
    else:
        # Chart type selector
        col1, col2 = st.columns([1, 2])
        
        with col1:
            chart_type = st.selectbox(
                "📊 Chart Type",
                options=[
                    "Bar Chart",
                    "Column Chart",
                    "Line Chart",
                    "Scatter Plot",
                    "Box Plot",
                    "Histogram",
                    "Violin Plot",
                    "Heatmap"
                ],
                key="chart_type_selector"
            )
        
        with col2:
            # Parameter selector based on available columns
            available_numeric = [col for col in df_filtered.columns if df_filtered[col].dtype in ['int64', 'float64']]
            available_categorical = [col for col in df_filtered.columns if df_filtered[col].dtype in ['object', 'bool', 'category']]
            
            # Initialize default values
            x_param = None
            y_param = None
            color_param = None
            size_param = None
            
            if chart_type in ["Bar Chart", "Column Chart", "Box Plot", "Violin Plot"]:
                x_param = st.selectbox(
                    "X-Axis / Category",
                    options=available_categorical + ["None"],
                    key="x_param_selector",
                    help="Select categorical variable for grouping"
                )
                y_param = st.selectbox(
                    "Y-Axis / Value",
                    options=available_numeric + ["None"],
                    key="y_param_selector",
                    help="Select numeric variable to measure"
                )
                color_param = st.selectbox(
                    "Color By (Optional)",
                    options=["None"] + available_categorical,
                    key="color_param_selector"
                )
            elif chart_type == "Scatter Plot":
                x_param = st.selectbox("X-Axis", options=available_numeric + ["None"], key="scatter_x")
                y_param = st.selectbox("Y-Axis", options=available_numeric + ["None"], key="scatter_y")
                color_param = st.selectbox("Color By", options=["None"] + available_categorical, key="scatter_color")
                size_param = st.selectbox("Size By (Optional)", options=["None"] + available_numeric, key="scatter_size")
            elif chart_type == "Line Chart":
                x_param = st.selectbox("X-Axis (Time)", options=["txn_date"] + available_numeric + ["None"], key="line_x")
                y_param = st.selectbox("Y-Axis", options=available_numeric + ["None"], key="line_y")
                color_param = st.selectbox("Color By", options=["None"] + available_categorical, key="line_color")
            elif chart_type == "Histogram":
                x_param = st.selectbox("Variable", options=available_numeric + ["None"], key="hist_x")
                color_param = st.selectbox("Color By (Optional)", options=["None"] + available_categorical, key="hist_color")
                y_param = None
            elif chart_type == "Heatmap":
                x_param = st.selectbox("X-Axis", options=available_categorical + ["None"], key="heat_x")
                y_param = st.selectbox("Y-Axis", options=available_categorical + ["None"], key="heat_y")
                color_param = st.selectbox("Value", options=available_numeric + ["None"], key="heat_value")
        
        st.markdown("---")
        
        # Generate chart based on selection
        # Ensure parameters are defined
        if x_param is None:
            x_param = "None"
        if y_param is None:
            y_param = "None"
        if color_param is None:
            color_param = "None"
        if size_param is None:
            size_param = "None"
            
        if chart_type == "Bar Chart" and x_param != "None" and y_param != "None":
            st.subheader(f"📊 Bar Chart: {y_param} by {x_param}")
            if color_param != "None":
                chart_data = df_filtered.groupby([x_param, color_param])[y_param].agg(['mean', 'sum', 'count']).reset_index()
                fig = px.bar(
                    chart_data,
                    x=x_param,
                    y='mean' if 'mean' in chart_data.columns else y_param,
                    color=color_param,
                    title=f"{y_param} by {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), 'mean': y_param.replace('_', ' ').title()}
                )
            else:
                chart_data = df_filtered.groupby(x_param)[y_param].agg(['mean', 'sum', 'count']).reset_index()
                fig = px.bar(
                    chart_data,
                    x=x_param,
                    y='mean' if 'mean' in chart_data.columns else y_param,
                    title=f"{y_param} by {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), 'mean': y_param.replace('_', ' ').title()}
                )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Column Chart" and x_param != "None" and y_param != "None":
            st.subheader(f"📊 Column Chart: {y_param} by {x_param}")
            if color_param != "None":
                chart_data = df_filtered.groupby([x_param, color_param])[y_param].agg(['mean', 'sum', 'count']).reset_index()
                fig = px.bar(
                    chart_data,
                    x=x_param,
                    y='mean' if 'mean' in chart_data.columns else y_param,
                    color=color_param,
                    orientation='v',
                    title=f"{y_param} by {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), 'mean': y_param.replace('_', ' ').title()}
                )
            else:
                chart_data = df_filtered.groupby(x_param)[y_param].agg(['mean', 'sum', 'count']).reset_index()
                fig = px.bar(
                    chart_data,
                    x=x_param,
                    y='mean' if 'mean' in chart_data.columns else y_param,
                    orientation='v',
                    title=f"{y_param} by {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), 'mean': y_param.replace('_', ' ').title()}
                )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Line Chart" and x_param != "None" and y_param != "None":
            st.subheader(f"📈 Line Chart: {y_param} over {x_param}")
            if x_param == "txn_date" and "txn_date" in df_filtered.columns:
                # Time series aggregation
                if color_param != "None":
                    daily_data = df_filtered.groupby([df_filtered["txn_date"].dt.date, color_param])[y_param].mean().reset_index()
                    daily_data.columns = ["Date", color_param, y_param]
                    fig = px.line(
                        daily_data,
                        x="Date",
                        y=y_param,
                        color=color_param,
                        title=f"{y_param} Over Time",
                        markers=True
                    )
                else:
                    daily_data = df_filtered.groupby(df_filtered["txn_date"].dt.date)[y_param].mean().reset_index()
                    daily_data.columns = ["Date", y_param]
                    fig = px.line(
                        daily_data,
                        x="Date",
                        y=y_param,
                        title=f"{y_param} Over Time",
                        markers=True
                    )
            else:
                if color_param != "None":
                    fig = px.line(
                        df_filtered.groupby([x_param, color_param])[y_param].mean().reset_index(),
                        x=x_param,
                        y=y_param,
                        color=color_param,
                        title=f"{y_param} by {x_param}",
                        markers=True
                    )
                else:
                    fig = px.line(
                        df_filtered.groupby(x_param)[y_param].mean().reset_index(),
                        x=x_param,
                        y=y_param,
                        title=f"{y_param} by {x_param}",
                        markers=True
                    )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Scatter Plot" and x_param != "None" and y_param != "None":
            st.subheader(f"🔍 Scatter Plot: {y_param} vs {x_param}")
            scatter_df = df_filtered[[x_param, y_param]].copy()
            if color_param != "None":
                scatter_df[color_param] = df_filtered[color_param]
            if size_param != "None":
                scatter_df[size_param] = df_filtered[size_param]
                fig = px.scatter(
                    scatter_df,
                    x=x_param,
                    y=y_param,
                    color=color_param if color_param != "None" else None,
                    size=size_param if size_param != "None" else None,
                    title=f"{y_param} vs {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), y_param: y_param.replace('_', ' ').title()}
                )
            else:
                fig = px.scatter(
                    scatter_df,
                    x=x_param,
                    y=y_param,
                    color=color_param if color_param != "None" else None,
                    title=f"{y_param} vs {x_param}",
                    labels={x_param: x_param.replace('_', ' ').title(), y_param: y_param.replace('_', ' ').title()}
                )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Box Plot" and x_param != "None" and y_param != "None":
            st.subheader(f"📦 Box Plot: {y_param} by {x_param}")
            fig = px.box(
                df_filtered,
                x=x_param,
                y=y_param,
                color=color_param if color_param != "None" else None,
                title=f"Distribution of {y_param} by {x_param}",
                labels={x_param: x_param.replace('_', ' ').title(), y_param: y_param.replace('_', ' ').title()}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Histogram" and x_param != "None":
            st.subheader(f"📊 Histogram: Distribution of {x_param}")
            fig = px.histogram(
                df_filtered,
                x=x_param,
                color=color_param if color_param != "None" else None,
                nbins=50,
                title=f"Distribution of {x_param}",
                labels={x_param: x_param.replace('_', ' ').title()}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Violin Plot" and x_param != "None" and y_param != "None":
            st.subheader(f"🎻 Violin Plot: {y_param} by {x_param}")
            fig = px.violin(
                df_filtered,
                x=x_param,
                y=y_param,
                color=color_param if color_param != "None" else None,
                title=f"Distribution of {y_param} by {x_param}",
                labels={x_param: x_param.replace('_', ' ').title(), y_param: y_param.replace('_', ' ').title()}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Heatmap" and x_param != "None" and y_param != "None" and color_param != "None":
            st.subheader(f"🔥 Heatmap: {color_param} by {x_param} and {y_param}")
            pivot_data = df_filtered.groupby([x_param, y_param])[color_param].mean().reset_index()
            pivot_table = pivot_data.pivot(index=y_param, columns=x_param, values=color_param)
            fig = px.imshow(
                pivot_table,
                title=f"{color_param} Heatmap",
                labels=dict(x=x_param.replace('_', ' ').title(), y=y_param.replace('_', ' ').title(), color=color_param.replace('_', ' ').title()),
                color_continuous_scale="RdYlBu_r"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("💡 Select chart type and parameters above to generate visualizations")
            
            # Show available columns for reference
            with st.expander("📋 Available Columns", expanded=False):
                st.markdown("**Numeric Columns:**")
                st.code(", ".join(available_numeric[:10]) + ("..." if len(available_numeric) > 10 else ""))
                st.markdown("**Categorical Columns:**")
                st.code(", ".join(available_categorical[:10]) + ("..." if len(available_categorical) > 10 else ""))
        
        # Pre-defined insightful charts section
        st.markdown("---")
        st.subheader("🎯 Pre-defined Analytics Charts")
        st.markdown("**Key insights from fraud analytics**")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Transaction Velocity Box Plot (from notebook)
            if "txns_last_24h" in df_filtered.columns and "is_fraud" in df_filtered.columns:
                st.markdown("**Transaction Velocity by Fraud Status**")
                df_plot = df_filtered[["txns_last_24h", "is_fraud"]].copy()
                df_plot["Transaction_Type"] = df_plot["is_fraud"].map({True: "Fraud", False: "Legitimate"})
                # Filter outliers for better visualization
                df_plot = df_plot[df_plot["txns_last_24h"] <= df_plot["txns_last_24h"].quantile(0.95)]
                fig_vel = px.box(
                    df_plot,
                    x="Transaction_Type",
                    y="txns_last_24h",
                    title="Transaction Velocity Comparison",
                    labels={"txns_last_24h": "Transactions Last 24h", "Transaction_Type": "Transaction Type"}
                )
                st.plotly_chart(fig_vel, use_container_width=True)
        
        with col_b:
            # Amount Deviation Histogram (from notebook)
            if "amount_vs_card_avg" in df_filtered.columns and "is_fraud" in df_filtered.columns:
                st.markdown("**Amount Deviation Distribution**")
                df_plot = df_filtered[["amount_vs_card_avg", "is_fraud"]].copy()
                df_plot["Transaction_Type"] = df_plot["is_fraud"].map({True: "Fraud", False: "Legitimate"})
                # Filter outliers
                df_plot = df_plot[(df_plot["amount_vs_card_avg"] >= 0) & (df_plot["amount_vs_card_avg"] <= 10)]
                fig_amt = px.histogram(
                    df_plot,
                    x="amount_vs_card_avg",
                    color="Transaction_Type",
                    nbins=50,
                    title="Amount vs Card Average Distribution",
                    labels={"amount_vs_card_avg": "Amount / Card Average", "count": "Frequency"},
                    barmode="overlay",
                    opacity=0.6
                )
                st.plotly_chart(fig_amt, use_container_width=True)
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            # Risk Score by Fraud Status
            if "risk_score" in df_filtered.columns and "is_fraud" in df_filtered.columns:
                st.markdown("**Risk Score Distribution by Fraud Status**")
                df_plot = df_filtered[["risk_score", "is_fraud"]].copy()
                df_plot["Transaction_Type"] = df_plot["is_fraud"].map({True: "Fraud", False: "Legitimate"})
                fig_risk = px.violin(
                    df_plot,
                    x="Transaction_Type",
                    y="risk_score",
                    color="Transaction_Type",
                    title="Risk Score Distribution",
                    labels={"risk_score": "Risk Score", "Transaction_Type": "Transaction Type"}
                )
                st.plotly_chart(fig_risk, use_container_width=True)
        
        with col_d:
            # Fraud Rate by Country
            if "country_std" in df_filtered.columns and "is_fraud" in df_filtered.columns:
                st.markdown("**Fraud Rate by Country**")
                country_fraud = df_filtered.groupby("country_std").agg({
                    "is_fraud": ["sum", "count"]
                }).reset_index()
                country_fraud.columns = ["Country", "Fraud_Count", "Total_Count"]
                country_fraud["Fraud_Rate"] = (country_fraud["Fraud_Count"] / country_fraud["Total_Count"] * 100).round(2)
                country_fraud = country_fraud.sort_values("Fraud_Rate", ascending=False).head(10)
                fig_country = px.bar(
                    country_fraud,
                    x="Country",
                    y="Fraud_Rate",
                    title="Top 10 Countries by Fraud Rate (%)",
                    labels={"Fraud_Rate": "Fraud Rate (%)", "Country": "Country"},
                    color="Fraud_Rate",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_country, use_container_width=True)

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

