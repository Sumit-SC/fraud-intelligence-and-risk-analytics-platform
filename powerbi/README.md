## Purpose of the Power BI Layer

The Power BI assets in this project translate the underlying fraud analytics pipeline into **executive-ready dashboards** and **operational monitoring views**.

They are designed for:

- **Senior stakeholders** who need a clear view of fraud risk, losses, and trends without interacting with code or notebooks.
- **Risk and fraud leaders** who need to understand where to focus controls, staffing, and playbook improvements.

The core report is delivered as a `.pbix` file under `docs/` to keep the repository clean and GitHub-friendly.

---

## Dataset and Model

- **Source dataset**
  - The primary input is the **feature table and BI export** produced by the SQL pipeline and export scripts.
  - Data is typically exported as a **denormalized CSV** containing:
    - Transaction-level details (amount, time, channel, geography, merchant, device).
    - Fraud labels and related metadata.
    - Aggregated and windowed features (velocity, decline history, merchant risk, etc.).

- **Power BI data model**
  - Built around a **fact table of transactions** with supporting dimensions where appropriate (e.g., date, merchant, geography).
  - Designed to allow:
    - Fast slicing by time, merchant, channel, and geography.
    - Drill-through from portfolio KPIs to transaction-level detail pages.

The export process and structure are described at a high level in `docs/data_pipeline.md`.

---

## KPI Definitions

Power BI surfaces a standard set of **fraud and loss KPIs** typically used in production environments, for example:

- **Fraud Rate**
  - Share of transactions flagged or confirmed as fraud over a period.
  - Can be expressed in **transaction count** or **monetary value** terms.

- **Fraud Loss**
  - Total value of confirmed fraudulent transactions (or chargebacks, where applicable).

- **Attempted vs Realized Fraud**
  - Comparison between **attempted high-risk activity** and **realized financial loss**.

- **False Positive Rate (optional, if labels available)**
  - Proportion of alerts or reviewed cases that were ultimately non-fraud.

- **Merchant / Segment Concentration**
  - Share of fraud volume contributed by the **top N merchants, MCCs, or geographies**.

These KPIs can be refined to mirror the specific definitions used by a given institution; the current implementation is illustrative but aligned with common practice.

---

## Slicers and Drill-Down Logic

The Power BI report is structured to encourage **top-down exploration**:

- **Global slicers**
  - Time period (e.g., month, week, custom date range).
  - Geography (country, region).
  - Channel (e.g., e-commerce, POS, in-app).
  - Merchant and merchant category.
  - Card or customer segments where available.

- **Drill-down paths**
  - From **portfolio overview → segment view → merchant or card view → transaction detail**.
  - From **KPI tiles or charts** into underlying transaction-level data via drill-through pages.

Slicers are intentionally limited to the dimensions that matter most for **risk segmentation and capacity planning**, avoiding dashboard clutter.

---

## Report Layout (Conceptual)

- **Executive Overview page**
  - High-level KPIs (fraud rate, fraud loss, trends).
  - Top contributing segments (merchants, channels, geographies).
  - Time-series trend visuals for quick pattern recognition.

- **Fraud Analytics page**
  - Heatmaps and bar charts for concentration analysis.
  - Velocity and behavioral feature summaries across cohorts.
  - Comparison of fraud vs non-fraud behavior on key dimensions.

- **Entity / Merchant Detail page**
  - Focused view per merchant, MCC, or geography.
  - Summary KPIs, trend charts, and top-risk cards or devices.

- **Transaction Detail page**
  - Table of filtered transactions with key features and labels.
  - Supports deep dives when combined with slicers and drill-through from upstream pages.

## Dashboard Screenshots

### Full Dashboard Overview

<!-- TODO: Add Power BI dashboard screenshot -->
![Power BI Fraud Dashboard](../docs/assets/powerbi_full_dashboard.png)

_Single-page operational overview used by fraud and risk teams._

### Dashboard Preview

![Power BI Fraud Analytics Dashboard](docs/images/powerbi_overview.png)

The dashboard provides an executive-level view of fraud metrics, trends, and high-risk segments with interactive drill-down capabilities.

---

## How to Use the Power BI File

- **Location**
  - The primary report file is stored under `docs/Fraud_Analytics.pbix`.

- **Opening the report**
  - Open the `.pbix` file with **Power BI Desktop**.
  - Refresh the dataset if you have regenerated or modified the BI export.

- **Interactive online dashboard**
  - **View the published report**: [Power BI Playground Dashboard](https://app.powerbi.com/reportEmbed?reportId=31b9f9b4-cda8-4ca2-9412-5cbeb3b3acfb&autoAuth=true&embeddedDemo=true)
  - The dashboard is embedded in Power BI Playground and can be accessed directly via the link above.

- **Embedding in other applications**
  - Use the following iframe code to embed the dashboard in HTML pages, Streamlit apps, or other web applications:
    ```html
    <iframe title="Fraud_Analytics" width="1140" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=31b9f9b4-cda8-4ca2-9412-5cbeb3b3acfb&autoAuth=true&embeddedDemo=true" frameborder="0" allowFullScreen="true"></iframe>
    ```
  - The Streamlit app (Basic Mode) includes a Power BI integration tab where this embed URL can be used.

- **Publishing (optional)**
  - The report is already published to Power BI Service and accessible via the embed link above.
  - For local development, you can open and modify the `.pbix` file in Power BI Desktop and republish if needed.

All report assets are kept in `docs/` to keep the root repository clean while remaining easy to locate for hiring managers and stakeholders reviewing the project.


