"""
Check for common errors in Streamlit app pages.
This script validates imports and catches syntax errors before running Streamlit.

Location: testing/
Run from project root: uv run python testing/check_streamlit_errors.py
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def check_syntax(file_path):
    """Check if a Python file has syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_imports():
    """Check that all modules can be imported."""
    modules_to_check = [
        ("app.data_loader", "load_transaction_data"),
        ("app.utils", "format_currency"),
        ("app.risk_scoring", "score_transactions"),
        ("app-vizulation.data_loader", "load_transaction_data"),
        ("app-vizulation.utils", "format_currency"),
        ("app-vizulation.risk_scoring", "score_transactions"),
    ]
    
    results = []
    for module_name, func_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[func_name])
            getattr(module, func_name)
            results.append((module_name, True, None))
        except ImportError as e:
            results.append((module_name, False, f"Import error: {str(e)}"))
        except AttributeError as e:
            results.append((module_name, False, f"Attribute error: {str(e)}"))
        except Exception as e:
            results.append((module_name, False, f"Error: {str(e)}"))
    
    return results

def main():
    print("=" * 60)
    print("STREAMLIT APP ERROR CHECKER")
    print("=" * 60)
    
    # Check syntax of main app files
    print("\n[1] Checking syntax of main app files...")
    app_files = [
        project_root / "app-vizulation" / "streamlit_app.py",
        project_root / "app-vizulation" / "risk_scoring.py",
        project_root / "app-vizulation" / "data_loader.py",
        project_root / "app-vizulation" / "utils.py",
    ]
    
    for app_file in app_files:
        if app_file.exists():
            is_valid, error = check_syntax(app_file)
            if is_valid:
                print(f"  ✓ {app_file.name}")
            else:
                print(f"  ✗ {app_file.name}: {error}")
        else:
            print(f"  ⚠ {app_file.name}: File not found")
    
    # Check imports
    print("\n[2] Checking module imports...")
    import_results = check_imports()
    for module_name, success, error in import_results:
        if success:
            print(f"  ✓ {module_name}")
        else:
            print(f"  ✗ {module_name}: {error}")
    
    # Check page files
    print("\n[3] Checking page files...")
    pages_dir = project_root / "app-vizulation" / "pages"
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.py"):
            is_valid, error = check_syntax(page_file)
            if is_valid:
                print(f"  ✓ {page_file.name}")
            else:
                print(f"  ✗ {page_file.name}: {error}")
    else:
        print("  ⚠ Pages directory not found")
    
    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

