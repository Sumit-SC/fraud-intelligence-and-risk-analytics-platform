## Environment Setup

This guide explains how to run the fraud intelligence and risk analytics platform locally in a way that mirrors a production-style analytics stack.

It focuses on:

- **Python environment setup** using either `uv` (recommended) or `pip`.
- **Database (MySQL) setup** for the SQL pipeline.
- **End-to-end run sequence** to populate data and start the applications.
- **Common issues and how to resolve them**.

---

## 1. Repository and Python Environment

### 1.1 Clone the Repository

- Clone the project and move into the root folder:
  - `git clone https://github.com/<your-username>/fraud-intelligence-and-risk-analytics-platform.git`
  - `cd fraud-intelligence-and-risk-analytics-platform`

### 1.2 Using `uv` (recommended)

- **Why `uv`**
  - Fast resolver and installer, good isolation, and simple commands.
  - Captures dependencies via `pyproject.toml` / `uv.lock`.

- **Install `uv`** (see official instructions if not already installed).

- **Create and sync the environment**
  - From the project root: `uv sync`
  - This will create a virtual environment and install all required dependencies.

- **Run commands via `uv`**
  - Example: `uv run python src/generate_raw_data.py`
  - Example: `uv run streamlit run streamlit_app.py`

### 1.3 Using `pip` (alternative)

- **Create a virtual environment**
  - `python -m venv .venv`
  - Activate it using the appropriate command for your OS/shell.

- **Install dependencies**
  - `pip install -r requirements.txt`

- **Run commands**
  - Example: `python src/generate_raw_data.py`
  - Example: `streamlit run streamlit_app.py`

> Pick one approach (`uv` or `pip`) and use it consistently to avoid environment drift.

---

## 2. MySQL Setup

### 2.1 Install and Start MySQL

- Install **MySQL 8+** (local instance or container).
- Ensure the MySQL service is running and that you can connect with a user account that has permission to:
  - Create databases.
  - Create and modify tables.
  - Insert and update data.

### 2.2 Create Database and Raw Tables

- Connect to MySQL using your preferred client (CLI or GUI).
- Run the DDL scripts in `sql/ddl/` in order:
  - Create the database.
  - Create raw transactional and dimension tables.

### 2.3 Configure Connection Settings

- Create a local configuration (e.g., environment variables or a `.env` file) with:
  - Host, port, username, password.
  - Database name (as created by the DDL scripts).

- Ensure the Python scripts under `src/` can read these values (for example via environment variables or a configuration file), so they can connect to MySQL without hard-coded credentials.

> Keep credentials out of version control; this project assumes local, non-production credentials only.

---

## 3. Data Pipeline Run Sequence

Once the environment and database are ready, the typical end-to-end flow is:

1. **Generate synthetic raw data**
   - Use the generator script under `src/` to create realistic transaction and entity CSVs in `data/raw/`.

2. **Load raw data into MySQL**
   - Run the loader script to ingest CSVs into the raw tables defined by the DDL scripts.

3. **Execute the SQL pipeline**
   - Run staging and feature engineering SQL scripts in order (see `sql/README.md` for the recommended sequence).
   - Validate that the final feature tables are populated and consistent.

4. **Export BI-ready data**
   - Use the export script to produce denormalized datasets under `data/bi/` for Power BI and other consumers.

5. **Launch the Streamlit app**
   - Start the unified app (`streamlit_app.py`) to access both Basic and Advanced modes.

This pipeline can be repeated whenever you regenerate data or adjust the SQL logic.

---

## 4. Running the Applications

### 4.1 Streamlit (Unified Entry Point)

- From the project root:
  - With `uv`: `uv run streamlit run streamlit_app.py`
  - With `pip` / plain Python: `streamlit run streamlit_app.py`

- Open the URL shown in the terminal (typically `http://localhost:8501`).
- Choose between **Basic Mode** (visualization-first) and **Advanced Mode** (investigation-focused) via the UI.

### 4.2 Direct Mode Access (Optional)

- Advanced Mode only: run `app/streamlit_app.py` as the main entry point.
- Basic Mode only: run `app-vizulation/streamlit_app.py` as the main entry point.

The unified router is generally preferred for portfolio and interview walkthroughs.

---

## 5. Common Issues and Fixes

### 5.1 Streamlit Cannot Find Modules or Packages

- **Symptom**
  - Import errors for modules in `app/`, `app-vizulation/`, or `src/` when running Streamlit.

- **Checks**
  - Confirm you are running from the **project root** directory.
  - Ensure the environment (virtualenv or `uv` environment) is **activated**.
  - Re-run dependency installation (`uv sync` or `pip install -r requirements.txt`).

### 5.2 MySQL Connection Errors

- **Symptom**
  - Timeouts, authentication errors, or “database does not exist” messages.

- **Checks**
  - Verify the MySQL service is running.
  - Confirm credentials, host, and port are correct.
  - Ensure the database and tables have been created via the DDL scripts.
  - Check that the user has appropriate permissions on the target database.

### 5.3 Empty or Partial Dashboards

- **Symptom**
  - Streamlit or Power BI dashboards show empty tables or charts.

- **Checks**
  - Validate that the **feature tables** have been populated in MySQL.
  - Rerun the SQL staging and feature scripts in the correct order.
  - Confirm the BI export script has created the expected files in `data/bi/`.

### 5.4 Performance or Resource Constraints

- **Symptom**
  - Slow page loads, timeouts, or memory-related errors.

- **Mitigations**
  - Use **smaller data slices** for local testing (e.g., fewer months or limited entities).
  - Prefer the **Basic Mode** Streamlit view on lower-spec machines.
  - Ensure you are not running multiple heavy processes (e.g., notebooks, BI, and app) concurrently on constrained hardware.

---

This setup guide is intentionally high level and environment-agnostic so it can be adapted to different local and cloud setups while preserving the core fraud analytics workflow.


