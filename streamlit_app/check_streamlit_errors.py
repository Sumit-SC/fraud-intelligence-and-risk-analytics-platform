"""
Check for common errors in Streamlit app pages.
This script validates imports and catches syntax errors before running Streamlit.

Moved under streamlit_app/, but still checks advanced app modules under app/.
"""

import sys
from pathlib import Path

# Add project root to path (one level above this file)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_syntax(file_path):
    """Check if a Python file has syntax errors."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, file_path, "exec")
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_imports():
    """Check that all modules can be imported."""
    modules_to_check = [
        ("app.data_loader", "load_transaction_data"),
        ("app.utils", "apply_filters"),
        ("app.shared", "get_filtered_data"),
        ("app.risk_scoring", "score_transactions"),
        ("app.analytics", "get_fraud_trends"),
    ]

    errors = []
    for module_name, func_name in modules_to_check:
        try:
            mod = __import__(module_name, fromlist=[func_name])
            if not hasattr(mod, func_name):
                errors.append(f"{module_name}.{func_name} - Function not found")
        except Exception as e:
            errors.append(f"{module_name}.{func_name} - {str(e)}")

    return errors


def check_pages():
    """Check all Streamlit page files."""
    page_files = [
        "app/streamlit_app.py",
        "app/pages/2_🔎_Risk_Explanation.py",
        "app/pages/3_📊_Analytics_Dashboard.py",
        "app/pages/4_📥_Export_Documentation.py",
    ]

    errors = []
    for page_file in page_files:
        file_path = project_root / page_file
        if not file_path.exists():
            errors.append(f"{page_file} - File not found")
            continue

        is_valid, error_msg = check_syntax(file_path)
        if not is_valid:
            errors.append(f"{page_file} - {error_msg}")

    return errors


def main():
    print("=" * 60)
    print("Streamlit App Error Checker")
    print("=" * 60)

    # Check syntax
    print("\n1. Checking page syntax...")
    page_errors = check_pages()
    if page_errors:
        print("❌ Syntax errors found:")
        for error in page_errors:
            print(f"   - {error}")
    else:
        print("✅ All page files have valid syntax")

    # Check imports
    print("\n2. Checking module imports...")
    import_errors = check_imports()
    if import_errors:
        print("❌ Import errors found:")
        for error in import_errors:
            print(f"   - {error}")
    else:
        print("✅ All modules can be imported")

    # Summary
    print("\n" + "=" * 60)
    total_errors = len(page_errors) + len(import_errors)
    if total_errors == 0:
        print("✅ All checks passed! App should run without errors.")
        return 0
    else:
        print(f"❌ Found {total_errors} error(s). Please fix before running Streamlit.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


