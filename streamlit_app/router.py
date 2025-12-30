"""Unified Fraud Analytics App - Mode Router."""

import sys
from pathlib import Path

import streamlit as st


def run() -> None:
    """Entry point for the unified mode router."""
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
        return

    project_root = Path(__file__).parent.parent
    
    try:
        if st.session_state.app_mode == "basic":
            app_viz_path = project_root / "app-vizulation"
            if str(app_viz_path) not in sys.path:
                sys.path.insert(0, str(app_viz_path))
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            import pandas as pd
            import os

            # Check which page to load from session state
            current_page = st.session_state.get("basic_current_page", "main")
            
            if current_page == "dashboard":
                # Load Interactive Dashboard page
                basic_app_file = app_viz_path / "pages" / "1_📊_Interactive_Dashboard.py"
            else:
                # Load main dashboard
                basic_app_file = app_viz_path / "streamlit_app.py"
            
            old_cwd = os.getcwd()
            old_path = sys.path.copy()
            try:
                os.chdir(str(app_viz_path))
                with open(basic_app_file, 'r', encoding='utf-8') as f:
                    app_code = f.read()
                
                exec_globals = {
                    "__file__": str(basic_app_file),
                    "__name__": "__main__",
                    "sys": sys,
                    "Path": Path,
                    "st": st,
                    "pd": pd,
                    "project_root": project_root,
                    "app_dir": app_viz_path,
                }
                exec(app_code, exec_globals)
            finally:
                os.chdir(old_cwd)
                sys.path[:] = old_path

        elif st.session_state.app_mode == "advanced":
            app_path = project_root / "app"
            if str(app_path) not in sys.path:
                sys.path.insert(0, str(app_path))
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            import atexit
            import pandas as pd
            import os

            advanced_app_file = app_path / "streamlit_app.py"
            
            old_cwd = os.getcwd()
            old_path = sys.path.copy()
            try:
                os.chdir(str(app_path))
                with open(advanced_app_file, 'r', encoding='utf-8') as f:
                    app_code = f.read()
                
                exec_globals = {
                    "__file__": str(advanced_app_file),
                    "__name__": "__main__",
                    "sys": sys,
                    "Path": Path,
                    "st": st,
                    "pd": pd,
                    "project_root": project_root,
                    "atexit": atexit,
                }
                exec(app_code, exec_globals)
            finally:
                os.chdir(old_cwd)
                sys.path[:] = old_path

    except Exception as e:
        mode = st.session_state.app_mode or "selected"
        st.error(f"Error loading {mode.capitalize()} Mode: {str(e)}")
        st.exception(e)
        if st.button("🏠 Back to Mode Selector"):
            st.session_state.app_mode = None
            st.rerun()


