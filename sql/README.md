## SQL Layer Overview

This project is intentionally **SQL-first**: the database is treated as the system of record, and all critical business transformations live in SQL rather than scattered across application code.

The SQL layer is organized into three conceptual tiers:

- **Raw / DDL layer** – database and table definitions for loading source data.
- **Staging layer** – cleaned, standardized, and enriched transactional data.
- **Feature layer** – analytics- and model-ready views that expose fraud signals.

This structure mirrors how production fraud and risk environments are typically managed in financial institutions.

---

## Data Layers

### Raw and DDL

- **Location**: `sql/ddl/`
- **Purpose**:
  - Create the **fraud analytics database** and core raw tables.
  - Define schemas for transactions, cards, devices, merchants, rule hits, and investigator notes.
  - Establish consistent data types and primary/foreign keys that downstream layers rely on.

Raw tables are loaded via Python ingestion scripts (`src/load_raw_data.py`) from CSV exports in `data/raw/`. At this stage, the focus is **faithfully representing source systems**, not applying business rules.

### Staging Layer

- **Location**: `sql/staging/`
- **Key scripts**:
  - `stg_transactions.sql`
  - `stg_transactions_enriched.sql`

- **Purpose**:
  - Clean and normalize transactional data (timestamps, currencies, amounts, channels).
  - Apply basic data quality rules (null handling, outlier clipping where appropriate).
  - Join core transaction facts with **cards, devices, merchants, and rules** to create an enriched, investigation-friendly view.

The staging layer is the bridge between **raw events** and **business logic**. It is where the data becomes reliable enough to support risk decisions, but before heavy feature engineering is applied.

### Feature Layer

- **Location**: `sql/features/`
- **Key scripts**:
  - `feat_transactions.sql`
  - `feat_transactions_risk.sql`
  - `feat_transactions_risk_validation.sql`

- **Purpose**:
  - Compute **business-aligned fraud features**, such as:
    - Velocity windows (transactions per card over 1h / 24h / 30d).
    - Decline and rule-hit history.
    - Merchant-level fraud rates and risk tiers.
    - Behavioral deltas vs historic card behavior (amounts, channels, geography).
  - Assemble a **single feature table** that can be used consistently by:
    - Machine learning models.
    - Streamlit dashboards.
    - Power BI and other BI consumers.

The feature layer is deliberately **denormalized and opinionated**: it encodes the current fraud strategy and risk POV directly in SQL.

---

## Execution Order

In a typical end-to-end run, the SQL scripts are executed in the following logical order **after** raw data has been loaded:

1. **DDL / database creation**
   - Create database and raw tables.
2. **Raw data load**
   - Populate raw tables from CSVs via Python ingestion.
3. **Staging layer**
   - `sql/staging/stg_transactions.sql`
   - `sql/staging/stg_transactions_enriched.sql`
4. **Feature layer**
   - `sql/features/feat_transactions.sql`
   - `sql/features/feat_transactions_risk.sql`
   - `sql/features/feat_transactions_risk_validation.sql` (sanity checks and QA).

> Exact commands and example session notes are documented in `docs/setup.md` and can be adapted for local, containerized, or cloud-hosted MySQL environments.

---

## Business Logic vs Technical Logic

The SQL layer deliberately separates **business logic** from purely **technical transformations**:

- **Business logic (lives in SQL)**:
  - How to define a **“high-risk merchant”** (e.g., fraud rate thresholds over 30 days).
  - How to count **velocity** and **decline history** windows.
  - How to categorize **risk bands** and segments for reporting.
  - How to aggregate risk at **card, device, merchant, and customer** levels.

- **Technical logic (mostly outside SQL)**:
  - Orchestration of job runs and scheduling.
  - Environment configuration (connections, credentials).
  - Application-specific presentation logic in Streamlit.

By encoding the **core risk rules in SQL**, the platform:

- Ensures that data scientists, analysts, and risk managers can **read and audit** the logic directly.
- Makes it easier to **version, review, and test** changes via SQL diffs and pull requests.
- Reduces the risk of logic drifting across multiple codebases (e.g., Python vs BI vs rules engine).

For a narrative description of how the SQL pipeline fits into the full system, see `docs/data_pipeline.md`.


