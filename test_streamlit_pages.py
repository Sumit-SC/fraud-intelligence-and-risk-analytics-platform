"""
Quick test script to check for import errors in all Streamlit pages.
Run this to catch errors before starting Streamlit.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all pages can be imported without errors."""
    pages = [
        "app.streamlit_app",
        "app.pages.2_🔎_Risk_Explanation",
        "app.pages.3_📊_Analytics_Dashboard",
        "app.pages.4_📥_Export_Documentation",
    ]
    
    errors = []
    for page in pages:
        try:
            __import__(page)
            print(f"✅ {page} - OK")
        except Exception as e:
            error_msg = f"❌ {page} - ERROR: {str(e)}"
            print(error_msg)
            errors.append((page, str(e)))
    
    if errors:
        print("\n" + "="*60)
        print("IMPORT ERRORS FOUND:")
        print("="*60)
        for page, error in errors:
            print(f"\n{page}:")
            print(f"  {error}")
        return False
    else:
        print("\n✅ All pages imported successfully!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)



