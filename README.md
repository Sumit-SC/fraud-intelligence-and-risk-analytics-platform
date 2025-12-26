# Fraud Intelligence & Risk Analytics Platform

An end-to-end, analytics-first fraud intelligence system that demonstrates how fintech companies ingest messy data, clean it with SQL, derive business-relevant features, perform ML-lite scoring, and deliver insights via Streamlit dashboards.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **MySQL** (local or remote)
- **uv** (Python package manager) - [Install uv](https://github.com/astral-sh/uv)

### Step 1: Install Dependencies

```bash
# Install all dependencies using uv
uv sync
```

### Step 2: Set Up MySQL Database

1. **Start MySQL** (if running locally)

2. **Create the database and tables:**
   ```bash
   # Connect to MySQL
   mysql -u root -p
   
   # Run database creation script
   source sql/ddl/01_create_database.sql
   source sql/ddl/02_create_raw_tables.sql
   ```

3. **Set environment variables** (create `.env` file in project root):
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=fraud_db
   ```

   Or use default password `sanalyst` for local development (if not set).

### Step 3: Generate Raw Data (If Not Already Generated)

```bash
# Generate synthetic transaction data
uv run python src/generate_raw_data.py
```

This creates CSV files in `data/raw/`:
- Transactions (monthly files)
- Merchants
- Cards
- Devices
- Rule hits
- Investigator notes

### Step 4: Load Raw Data into MySQL

```bash
# Load all raw CSV files into MySQL
uv run python src/load_raw_data.py
```

### Step 5: Build SQL Pipeline (Staging → Features)

Run SQL scripts in order:

```bash
# Connect to MySQL
mysql -u root -p fraud_db

# Stage 3: Clean and normalize transactions
source sql/staging/stg_transactions.sql

# Stage 4: Enrich with business context
source sql/staging/stg_transactions_enriched.sql

# Stage 5A: Transaction-level features
source sql/features/feat_transactions.sql

# Stage 5B: Aggregate risk features
source sql/features/feat_transactions_risk.sql
```

### Step 6: Export BI Data

```bash
# Export BI-ready CSV for Streamlit app
uv run python src/export_bi_data.py
```

This creates `data/bi/feat_transactions_risk_bi.csv` (sampled, 300k-500k rows).

### Step 7: Run Streamlit App

```bash
# Start the Streamlit fraud investigation app
uv run streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 📊 App Features

### Main Pages

1. **Transaction Overview** - Filter transactions, view risk scores, quick analysis
2. **Risk Explanation** - Detailed SHAP-based explanations for individual transactions
3. **Analytics Dashboard** - Fraud trends, geographic analysis, merchant risk, etc.
4. **Export & Documentation** - Download filtered data, view analytics notebook

### Key Features

- **Interactive Filters**: Date range, merchant risk tier, channel, country, fraud status
- **ML-lite Risk Scoring**: Ensemble models (Logistic Regression + Random Forest)
- **SHAP Explanations**: Model-agnostic feature importance
- **Model Persistence**: Models saved to `models/` directory (no retraining on filter changes)
- **Quick Analysis**: One-click transaction risk assessment

## 🔧 Development Workflow

### Running Individual Components

```bash
# Generate raw data only
uv run python src/generate_raw_data.py

# Load raw data only
uv run python src/load_raw_data.py

# Export BI data only
uv run python src/export_bi_data.py

# Run Streamlit app
uv run streamlit run app/streamlit_app.py
```

### Jupyter Notebook

```bash
# Start Jupyter Lab
uv run jupyter lab

# Open notebooks/06_fraud_analytics_storytelling.ipynb
```

### Model Management

Models are automatically saved to `models/` directory after first training:
- `lr_model.pkl` - Logistic Regression
- `rf_model.pkl` - Random Forest
- `scaler.pkl` - Feature scaler
- `model_metadata.pkl` - Model metadata

To retrain models:
```python
from app.risk_scoring import retrain_models
import pandas as pd

# Load your data
df = pd.read_csv("data/bi/feat_transactions_risk_bi.csv")

# Force retrain
retrain_models(df, force=True)
```

## 📁 Project Structure

```
fraud-intelligence-and-risk-analytics/
├── app/                    # Streamlit application
│   ├── streamlit_app.py   # Main app entry point
│   ├── risk_scoring.py    # ML-lite scoring logic
│   ├── data_loader.py     # Data loading utilities
│   └── pages/             # Multi-page app pages
├── data/
│   ├── raw/              # Generated raw CSV files
│   └── bi/               # BI-ready export CSV
├── models/                # Saved ML models (.pkl files)
├── notebooks/             # Jupyter notebooks for analysis
├── sql/
│   ├── ddl/              # Database & table creation
│   ├── staging/          # Data cleaning & normalization
│   └── features/         # Feature engineering
└── src/                   # Python scripts
    ├── generate_raw_data.py
    ├── load_raw_data.py
    └── export_bi_data.py
```

## 🎯 Typical Workflow

1. **First Time Setup:**
   ```bash
   uv sync
   # Set up MySQL and .env file
   uv run python src/generate_raw_data.py
   uv run python src/load_raw_data.py
   # Run SQL scripts in MySQL
   uv run python src/export_bi_data.py
   uv run streamlit run app/streamlit_app.py
   ```

2. **Daily Development:**
   ```bash
   # Just run the Streamlit app (data already loaded)
   uv run streamlit run app/streamlit_app.py
   ```

3. **After Data Changes:**
   ```bash
   # Regenerate data
   uv run python src/generate_raw_data.py
   uv run python src/load_raw_data.py
   # Rebuild SQL pipeline
   # Re-export BI data
   uv run python src/export_bi_data.py
   ```

## 🐛 Troubleshooting

### MySQL Connection Issues

- Check MySQL is running: `mysql -u root -p`
- Verify `.env` file has correct credentials
- Default password is `sanalyst` if `MYSQL_PASSWORD` not set

### Models Not Loading

- Delete `models/` directory to force retraining
- Check file permissions on `models/` directory

### Streamlit App Not Loading Data

- Ensure `data/bi/feat_transactions_risk_bi.csv` exists
- Run `uv run python src/export_bi_data.py` if missing

### Port Already in Use

```bash
# Use different port
uv run streamlit run app/streamlit_app.py --server.port 8502
```

## 📝 Notes

- **Model Training**: Models train on first data load, then persist to disk
- **Data Sampling**: BI export samples non-fraud rows to keep dataset manageable (300k-500k rows)
- **Performance**: First load may take 10-30 seconds (model training). Subsequent loads are instant.

## 🎓 Project Stages

This project follows an 8-stage build blueprint:

1. **Data Generation** - Synthetic messy fintech data
2. **Raw Ingestion** - Load into MySQL
3. **Staging Layer** - Clean and normalize
4. **Enriched Staging** - Add business context
5. **Feature Engineering** - Transaction and aggregate features
6. **Analytics Notebook** - Storytelling and insights
7. **BI Export** - Prepare for dashboards
8. **Streamlit App** - Interactive investigation tool

---

**Built for**: Senior Data Analyst, Product Analyst, Decision Scientist, BI/Analytics Engineer portfolios

