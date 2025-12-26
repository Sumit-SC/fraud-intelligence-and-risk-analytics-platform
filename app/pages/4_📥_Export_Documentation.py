"""
Export & Documentation Page

Download filtered data and view analytics notebook.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.shared import get_filtered_data

st.set_page_config(
    page_title="Export & Documentation",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Export & Documentation")

# Get filtered data (skip scoring for faster load - export doesn't need risk scores)
try:
    with st.spinner("🔄 Loading transactions..."):
        df_full, df_filtered = get_filtered_data(skip_scoring=True)
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

if df_full.empty:
    st.error("⚠️ No transaction data found. Please run `src/export_bi_data.py` first to generate the BI export CSV.")
    st.stop()

# Ensure we have data to work with
st.info(f"📊 Loaded {len(df_full):,} total transactions. {len(df_filtered):,} transactions match current filters.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Export Filtered Data")
    if not df_filtered.empty:
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="fraud_investigation_export.csv",
            mime="text/csv"
        )
        st.caption(f"Export {len(df_filtered):,} filtered transactions")
    else:
        st.info("No data to export. Adjust filters on the main page.")

with col2:
    st.subheader("View Analytics Notebook")
    notebook_path = "notebooks/06_fraud_analytics_storytelling.ipynb"
    
    # Option 1: Link to GitHub (if repo is on GitHub)
    st.markdown("""
    **View on GitHub:**
    - If your repo is on GitHub, you can view the notebook directly
    - GitHub automatically renders Jupyter notebooks
    - Example: `https://github.com/yourusername/repo/blob/main/notebooks/06_fraud_analytics_storytelling.ipynb`
    """)
    
    # Option 2: Link to nbviewer
    st.markdown("""
    **View on nbviewer:**
    - Paste your GitHub notebook URL into [nbviewer.jupyter.org](https://nbviewer.jupyter.org)
    - Works for any public GitHub repository
    """)
    
    # Option 3: Local file info
    notebook_file = Path(notebook_path)
    if notebook_file.exists():
        st.success(f"✅ Notebook found at: `{notebook_path}`")
        st.info("""
        **To view locally:**
        1. Open Jupyter Lab: `uv run jupyter lab`
        2. Navigate to the `notebooks/` folder
        3. Open `06_fraud_analytics_storytelling.ipynb`
        """)
    else:
        st.warning(f"⚠️ Notebook not found at: `{notebook_path}`")

