# Testing Directory

This directory contains test scripts and error checking utilities for the Fraud Intelligence & Risk Analytics project.

## Structure

```
testing/
├── README.md                          # This file
├── check_streamlit_errors.py          # Syntax and import checker for Streamlit apps
└── app-vizulation/                    # Tests for app-vizulation Streamlit app
    ├── test_app.py                    # Main app functionality tests
    ├── test_explanations.py            # Risk explanation tests
    ├── test_shap.py                   # SHAP explanation tests
    └── check_errors.py                # Error checking for app-vizulation
```

## Usage

All scripts should be run from the **project root** directory:

```bash
# Check for errors in Streamlit apps
uv run python testing/check_streamlit_errors.py

# Test app-vizulation functionality
uv run python testing/app-vizulation/test_app.py

# Test risk explanations
uv run python testing/app-vizulation/test_explanations.py

# Test SHAP explanations
uv run python testing/app-vizulation/test_shap.py

# Quick error check for app-vizulation
uv run python testing/app-vizulation/check_errors.py
```

## Purpose

These test files are **not part of the main application**. They are utility scripts for:
- **Development**: Quick error checking during development
- **Debugging**: Isolating issues with imports, data loading, or model training
- **Validation**: Ensuring the app works correctly before deployment

## Main Application Files

The main application files are kept clean and simple:
- `app-vizulation/streamlit_app.py` - Main Streamlit app
- `app-vizulation/risk_scoring.py` - ML-lite risk scoring
- `app-vizulation/data_loader.py` - Data loading utilities
- `app-vizulation/utils.py` - Helper functions
- `app-vizulation/pages/` - Additional Streamlit pages

## Notes

- All test files have updated paths to work from the `testing/` directory
- Tests use small data samples for speed
- These files can be safely ignored when reviewing the main codebase

