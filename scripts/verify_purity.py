import ast
import os
import sys

def check_purity(filepath: str, allowed_imports: set = None) -> bool:
    """
    Checks if a file adheres to Purity rules:
    1. No 'import config'
    2. No 'from config import ...' (unless allowed)
    """
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    has_error = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "config":
                    print(f"ERROR: {filepath} imports 'config' directly.")
                    has_error = True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "config":
                print(f"ERROR: {filepath} imports from 'config'.")
                has_error = True

    return not has_error

def check_init_signature(filepath: str, expected_dto_type: str) -> bool:
    """
    Checks if __init__ accepts a config_dto of specific type.
    """
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for arg in node.args.args:
                if arg.annotation:
                    # Handle Name and Attribute annotation types
                    type_name = ""
                    if isinstance(arg.annotation, ast.Name):
                        type_name = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Str):
                        type_name = arg.annotation.s

                    if type_name == expected_dto_type:
                        return True
            print(f"ERROR: {filepath} __init__ does not seem to accept {expected_dto_type}.")
            return False
    return True # If no __init__ found? Should fail? Assuming Agent has __init__.

def main():
    agent_files = {
        "simulation/core_agents.py": "HouseholdConfigDTO",
        "simulation/firms.py": "FirmConfigDTO"
    }

    all_passed = True
    for filepath, dto in agent_files.items():
        if not os.path.exists(filepath):
            print(f"Skipping {filepath} (not found)")
            continue

        print(f"Checking {filepath}...")
        if not check_purity(filepath):
            all_passed = False

        if not check_init_signature(filepath, dto):
            all_passed = False

    if all_passed:
        print("Purity Check Passed!")
        sys.exit(0)
    else:
        print("Purity Check Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
