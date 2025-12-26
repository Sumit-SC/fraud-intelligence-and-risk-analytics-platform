# Fraud Investigation & Risk Scoring - Visualization App

**Stage 8A: Clean app skeleton focused on visualization and showcasing the project.**

This is a visualization-focused Streamlit app designed to showcase the Fraud Intelligence & Risk Analytics project. It provides a clean interface for exploring transactions, filtering data, and viewing risk explanations.

## Features

- **App Title**: "Fraud Investigation & Risk Scoring"
- **Sidebar Filters**:
  - Date range (txn_date)
  - Merchant risk tier
  - Channel
  - Country
  - Fraud / Non-fraud toggle
- **Main Section A**: Transaction table with key columns, sorted by risk score
- **Main Section B**: Risk explanation panel for selected transactions

## Project Structure

```
app-vizulation/
├── __init__.py          # Package initialization
├── streamlit_app.py     # Main UI application
├── data_loader.py       # Data loading functions
├── risk_scoring.py      # Placeholder risk scoring logic
├── utils.py             # Helper functions
└── README.md            # This file
```

## Running the App

### Option 1: Run from project root
```bash
streamlit run app-vizulation/streamlit_app.py
```

### Option 2: Run from app-vizulation directory
```bash
cd app-vizulation
streamlit run streamlit_app.py
```

## Prerequisites

1. **Data Export**: Ensure the BI export CSV exists:
   ```bash
   python src/export_bi_data.py
   ```
   This generates `data/bi/feat_transactions_risk_bi.csv`

2. **Dependencies**: Install required packages:
   ```bash
   pip install streamlit pandas scikit-learn numpy
   ```

## Stage 8A vs Stage 8B

### Stage 8A (Completed)
- ✅ Clean app skeleton
- ✅ Layout and filters
- ✅ Placeholder risk scoring (rule-based)
- ✅ Text-based risk explanations
- ✅ Transaction table with sorting
- ✅ Power BI file reference

### Stage 8B (Completed)
- ✅ ML-lite model integration (Logistic Regression)
- ✅ Model coefficient-based explanations
- ✅ Transaction statistics dashboard
- ✅ Filter-responsive statistics
- ✅ Risk band distribution
- ⏳ Power BI screenshot embeddings (optional enhancement)

## Data Source

The app loads data from:
- `data/bi/feat_transactions_risk_bi.csv` (BI export feature table)

## Power BI Integration

The app references the Power BI file:
- `Fraud_Analytics.pbix` (in project root)

**Note**: Power BI files cannot be directly embedded in Streamlit. To view:
1. Open `Fraud_Analytics.pbix` in Power BI Desktop
2. Or publish to Power BI Service and embed using iframe (requires Power BI Pro/PPU)

## Screenshots

**TODO Stage 8B**: Add screenshots of Power BI dashboards to showcase the project.

You can add screenshots using:
```python
st.image("path/to/screenshot.png", caption="Power BI Executive Dashboard")
```

## Technical Notes

- **Risk Scoring**: Uses ML-lite Logistic Regression model for explainable risk ranking.
  - Features: `txns_last_24h`, `declined_txns_last_24h`, `merchant_fraud_rate_30d`, `is_high_risk_merchant`, `is_emulator_device`
  - Model trains automatically on data with fraud labels
  - Coefficients provide interpretable feature importance
- **Risk Bands**: 
  - LOW: <30% probability (likely legitimate)
  - MEDIUM: 30-60% probability (needs review)
  - HIGH: ≥60% probability (strong fraud signal)
- **Statistics**: Transaction statistics update dynamically with filter changes:
  - Fraud counts and percentages
  - Risk band distribution
  - Amount statistics
  - Merchant risk tier breakdown
  - Channel and country breakdowns
- **Performance**: App is optimized for quick loading. Large datasets are handled efficiently with filtering.

## Development

This app is part of the Fraud Intelligence & Risk Analytics project. It complements the Power BI dashboards by providing:
- Interactive transaction exploration
- Risk score explanations
- Investigator-style interface

For full ML implementation, see `notebooks/07_model_training_experimentation.ipynb`.

