# 🎨 Basic Mode - Visualization Dashboard

**Lightweight, fast visualization-focused Streamlit app** for quick fraud data exploration.

## Overview

This is the **Basic Mode** of the Fraud Intelligence & Risk Analytics platform - optimized for speed and visual exploration. Perfect for quick data exploration, ad-hoc analysis, and showcasing interactive visualizations.

## Features

- ⚡ **Fast Loading**: Optimized for quick data access
- 📊 **Interactive Charts**: Plotly-based visualizations
- 🎯 **Simple Risk Scoring**: Logistic Regression-based scoring
- 📄 **PDF Viewer**: Upload and view reports
- 🔗 **Power BI Integration**: Embed Power BI dashboards
- 🎨 **Custom Chart Builder**: Create your own visualizations

## Quick Start

```bash
# From project root
uv run streamlit run app-vizulation/streamlit_app.py

# Or use the unified app
uv run streamlit run streamlit_app.py
# Then select "Basic Mode"
```

## Key Components

### Main App
- **File**: [`streamlit_app.py`](streamlit_app.py)
- **Features**: Transaction table, filters, risk scoring, statistics

### Interactive Dashboard Page
- **File**: [`pages/1_📊_Interactive_Dashboard.py`](pages/1_📊_Interactive_Dashboard.py)
- **Features**: 
  - Custom chart builder (Bar, Line, Scatter, Box, Histogram, Violin, Heatmap)
  - Pre-defined analytics charts
  - PDF viewer
  - Power BI embed viewer

### Data Loading
- **File**: [`data_loader.py`](data_loader.py)
- **Function**: Loads BI export CSV (`data/bi/feat_transactions_risk_bi.csv`)

### Risk Scoring
- **File**: [`risk_scoring.py`](risk_scoring.py)
- **Model**: Logistic Regression with SHAP explanations
- **Features**: Transaction velocity, decline history, merchant risk, device type

### Utilities
- **File**: [`utils.py`](utils.py)
- **Functions**: Currency formatting, filter application

## Data Source

Loads from: `data/bi/feat_transactions_risk_bi.csv`

**Generate if missing**:
```bash
uv run python src/export_bi_data.py
```

## Dependencies

See [`streamlit_app/requirements.txt`](../streamlit_app/requirements.txt) for full list.

Core dependencies:
- `streamlit`
- `pandas`
- `plotly`
- `scikit-learn`
- `shap`

## Usage Tips

1. **Quick Exploration**: Use filters in sidebar to narrow down transactions
2. **Custom Charts**: Go to Interactive Dashboard tab → Select chart type → Choose X/Y axes
3. **Power BI**: Upload Power BI Service URL in Power BI Integration tab
4. **PDF Reports**: Upload PDF files in Reports & Presentations tab

## Differences from Advanced Mode

| Feature | Basic Mode | Advanced Mode |
|---------|-----------|---------------|
| Risk Scoring | Logistic Regression | Ensemble (LR + RF) |
| Pages | Single page + Interactive Dashboard | Multi-page (4 pages) |
| Focus | Visualization & exploration | Full investigation workflow |
| Performance | Faster loading | More comprehensive |

## Related Files

- **Main Router**: [`../streamlit_app.py`](../streamlit_app.py)
- **Advanced Mode**: [`../app/streamlit_app.py`](../app/streamlit_app.py)
- **Data Export**: [`../src/export_bi_data.py`](../src/export_bi_data.py)
