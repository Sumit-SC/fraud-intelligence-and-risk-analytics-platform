## Purpose of the Notebooks

The notebooks in this project are designed as **analysis and experimentation workspaces**, not as production code.

They serve three primary purposes:

- **Exploratory analysis** – understanding fraud patterns, distributions, and correlations in the feature space.
- **Model experimentation** – iterating on model choices, feature sets, and thresholds before codifying them in the application.
- **Storytelling and communication** – building visual narratives that can be reused in presentations, interviews, and internal documentation.

---

## Available Notebooks

- **`06_fraud_analytics_storytelling.ipynb`**
  - Focuses on **descriptive analytics** and narrative:
    - How fraud rates evolve over time.
    - Which merchants, channels, and geographies concentrate risk.
    - How velocity and behavioral features behave for fraud vs non-fraud segments.
  - Intended to support **executive storytelling** and stakeholder education rather than low-level feature debugging.

- **`07_model_training_experimentation.ipynb`**
  - Focuses on **model design and evaluation**:
    - Training baseline and ensemble models on the feature tables.
    - Comparing metrics (precision, recall, F1, ROC/AUC) under different configurations.
    - Investigating feature importance and SHAP-derived explanations.
  - Used as a sandbox to test ideas before they are embedded in `app/risk_scoring.py`.

---

## Why Visuals Are Intentionally Limited

The notebooks avoid becoming **full BI dashboards** for a few reasons:

- **Clarity of responsibility**
  - Notebooks are for **analysis and design**, while operational monitoring and reporting are handled by **Power BI** and **Streamlit**.

- **Reproducibility and version control**
  - Keeping visual content focused and purposeful makes it easier to re-run, review, and diff notebooks in Git.

- **Performance and practicality**
  - Heavy dashboards and interactive visualizations are better suited to Streamlit and BI tools, which are optimized for repeated usage and stakeholder access.

The intent is that any visual that graduates from a notebook into repeated use should be migrated into **Power BI** or the **Streamlit app**.

---

## Analysis vs BI Storytelling

It is useful to distinguish between:

- **Analysis (in notebooks)**
  - Objective: answer **“what is happening and why?”** from an analyst’s perspective.
  - Typical outputs:
    - Diagnostic plots and tables.
    - Feature distributions and correlations.
    - Model comparison charts and error analysis.
  - Audience: data scientists, quantitative analysts, and technically-minded risk leads.

- **BI storytelling (in Power BI and Streamlit)**
  - Objective: answer **“what should we do next?”** for decision-makers and operations teams.
  - Typical outputs:
    - KPI dashboards and trend monitoring.
    - Drill-down paths from portfolio view to entity-level detail.
    - Investigation queues and prioritization views.
  - Audience: fraud operations, risk management, and business stakeholders.

Notebooks are where **hypotheses are tested and validated**. Once a hypothesis is robust and business-relevant, it is translated into:

- **SQL features** in `sql/features/`,
- **Models and scores** in `app/risk_scoring.py`, and
- **Dashboards and workflows** in the Streamlit and Power BI layers.

---

## How to Use the Notebooks

- Work through the notebooks **sequentially** when presenting the project:
  - Start with `06_fraud_analytics_storytelling.ipynb` to ground the business problem and patterns.
  - Move to `07_model_training_experimentation.ipynb` to show how those patterns inform the model design.

- Use them as **talking points** in interviews:
  - How you evaluated trade-offs between false positives and false negatives.
  - How you validated that features are both **predictive** and **business-interpretable**.
  - How you converted exploratory work into stable, production-appropriate logic.

Environment setup and Jupyter instructions are covered at a high level in `docs/setup.md`.

---

## Notebook Screenshots

### Fraud Analytics Storytelling

<!-- TODO: Add notebook storytelling screenshot -->
![Fraud Analytics Storytelling](../docs/assets/notebook_storytelling.png)

_Shows: key visualizations from the storytelling notebook including fraud trends, merchant concentration, and velocity patterns._

### Model Training Experimentation

<!-- TODO: Add model training notebook screenshot -->
![Model Training Experimentation](../docs/assets/notebook_model_training.png)

_Shows: model comparison charts, feature importance, SHAP visualizations, and evaluation metrics._


