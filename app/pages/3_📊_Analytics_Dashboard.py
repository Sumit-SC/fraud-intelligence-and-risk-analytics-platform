"""
Analytics Dashboard Page

Explore fraud patterns, trends, and risk concentrations.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.shared import get_filtered_data
from app.analytics import (
    get_fraud_trends,
    get_geographic_analysis,
    get_top_risky_merchants,
    get_top_risky_cards,
    get_channel_analysis,
    get_hourly_patterns
)

# Page config - skip if running from unified router
if 'unified_app' not in st.session_state or not st.session_state.get('unified_app', False):
    st.set_page_config(
        page_title="Analytics Dashboard",
        page_icon="📊",
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

st.title("📊 Analytics Dashboard")
st.markdown("**Explore fraud patterns, trends, and risk concentrations across different dimensions.**")

# Get filtered data (skip scoring for faster load - analytics doesn't need risk scores)
try:
    with st.spinner("🔄 Loading transactions..."):
        # get_filtered_data returns (dataset_stats, filtered_summary, df_rows)
        dataset_stats, filtered_summary, df_filtered = get_filtered_data(skip_scoring=True)
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

if df_filtered.empty:
    st.warning("⚠️ No transactions match the selected filters. Please adjust your filters on the main page.")
    st.info("💡 **Tip**: Go to the Transaction Overview page to set filters.")
    st.stop()

# Dataset size selector on main page (default 10K) - for charting performance
st.markdown("---")
col_info, col_selector = st.columns([2, 1])
with col_info:
    st.markdown(f"**📊 Filtered Data:** {len(df_filtered):,} transactions")
with col_selector:
    # Dataset size options (kept conservative for Streamlit Cloud)
    chunk_options = {
        "5K": 5000,
        "10K": 10000,
        "25K": 25000,
        "50K (cap)": 50000,
    }
    
    # Filter out options larger than available filtered data
    available_chunks = {k: v for k, v in chunk_options.items() if v <= len(df_filtered)}
    if not available_chunks:
        available_chunks = {"All Filtered": len(df_filtered)}
    
    # Default to 10K (index 1 if available, otherwise first option)
    keys = list(available_chunks.keys())
    default_index = keys.index("10K") if "10K" in keys else 0
    
    selected_chunk_label = st.selectbox(
        "📊 Dataset Size (sample for charts)",
        options=keys,
        index=default_index,
        key="analytics_dataset_size",
        help="Filters are applied first, then a random sample is taken for charting to keep performance smooth."
    )
    dataset_size = available_chunks[selected_chunk_label]

# Sample data based on selected size (default 10K) - for all analytics
if len(df_filtered) > dataset_size:
    df_chart = df_filtered.sample(n=dataset_size, random_state=42).copy()
    st.info(f"📊 Using {dataset_size:,} randomly sampled data points (from {len(df_filtered):,} filtered transactions) for analytics to improve performance.")
else:
    df_chart = df_filtered.copy()
    if len(df_filtered) > 0:
        st.success(f"✅ Using all {len(df_filtered):,} filtered transactions for analytics.")

# Analytics tabs - always show, even if some tabs have no data
analytics_tabs = st.tabs([
    "📈 Trends Over Time",
    "🌍 Geographic Analysis",
    "🏪 Top Risky Merchants",
    "💳 Top Risky Cards",
    "📱 Channel Analysis",
    "🕐 Hourly Patterns"
])

with analytics_tabs[0]:
    st.subheader("Fraud Trends Over Time")
    try:
        import plotly.express as px
        if "txn_date" in df_chart.columns and "is_fraud" in df_chart.columns:
            trends_df = get_fraud_trends(df_chart)
            if not trends_df.empty:
                fig = px.line(
                    trends_df,
                    x="date",
                    y=["fraud_count", "non_fraud_count"],
                    title="Fraud vs Non-Fraud Transactions Over Time",
                    labels={"value": "Transaction Count", "date": "Date", "variable": "Type"},
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(trends_df, width='stretch', hide_index=True)
            else:
                st.info("No date data available for trend analysis.")
        else:
            st.info("Date or fraud column not available for trend analysis.")
    except Exception as e:
        st.error(f"Error generating trends: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[1]:
    st.subheader("Fraud by Country")
    try:
        import plotly.express as px
        geo_df = get_geographic_analysis(df_chart)
        if not geo_df.empty:
            fig = px.bar(
                geo_df,
                x="country",
                y="fraud_rate",
                title="Fraud Rate by Country",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(geo_df, width='stretch', hide_index=True)
        else:
            st.info("No geographic data available.")
    except Exception as e:
        st.error(f"Error generating geographic analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[2]:
    st.subheader("Top Risky Merchants")
    try:
        import plotly.express as px
        merchants_df = get_top_risky_merchants(df_chart, top_n=20)
        if not merchants_df.empty:
            fig = px.bar(
                merchants_df,
                x="merchant_id",
                y="fraud_count",
                title="Top Merchants by Fraud Count (sample)",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(merchants_df, width='stretch', hide_index=True)
        else:
            st.info("No merchant data available.")
    except Exception as e:
        st.error(f"Error generating merchant analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[3]:
    st.subheader("Top Risky Cards")
    try:
        import plotly.express as px
        cards_df = get_top_risky_cards(df_chart, top_n=20)
        if not cards_df.empty:
            if "card_id" in cards_df.columns:
                fig = px.bar(
                    cards_df,
                    x="card_id",
                    y="fraud_count",
                    title="Top Cards by Fraud Count (sample)",
                )
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(cards_df, width='stretch', hide_index=True)
        else:
            st.info("No card data available.")
    except Exception as e:
        st.error(f"Error generating card analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[4]:
    st.subheader("Fraud by Channel")
    try:
        import plotly.express as px
        channel_df = get_channel_analysis(df_chart)
        if not channel_df.empty:
            fig = px.bar(
                channel_df,
                x="channel",
                y="fraud_rate",
                title="Fraud Rate by Channel",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(channel_df, width='stretch', hide_index=True)
        else:
            st.info("No channel data available.")
    except Exception as e:
        st.error(f"Error generating channel analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[5]:
    st.subheader("Fraud Patterns by Hour of Day")
    try:
        import plotly.express as px
        if "txn_ts" in df_filtered.columns:
            hourly_df = get_hourly_patterns(df_chart)
            if not hourly_df.empty:
                fig = px.line(
                    hourly_df,
                    x="hour",
                    y="fraud_rate",
                    title="Fraud Rate by Hour of Day",
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(hourly_df, width='stretch', hide_index=True)
            else:
                st.info("No timestamp data available for hourly analysis.")
        else:
            st.info("Timestamp column not available for hourly analysis.")
    except Exception as e:
        st.error(f"Error generating hourly patterns: {str(e)}")
        st.info("Please check your data and try again.")

