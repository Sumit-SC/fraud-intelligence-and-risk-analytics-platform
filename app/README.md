## Purpose of the Streamlit Application

The `app/` directory hosts the **Advanced Mode** Streamlit application: a multi-page fraud investigation console designed to mirror real workflows in fraud and risk operations teams.

Its primary goals are to:

- Provide an **end-to-end view** of a transaction: attributes, history, risk signals, and explanations.
- Help analysts and investigators **prioritize workload** by surfacing the riskiest entities and cases first.
- Offer **transparent, interpretable context** around risk scores to support defensible decisions and auditability.

---

## Target Users

- **Fraud analysts and investigators**
  - Need transaction-level detail, context, and explanations to accept/deny, escalate, or document cases.

- **Risk operations team leads**
  - Monitor queues, understand patterns in escalations, and identify where playbooks or rules need to change.

- **Risk managers and leadership**
  - Want portfolio-level KPIs while retaining the ability to drill into specific segments or cases.

The application is intentionally **opinionated** around these user personas and is not a generic analytics dashboard.

---

## Key Questions the App Helps Answer

- **At portfolio / segment level**
  - Where is fraud **concentrated** (by merchant, channel, geography, device type)?
  - How are **fraud rates and losses trending** over time?
  - Which **rules or patterns** are generating the most high-risk cases?

- **At transaction / entity level**
  - Why was this **transaction or card** scored as high risk?
  - What does its **recent behavior** look like (velocity, declines, amount deviations)?
  - How does this entity compare to both its **own history** and the **portfolio baseline**?

- **From an operational perspective**
  - Which cases should be worked on **first** today?
  - Where can we **reduce manual reviews** without materially increasing risk?
  - Which signals should be fed into **rules engines or upstream controls**?

---

## Page-Level Overview

The Advanced Mode app is organized into discrete pages under `app/pages/`, exposed from the main entrypoint `app/streamlit_app.py`:

- **Transaction Overview (home page)**
  - Central filter panel (date range, merchant, channel, geography, fraud label).
  - Paginated, risk-scored transaction table.
  - High-level KPIs (fraud rate, loss rate, approval metrics).

- **`2_🔎_Risk_Explanation.py` – Risk Explanation**
  - Single-transaction view with risk score, band, and narrative explanation.
  - Feature-level contributions (e.g., velocity, merchant fraud rate, device profile).
  - Designed to answer **“why is this risky?”** in one screen.

- **`3_📊_Analytics_Dashboard.py` – Analytics Dashboard**
  - Aggregated analytics over time, segments, and entities.
  - Focused on trends, concentration, and structural patterns in the fraud portfolio.
  - Supports **strategic decision-making** and hypothesis generation.

- **`4_📥_Export_Documentation.py` – Export & Documentation**
  - Curated exports for external tools (e.g., BI, case management, CSV extracts).
  - Pointers back to key documentation and playbooks.

The navigation is built to reflect how an analyst or lead would move from **portfolio view → case selection → deep dive → export/reporting**.

---

## Application Screenshots

### Transaction Overview Page

<!-- TODO: Add Streamlit transaction overview screenshot -->
![Streamlit Transaction Overview](../docs/assets/streamlit_transaction_overview.png)

_Shows: filter panel, risk-scored transaction table, and portfolio KPIs._

### Risk Explanation Page

<!-- TODO: Add Streamlit risk explanation screenshot -->
![Streamlit Risk Explanation](../docs/assets/streamlit_risk_explanation.png)

_Shows: single-transaction view with SHAP-based feature contributions and risk narrative._

### Analytics Dashboard Page

<!-- TODO: Add Streamlit analytics dashboard screenshot -->
![Streamlit Analytics Dashboard](../docs/assets/streamlit_analytics_dashboard.png)

_Shows: fraud trends, geographic analysis, merchant risk concentration, and hourly patterns._

---

## How to Run the Advanced App Locally

High-level instructions (detailed setup resides in `docs/setup.md`):

- **Prerequisites**
  - Python 3.11+.
  - MySQL 8+ with the schema and feature tables populated (see `sql/README.md`).
  - Dependencies installed via `uv sync` or `pip install -r requirements.txt`.

- **Run via unified entry point (recommended)**
  - `uv run streamlit run streamlit_app.py`
  - Choose **Advanced Mode** from the mode selector in the UI.

- **Run Advanced Mode directly (alternative)**
  - `uv run streamlit run app/streamlit_app.py`
  - This bypasses the mode selector and opens directly into the advanced investigation console.

Once running, adjust filters, inspect high-risk transactions, and navigate between pages to explore how the application supports the investigation lifecycle.

---

## How This App Fits into the Wider Platform

- **Upstream**
  - Relies on the **SQL feature tables** produced by the pipeline outlined in `sql/README.md` and `docs/data_pipeline.md`.
  - Uses the **feature set and labels** defined there to compute risk scores and SHAP-style explanations.

- **Alongside other tools**
  - Complements **Power BI** dashboards by offering a more **operational, case-centric view**.
  - Builds on insights and experiments from `notebooks/`, turning them into repeatable workflows.

- **Downstream**
  - Can be extended to send outputs to **case management systems**, **alert queues**, or **rule engines**, using the same risk signals and explanations exposed in the UI.

This makes the `app/` layer the main **human-in-the-loop decision surface** of the project.


