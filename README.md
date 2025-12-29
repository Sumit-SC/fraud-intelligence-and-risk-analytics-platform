# 🚨 Fraud Intelligence & Risk Analytics Platform

> **A production-ready fraud detection system** that demonstrates end-to-end data engineering, feature engineering, machine learning, and interactive visualization capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)](https://streamlit.io/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Desktop-yellow.svg)](https://powerbi.microsoft.com/)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Architecture & Data Pipeline](#-architecture--data-pipeline)
- [Data Collection & Generation](#-data-collection--generation)
- [Data Cleaning Pipeline](#-data-cleaning-pipeline)
- [Feature Engineering](#-feature-engineering)
- [Machine Learning Models](#-machine-learning-models)
- [Interactive Dashboards](#-interactive-dashboards)
- [Project Structure](#-project-structure)
- [Technologies Used](#-technologies-used)

---

## 🎯 Project Overview

This project showcases a **complete fraud detection analytics platform** built from scratch, demonstrating:

- **Data Engineering**: Synthetic data generation, ETL pipelines, SQL-based transformations
- **Feature Engineering**: Business-relevant fraud signals (velocity, behavioral patterns, merchant risk)
- **Machine Learning**: Ensemble models (Logistic Regression + Random Forest) with SHAP explanations
- **Data Visualization**: Interactive Streamlit dashboards and Power BI reports
- **Production Practices**: Model persistence, caching, error handling, modular architecture

**Perfect for**: Data Analysts, Data Engineers, ML Engineers, and Analytics professionals looking to showcase end-to-end capabilities.

---

## ✨ Key Features

### 🔍 **Fraud Detection & Risk Scoring**
- **Ensemble ML Models**: Logistic Regression + Random Forest for robust risk scoring
- **SHAP Explanations**: Model-agnostic feature importance for interpretability
- **Real-time Scoring**: Fast inference on filtered transaction subsets
- **Risk Bands**: LOW/MEDIUM/HIGH categorization for business users

### 📊 **Interactive Dashboards**
- **Basic Mode**: Fast visualization-focused interface with Plotly charts
- **Advanced Mode**: Full investigation workflow with multi-page analytics
- **Transaction Explorer**: Filter by date, merchant, channel, country, fraud status
- **Risk Explanation**: Detailed SHAP-based explanations for individual transactions
- **Analytics Dashboard**: Trends, geographic analysis, merchant risk, hourly patterns

### 🗄️ **Data Pipeline**
- **Synthetic Data Generation**: Realistic fintech transaction data with fraud patterns
- **SQL ETL Pipeline**: Staging → Enriched → Feature tables
- **BI Export**: Optimized CSV export for dashboard consumption
- **Model Persistence**: Trained models saved for fast inference

### 📈 **Power BI Integration**
- **Executive Dashboards**: High-level fraud metrics and trends
- **Interactive Reports**: Drill-down capabilities for investigation
- **Embedded Viewing**: Power BI dashboards accessible within Streamlit app

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **MySQL 8.0+** (local or remote)
- **uv** package manager ([Install here](https://github.com/astral-sh/uv))

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fraud-intelligence-and-risk-analytics

# Install dependencies
uv sync
```

### Database Setup

1. **Start MySQL** (if running locally)

2. **Create database and tables**:
   ```bash
   mysql -u root -p
   ```
   ```sql
   source sql/ddl/01_create_database.sql
   source sql/ddl/02_create_raw_tables.sql
   source sql/ddl/03_create_raw_dimensions.sql
   ```

3. **Configure environment** (create `.env` file):
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=fraud_db
   ```

### Run the Complete Pipeline

```bash
# 1. Generate synthetic transaction data
uv run python src/generate_raw_data.py

# 2. Load raw data into MySQL
uv run python src/load_raw_data.py

# 3. Run SQL pipeline (in MySQL)
mysql -u root -p fraud_db
source sql/staging/stg_transactions.sql
source sql/staging/stg_transactions_enriched.sql
source sql/features/feat_transactions.sql
source sql/features/feat_transactions_risk.sql

# 4. Export BI-ready data
uv run python src/export_bi_data.py

# 5. Launch Streamlit app
uv run streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

---

## 🏗️ Architecture & Data Pipeline

```
┌─────────────────┐
│  Data Generator │ → Synthetic transaction data (CSV files)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MySQL Loader  │ → Load raw CSVs into MySQL tables
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Pipeline   │ → Staging → Enriched → Features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BI Export     │ → CSV export for dashboards
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Streamlit App   │ → Interactive fraud investigation
└─────────────────┘
```

---

## 📥 Data Collection & Generation

### Synthetic Data Generator

**File**: [`src/generate_raw_data.py`](src/generate_raw_data.py)

Generates realistic fintech transaction data with:
- **Transactions**: 400k+ transactions across 12 months with realistic patterns
- **Fraud Patterns**: Velocity attacks, card testing, high-risk merchants
- **Supporting Data**: Merchants, cards, devices, rule hits, investigator notes

**Key Features**:
- Realistic date distributions and amounts
- Fraud injection based on business rules
- Referential integrity across tables
- Export to CSV format for MySQL ingestion

**Run**:
```bash
uv run python src/generate_raw_data.py
```

**Output**: CSV files in `data/raw/`:
- `transactions/transactions_2024-*.csv` (monthly files)
- `merchants/merchants.csv`
- `cards/cards.csv`
- `devices/devices.csv`
- `rules/rule_hits.csv`
- `investigations/investigator_notes.csv`

---

## 🧹 Data Cleaning Pipeline

### SQL-Based ETL Pipeline

The data cleaning pipeline uses **pure SQL** for maximum performance and maintainability.

#### **Staging Layer**

**File**: [`sql/staging/stg_transactions.sql`](sql/staging/stg_transactions.sql)

- Cleans transaction data
- Standardizes formats (dates, amounts, channels)
- Handles missing values
- Creates `stg_transactions` table

**File**: [`sql/staging/stg_transactions_enriched.sql`](sql/staging/stg_transactions_enriched.sql)

- Joins with merchant, card, device tables
- Adds business context (merchant risk tier, device type)
- Creates `stg_transactions_enriched` table

#### **Feature Engineering**

**File**: [`sql/features/feat_transactions.sql`](sql/features/feat_transactions.sql)

- **Velocity Features**: Transactions per hour/day
- **Behavioral Features**: Amount vs card average
- **Decline Features**: Failed transaction history
- Creates `feat_transactions` table

**File**: [`sql/features/feat_transactions_risk.sql`](sql/features/feat_transactions_risk.sql)

- **Aggregate Risk Features**: Merchant fraud rates, risk tiers
- **Time-Window Features**: 24h, 30d aggregations
- Creates `feat_transactions_risk` table (final feature table)

**Run SQL Pipeline**:
```bash
mysql -u root -p fraud_db
source sql/staging/stg_transactions.sql
source sql/staging/stg_transactions_enriched.sql
source sql/features/feat_transactions.sql
source sql/features/feat_transactions_risk.sql
```

---

## 🎯 Feature Engineering

### Business-Relevant Fraud Signals

The feature engineering focuses on **interpretable fraud signals**:

1. **Transaction Velocity** (`txns_last_24h`)
   - Fraudsters test cards quickly
   - High velocity = suspicious

2. **Decline History** (`declined_txns_last_24h`)
   - Multiple declines indicate card testing
   - Strong fraud indicator

3. **Merchant Risk** (`merchant_fraud_rate_30d`, `is_high_risk_merchant`)
   - Some merchants attract fraud
   - Historical fraud rates matter

4. **Device Type** (`is_emulator_device`)
   - Emulators often used for fraud
   - Mobile app vs web patterns

5. **Amount Deviation** (`amount_vs_card_avg`)
   - Unusual amounts relative to card history
   - Behavioral anomaly detection

**See**: [`sql/features/feat_transactions_risk.sql`](sql/features/feat_transactions_risk.sql) for full SQL implementation

---

## 🤖 Machine Learning Models

### Ensemble Approach

**File**: [`app/risk_scoring.py`](app/risk_scoring.py)

**Models**:
- **Logistic Regression**: Interpretable, fast, coefficient-based explanations
- **Random Forest**: Captures non-linear patterns, feature importance

**Ensemble**: Weighted average (50% LR + 50% RF) for robust predictions

### Model Features

- **Automatic Training**: Trains on first data load with fraud labels
- **Model Persistence**: Saves to `models/` directory (no retraining on filter changes)
- **SHAP Explanations**: Model-agnostic feature importance using SHAP values
- **Risk Bands**: LOW (<30%), MEDIUM (30-60%), HIGH (≥60%)

### Training & Experimentation

**Notebook**: [`notebooks/07_model_training_experimentation.ipynb`](notebooks/07_model_training_experimentation.ipynb)

- Model training workflow
- Hyperparameter exploration
- Evaluation metrics (precision, recall, F1)
- Feature importance analysis
- SHAP value visualization

**Run**:
```bash
uv run jupyter lab
# Open notebooks/07_model_training_experimentation.ipynb
```

---

## 📊 Interactive Dashboards

### Streamlit Application

**Entry Point**: [`streamlit_app.py`](streamlit_app.py)

**Two Modes**:

#### 🚀 **Basic Mode** (Visualization-Focused)
- Fast, lightweight interface
- Interactive Plotly charts
- Simple risk scoring
- PDF viewer & Power BI integration

**Code**: [`app-vizulation/streamlit_app.py`](app-vizulation/streamlit_app.py)

#### 🧠 **Advanced Mode** (Full Investigation)
- Complete transaction overview
- SHAP-based risk explanations
- Multi-page analytics dashboard
- Export & documentation

**Code**: [`app/streamlit_app.py`](app/streamlit_app.py)

### Key Pages

1. **Transaction Overview** ([`app/streamlit_app.py`](app/streamlit_app.py))
   - Filter transactions by date, merchant, channel, country
   - View risk scores and bands
   - Quick risk assessment

2. **Risk Explanation** ([`app/pages/2_🔎_Risk_Explanation.py`](app/pages/2_🔎_Risk_Explanation.py))
   - SHAP-based feature importance
   - Detailed transaction analysis
   - One-liner risk assessments

3. **Analytics Dashboard** ([`app/pages/3_📊_Analytics_Dashboard.py`](app/pages/3_📊_Analytics_Dashboard.py))
   - Fraud trends over time
   - Geographic analysis
   - Top risky merchants & cards
   - Channel & hourly patterns

4. **Interactive Dashboard** ([`app-vizulation/pages/1_📊_Interactive_Dashboard.py`](app-vizulation/pages/1_📊_Interactive_Dashboard.py))
   - Custom Plotly visualizations
   - Dynamic chart builder
   - Pre-defined analytics charts

### Run Streamlit App

```bash
# Unified app (mode selector)
uv run streamlit run streamlit_app.py

# Or run individual modes
uv run streamlit run app/streamlit_app.py          # Advanced Mode
uv run streamlit run app-vizulation/streamlit_app.py  # Basic Mode
```

---

## 📈 Power BI Dashboards

**File**: [`docs/Fraud_Analytics.pbix`](docs/Fraud_Analytics.pbix)

### Dashboard Features

- **Executive Summary**: High-level fraud metrics, trends, KPIs
- **Transaction Analysis**: Detailed transaction exploration
- **Risk Heatmaps**: Geographic and merchant risk visualization
- **Time Series Analysis**: Fraud trends over time
- **Drill-Down Capabilities**: Interactive exploration

### Viewing Power BI Dashboards

1. **Power BI Desktop**:
   ```bash
   # Open docs/Fraud_Analytics.pbix in Power BI Desktop
   ```

2. **Power BI Service** (requires Power BI Pro/PPU):
   - Publish to Power BI Service
   - Embed URL in Streamlit app (Basic Mode → Power BI Integration tab)

3. **Streamlit Integration**:
   - Basic Mode includes Power BI embed viewer
   - Paste Power BI Service URL to view dashboards

---

## 📁 Project Structure

```
fraud-intelligence-and-risk-analytics/
│
├── 📊 streamlit_app.py              # Main entry point (mode selector)
├── 📦 streamlit_app/                 # Streamlit package
│   ├── router.py                     # Mode router logic
│   └── requirements.txt              # Streamlit dependencies
│
├── 🚀 app/                           # Advanced Mode (Full Investigation)
│   ├── streamlit_app.py              # Main app
│   ├── risk_scoring.py               # ML models & scoring
│   ├── data_loader.py                # Data loading utilities
│   ├── analytics.py                  # Analytics functions
│   ├── shared.py                     # Shared utilities
│   └── pages/                        # Multi-page app pages
│       ├── 2_🔎_Risk_Explanation.py
│       ├── 3_📊_Analytics_Dashboard.py
│       └── 4_📥_Export_Documentation.py
│
├── 🎨 app-vizulation/                # Basic Mode (Visualization)
│   ├── streamlit_app.py              # Visualization app
│   ├── risk_scoring.py               # Simple risk scoring
│   ├── data_loader.py                # Data loading
│   └── pages/
│       └── 1_📊_Interactive_Dashboard.py
│
├── 📥 src/                           # Data Pipeline Scripts
│   ├── generate_raw_data.py          # Synthetic data generator
│   ├── load_raw_data.py              # MySQL data loader
│   └── export_bi_data.py            # BI export script
│
├── 🗄️ sql/                           # SQL Pipeline
│   ├── ddl/                          # Database & table creation
│   │   ├── 01_create_database.sql
│   │   ├── 02_create_raw_tables.sql
│   │   └── 03_create_raw_dimensions.sql
│   ├── staging/                      # Data cleaning
│   │   ├── stg_transactions.sql
│   │   └── stg_transactions_enriched.sql
│   └── features/                     # Feature engineering
│       ├── feat_transactions.sql
│       └── feat_transactions_risk.sql
│
├── 📓 notebooks/                     # Jupyter Notebooks
│   ├── 06_fraud_analytics_storytelling.ipynb
│   └── 07_model_training_experimentation.ipynb
│
├── 💾 data/                          # Data Files
│   ├── raw/                          # Generated raw CSVs
│   └── bi/                           # BI export CSV
│
├── 🤖 models/                        # Trained ML Models
│   ├── lr_model.pkl                  # Logistic Regression
│   ├── rf_model.pkl                  # Random Forest
│   ├── scaler.pkl                    # Feature scaler
│   └── model_metadata.pkl            # Model metadata
│
└── 📄 docs/                          # Documentation
    └── Fraud_Analytics.pbix          # Power BI dashboard
```

---

## 🛠️ Technologies Used

### **Data Engineering**
- **Python 3.11+**: Core language
- **Pandas**: Data manipulation
- **MySQL**: Relational database
- **SQL**: ETL pipeline and feature engineering

### **Machine Learning**
- **scikit-learn**: Logistic Regression, Random Forest
- **SHAP**: Model interpretability
- **NumPy**: Numerical computations

### **Visualization**
- **Streamlit**: Interactive web app
- **Plotly**: Interactive charts
- **Power BI**: Business intelligence dashboards

### **Development Tools**
- **uv**: Fast Python package manager
- **Jupyter Lab**: Notebook development
- **Git**: Version control

---

## 📚 Key Code Files

### **Data Pipeline**
- [`src/generate_raw_data.py`](src/generate_raw_data.py) - Synthetic data generation
- [`src/load_raw_data.py`](src/load_raw_data.py) - MySQL data loading
- [`src/export_bi_data.py`](src/export_bi_data.py) - BI export

### **SQL Pipeline**
- [`sql/staging/stg_transactions.sql`](sql/staging/stg_transactions.sql) - Data cleaning
- [`sql/staging/stg_transactions_enriched.sql`](sql/staging/stg_transactions_enriched.sql) - Data enrichment
- [`sql/features/feat_transactions.sql`](sql/features/feat_transactions.sql) - Feature engineering
- [`sql/features/feat_transactions_risk.sql`](sql/features/feat_transactions_risk.sql) - Risk features

### **Machine Learning**
- [`app/risk_scoring.py`](app/risk_scoring.py) - Ensemble models & scoring
- [`notebooks/07_model_training_experimentation.ipynb`](notebooks/07_model_training_experimentation.ipynb) - Model training

### **Dashboards**
- [`streamlit_app.py`](streamlit_app.py) - Main entry point
- [`app/streamlit_app.py`](app/streamlit_app.py) - Advanced Mode
- [`app-vizulation/streamlit_app.py`](app-vizulation/streamlit_app.py) - Basic Mode
- [`docs/Fraud_Analytics.pbix`](docs/Fraud_Analytics.pbix) - Power BI dashboard

---

## 🎓 Learning Outcomes

This project demonstrates:

✅ **End-to-end data engineering** from raw data to insights  
✅ **SQL-based ETL pipelines** for scalable data processing  
✅ **Feature engineering** with business-relevant fraud signals  
✅ **Machine learning** with interpretable models  
✅ **Production practices** (model persistence, caching, error handling)  
✅ **Interactive visualization** with Streamlit and Power BI  
✅ **Modular architecture** for maintainability  

---

## 📝 License

This project is for portfolio/demonstration purposes.

---

**Built with ❤️ for showcasing data engineering, ML, and analytics capabilities**
