"""Unified Fraud Analytics App - Mode Router."""

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if "app_mode" not in st.session_state:
    st.session_state.app_mode = None

st.session_state["unified_app"] = True

st.set_page_config(
    page_title="Fraud Intelligence & Risk Analytics",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
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

if st.session_state.app_mode is None:
    st.title("🧭 Fraud Intelligence & Risk Analytics")
    st.markdown("### Choose Your Mode")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Basic Mode")
        st.markdown(
            """
        **Visualization & Exploration Dashboard**
        
        - Fast, lightweight interface
        - Interactive Plotly charts
        - Simple risk scoring
        - PDF viewer & Power BI integration
        - Perfect for quick exploration
        """
        )
        if st.button("🚀 Launch Basic Mode", type="primary"):
            st.session_state.app_mode = "basic"
            st.rerun()

    with col2:
        st.markdown("### 🧠 Advanced Mode")
        st.markdown(
            """
        **Full Investigation Workflow**
        
        - Complete transaction overview
        - SHAP-based risk explanations
        - Multi-page analytics dashboard
        - Export & documentation
        - Ensemble ML models
        - Perfect for deep analysis
        """
        )
        if st.button("🧠 Launch Advanced Mode", type="primary"):
            st.session_state.app_mode = "advanced"
            st.rerun()

    st.markdown("---")
    st.info("💡 **Tip**: You can switch between modes anytime using the sidebar buttons.")


elif st.session_state.app_mode == "basic":
    try:
        app_viz_path = project_root / "app-vizulation"
        if str(app_viz_path) not in sys.path:
            sys.path.insert(0, str(app_viz_path))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        import importlib.util
        import pandas as pd

        basic_app_file = app_viz_path / "streamlit_app.py"
        spec = importlib.util.spec_from_file_location("basic_app", basic_app_file)
        basic_app_module = importlib.util.module_from_spec(spec)

        basic_app_module.__dict__.update(
            {
                "sys": sys,
                "Path": Path,
                "st": st,
                "pd": pd,
                "project_root": project_root,
                "app_dir": app_viz_path,
            }
        )

        spec.loader.exec_module(basic_app_module)

    except Exception as e:
        st.error(f"Error loading Basic Mode: {str(e)}")
        st.exception(e)
        if st.button("🏠 Back to Mode Selector"):
            st.session_state.app_mode = None
            st.rerun()


elif st.session_state.app_mode == "advanced":
    try:
        app_path = project_root / "app"
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        import importlib.util
        import atexit
        import pandas as pd

        advanced_app_file = app_path / "streamlit_app.py"
        spec = importlib.util.spec_from_file_location("advanced_app", advanced_app_file)
        advanced_app_module = importlib.util.module_from_spec(spec)

        advanced_app_module.__dict__.update(
            {
                "sys": sys,
                "Path": Path,
                "st": st,
                "pd": pd,
                "project_root": project_root,
                "atexit": atexit,
            }
        )

        spec.loader.exec_module(advanced_app_module)

    except Exception as e:
        st.error(f"Error loading Advanced Mode: {str(e)}")
        st.exception(e)
        if st.button("🏠 Back to Mode Selector"):
            st.session_state.app_mode = None
            st.rerun()


