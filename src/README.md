# Pipeline Orchestration (Stages 1–5)

This folder contains executable scripts for generating data, loading to MySQL,
building features, and exporting BI datasets.

## Key Scripts
- `generate_raw_data.py` — Stage 1: create synthetic fraud data
- `load_raw_data.py` — Stage 2: load raw CSVs into MySQL
- `run_stage5a.py` — Stage 5: run advanced pipeline steps
- `export_bi_data.py` — Stage 5: produce BI-ready exports

## Notes
- SQL execution order is documented in `sql/README.md`.
- Validation scripts (`verify_*`, `smoke_test_db.py`) are optional checks.
