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

st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

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
        if "txn_date" in df_filtered.columns and "is_fraud" in df_filtered.columns:
            trends_df = get_fraud_trends(df_filtered)
            if not trends_df.empty:
                chart_data = trends_df.set_index("date")[["fraud_count", "non_fraud_count"]]
                st.line_chart(chart_data)
                st.dataframe(trends_df, use_container_width=True, hide_index=True)
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
        geo_df = get_geographic_analysis(df_filtered)
        if not geo_df.empty:
            chart_data = geo_df.set_index("country")["fraud_rate"]
            st.bar_chart(chart_data)
            st.dataframe(geo_df, use_container_width=True, hide_index=True)
        else:
            st.info("No geographic data available.")
    except Exception as e:
        st.error(f"Error generating geographic analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[2]:
    st.subheader("Top Risky Merchants")
    try:
        merchants_df = get_top_risky_merchants(df_filtered, top_n=20)
        if not merchants_df.empty:
            chart_data = merchants_df.set_index("merchant_id")["fraud_count"]
            st.bar_chart(chart_data)
            st.dataframe(merchants_df, use_container_width=True, hide_index=True)
        else:
            st.info("No merchant data available.")
    except Exception as e:
        st.error(f"Error generating merchant analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[3]:
    st.subheader("Top Risky Cards")
    try:
        cards_df = get_top_risky_cards(df_filtered, top_n=20)
        if not cards_df.empty:
            if "card_id" in cards_df.columns:
                chart_data = cards_df.set_index("card_id")["fraud_count"]
                st.bar_chart(chart_data)
            st.dataframe(cards_df, use_container_width=True, hide_index=True)
        else:
            st.info("No card data available.")
    except Exception as e:
        st.error(f"Error generating card analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[4]:
    st.subheader("Fraud by Channel")
    try:
        channel_df = get_channel_analysis(df_filtered)
        if not channel_df.empty:
            chart_data = channel_df.set_index("channel")["fraud_rate"]
            st.bar_chart(chart_data)
            st.dataframe(channel_df, use_container_width=True, hide_index=True)
        else:
            st.info("No channel data available.")
    except Exception as e:
        st.error(f"Error generating channel analysis: {str(e)}")
        st.info("Please check your data and try again.")

with analytics_tabs[5]:
    st.subheader("Fraud Patterns by Hour of Day")
    try:
        if "txn_ts" in df_filtered.columns:
            hourly_df = get_hourly_patterns(df_filtered)
            if not hourly_df.empty:
                chart_data = hourly_df.set_index("hour")["fraud_rate"]
                st.line_chart(chart_data)
                st.dataframe(hourly_df, use_container_width=True, hide_index=True)
            else:
                st.info("No timestamp data available for hourly analysis.")
        else:
            st.info("Timestamp column not available for hourly analysis.")
    except Exception as e:
        st.error(f"Error generating hourly patterns: {str(e)}")
        st.info("Please check your data and try again.")

