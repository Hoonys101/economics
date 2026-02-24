import os
import sys

def check_dirs():
    found_errors = False
    for root, dirs, files in os.walk("."):
        if "__init__.py" in files:
            dirname = os.path.basename(root)
            # Check if directory starts with a digit
            if dirname and dirname[0].isdigit():
                print(f"Error: __init__.py found in numbered directory: {root}")
                found_errors = True

            # Check specific prohibited directories
            if dirname in ["design", "docs", "2_operations"]:
                print(f"Error: __init__.py found in prohibited directory: {root}")
                found_errors = True

    if not found_errors:
        print("Success: No __init__.py found in prohibited directories.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    check_dirs()
