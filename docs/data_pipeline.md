## End-to-End Data Pipeline (Conceptual Overview)

This document explains the **analytics pipeline** behind the fraud intelligence and risk analytics platform, without diving into code or SQL syntax.

The goal is to show how raw transactional data is transformed into **investigation-ready insights**, highlighting the reasoning behind each stage.

The pipeline can be summarized as:

> Data generation → Raw ingestion → Staging → Feature engineering → BI export → Applications (Streamlit & Power BI)

---

## 1. Data Generation and Raw Ingestion

### 1.1 Synthetic but Realistic Data

The project uses a synthetic data generator to mimic **real payment and fraud behavior**:

- Millions of transactions across multiple months.
- Supporting entities such as cards, devices, merchants, rule hits, and investigator notes.
- Embedded fraud patterns (e.g., high-velocity bursts, high-risk merchants, unusual amounts).

This approach allows us to demonstrate realistic fraud analytics on **non-sensitive data** while preserving patterns that appear in production environments.

### 1.2 Raw Layer in the Database

Raw CSVs are loaded into the database exactly as they come off the generator:

- Minimal transformation at this stage.
- Focus on **faithful reproduction of source systems** (schema and semantics).
- Separate tables for each entity type (transactions, cards, merchants, devices, etc.).

This raw layer gives a **traceable starting point** for all downstream transformations.

---

## 2. Staging: Cleaning and Enrichment

The staging layer is where data becomes **usable and trustworthy** for risk analysis.

### 2.1 Data Cleaning

Key objectives of the staging step:

- Standardize **timestamp formats**, time zones, and date fields.
- Normalize **amounts and currencies** to consistent units.
- Enforce **data types** and basic referential integrity.
- Handle or flag **missing and malformed values**.

The output is a clean, consistent transactional view that is still relatively close to the raw source data.

### 2.2 Business Enrichment

Next, transactions are enriched with contextual information:

- **Merchant attributes** (e.g., category, geography, risk tier).
- **Card and customer attributes** (e.g., product type, tenure where available).
- **Device and channel attributes** (e.g., mobile vs web, emulator flags).
- **Rule and investigation signals** (e.g., rule hits, notes from prior investigations).

This enriched staging view is built to answer questions like **“what do we know about this transaction and its context?”** before we compute advanced features.

---

## 3. Feature Engineering: Fraud Signals

The feature layer transforms enriched data into **explicit fraud signals** that can be used by models, dashboards, and rules engines.

### 3.1 Velocity and Behavioral Features

Examples of features derived at this stage include:

- **Velocity windows**
  - Number and value of transactions over the last hour, day, and month for each card or device.
  - Frequency of declines or rule hits in those windows.

- **Behavioral deviations**
  - Transaction amounts compared to a card’s typical spend.
  - Changes in channel mix (e.g., sudden shift from POS to e-commerce).
  - Time-of-day or day-of-week behavior changes.

These features capture **how behavior changes over time**, which is critical in fraud detection.

### 3.2 Merchant and Segment Risk

The pipeline also computes **aggregate risk statistics**:

- Fraud rates per merchant, merchant category, or geography over rolling windows.
- Identification of **high-risk merchants or segments** based on thresholds.
- Concentration metrics—how much of the fraud is contributed by the top merchants or regions.

This enables the platform to provide both **transaction-level** and **segment-level** perspectives on risk.

### 3.3 Final Feature Tables

All relevant features are assembled into final, denormalized tables that:

- Align with model training and scoring needs.
- Provide a **single source of truth** for BI and analytics needs.

These tables are intentionally designed to be **readable by analysts** (column names and structures reflect business concepts, not just technical fields).

---

## 4. BI Export and Aggregation

Once feature tables are ready, they are exported for **downstream consumption**:

- A consolidated dataset is written out to **BI-friendly files** (e.g., CSV) in `data/bi/`.

The BI export is structured to:

- Support **Power BI dashboards** for executives and managers.
- Allow **ad-hoc analysis** by analysts and data scientists outside of the application.

This export step decouples the **database and feature logic** from the **reporting tools**, which is a common production pattern.

---

## 5. Applications: Streamlit and Power BI

The platform exposes the engineered data and risk signals through two primary application layers.

### 5.1 Streamlit Application

The Streamlit apps (Basic and Advanced modes) are built on top of the feature tables and export logic:

- **Basic Mode**
  - Focused on quick visualization and exploration.
  - Ideal for demos, storytelling, and initial exploration.

- **Advanced Mode**
  - Mimics an analyst’s daily investigation console.
  - Delivers transaction-level detail, risk scores, and explanations.
  - Includes analytics dashboards and export capabilities.

This interactive layer is where **individual analysts and risk operations teams** spend their time.

### 5.2 Power BI Dashboards

Power BI uses the BI export dataset to provide:

- Portfolio-level metrics and trends.
- Drill-down into segments and entities.
- A familiar environment for **senior stakeholders** who already use BI tools.

The combination of Streamlit and Power BI allows the same underlying pipeline to support **both operational and strategic use cases**.

---

## 6. Design Principles and Trade-Offs

Several deliberate design choices shape this pipeline:

- **SQL as the central language**
  - Core definitions of fraud signals and aggregations live in SQL, making them easier for risk and analytics teams to review and govern.

- **Separation of concerns**
  - **Raw / staging / feature / BI** layers are clearly separated to avoid mixing data quality, business logic, and presentation concerns.

- **Explainability over black-box complexity**
  - Features and metrics are kept interpretable so that analysts can connect **model outputs** back to **business intuition**.

- **Synthetic but realistic data**
  - Enables open sharing and portfolio use without compromising real customer data.

These principles make the project suitable not just as a technical demo, but as a **blueprint for how to structure fraud analytics pipelines** in practice.


