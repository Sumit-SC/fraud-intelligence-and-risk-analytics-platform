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

# Dataset size selector on main page (default 10K) - for charting performance
st.markdown("---")
col_info, col_selector = st.columns([2, 1])
with col_info:
    st.markdown(f"**📊 Filtered Data:** {len(df_filtered):,} transactions")
with col_selector:
    # Dataset size options
    chunk_options = {
        "5K": 5000,
        "10K": 10000,
        "25K": 25000,
        "50K": 50000,
        "100K": 100000,
        "250K": 250000,
        "400K": 400000,
        "All Data": len(df_filtered)
    }
    
    # Filter out options larger than available filtered data
    available_chunks = {k: v for k, v in chunk_options.items() if v <= len(df_filtered)}
    if len(df_filtered) > 400000:
        available_chunks["All Data"] = len(df_filtered)
    elif "All Data" not in available_chunks:
        available_chunks["All Data"] = len(df_filtered)
    
    # Default to 10K (index 1 if available, otherwise first option)
    default_index = 1 if "10K" in available_chunks else 0
    if default_index >= len(available_chunks):
        default_index = 0
    
    selected_chunk_label = st.selectbox(
        "📊 Dataset Size",
        options=list(available_chunks.keys()),
        index=default_index,
        key="analytics_dataset_size",
        help="Select dataset size for charting. Filters are applied first, then sampling."
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
        if "txn_date" in df_chart.columns and "is_fraud" in df_chart.columns:
            trends_df = get_fraud_trends(df_chart)
            if not trends_df.empty:
                chart_data = trends_df.set_index("date")[["fraud_count", "non_fraud_count"]]
                st.line_chart(chart_data)
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
        geo_df = get_geographic_analysis(df_chart)
        if not geo_df.empty:
            chart_data = geo_df.set_index("country")["fraud_rate"]
            st.bar_chart(chart_data)
            st.dataframe(geo_df, width='stretch', hide_index=True)
        else:
            st.info("No geographic data available.")
    except Exception as e:
        st.error(f"Error generating geographic analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[2]:
    st.subheader("Top Risky Merchants")
    try:
        merchants_df = get_top_risky_merchants(df_chart, top_n=20)
        if not merchants_df.empty:
            chart_data = merchants_df.set_index("merchant_id")["fraud_count"]
            st.bar_chart(chart_data)
            st.dataframe(merchants_df, width='stretch', hide_index=True)
        else:
            st.info("No merchant data available.")
    except Exception as e:
        st.error(f"Error generating merchant analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[3]:
    st.subheader("Top Risky Cards")
    try:
        cards_df = get_top_risky_cards(df_chart, top_n=20)
        if not cards_df.empty:
            if "card_id" in cards_df.columns:
                chart_data = cards_df.set_index("card_id")["fraud_count"]
                st.bar_chart(chart_data)
            st.dataframe(cards_df, width='stretch', hide_index=True)
        else:
            st.info("No card data available.")
    except Exception as e:
        st.error(f"Error generating card analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[4]:
    st.subheader("Fraud by Channel")
    try:
        channel_df = get_channel_analysis(df_chart)
        if not channel_df.empty:
            chart_data = channel_df.set_index("channel")["fraud_rate"]
            st.bar_chart(chart_data)
            st.dataframe(channel_df, width='stretch', hide_index=True)
        else:
            st.info("No channel data available.")
    except Exception as e:
        st.error(f"Error generating channel analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[5]:
    st.subheader("Fraud Patterns by Hour of Day")
    try:
        if "txn_ts" in df_filtered.columns:
            hourly_df = get_hourly_patterns(df_chart)
            if not hourly_df.empty:
                chart_data = hourly_df.set_index("hour")["fraud_rate"]
                st.line_chart(chart_data)
                st.dataframe(hourly_df, width='stretch', hide_index=True)
            else:
                st.info("No timestamp data available for hourly analysis.")
        else:
            st.info("Timestamp column not available for hourly analysis.")
    except Exception as e:
        st.error(f"Error generating hourly patterns: {str(e)}")
        st.info("Please check your data and try again.")

