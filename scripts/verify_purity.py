import ast
import os
import sys
import tomllib
from pathlib import Path

# Load Configuration
def load_purity_config():
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            config = data.get("tool", {}).get("purity", {})
            if not config:
                 print("⚠️  Warning: [tool.purity] section not found in pyproject.toml. Using defaults.")
            return config
    except FileNotFoundError:
        print("❌ pyproject.toml not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

config = load_purity_config()

FORBIDDEN_IMPORTS = set(config.get("forbidden_imports", []))
FORBIDDEN_TYPES = set(config.get("forbidden_kernel_types", []))
CHECK_IMPORTS_DIRS = config.get("check_imports_dirs", [])
CHECK_TYPES_DIRS = config.get("check_types_dirs", [])
CHECK_TYPES_FILES = config.get("check_types_files", [])

def get_annotation_names(node):
    """
    Recursively extract names from a type annotation node.
    Returns a set of names found in the annotation.
    """
    names = set()
    if node is None:
        return names

    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, ast.Attribute):
        # handle module.Type
        names.add(node.attr)
    elif isinstance(node, ast.Subscript):
        # handle List[Type], Optional[Type]
        names = names.union(get_annotation_names(node.slice))
    elif isinstance(node, ast.Tuple):
        for elt in node.elts:
            names = names.union(get_annotation_names(elt))
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        # Handle string forward references
        names.add(node.value)
    # Recursion for other complex types could be added.

    return names

def check_file_purity(filepath, check_types=True):
    """
    Checks a single file for Purity violations.
    Returns a list of error strings.
    """
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception as e:
        return [f"Failed to parse {filepath}: {str(e)}"]

    for node in ast.walk(tree):
        # Check 1: Forbidden Imports (Always active for target files)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_IMPORTS:
                    errors.append(f"Line {node.lineno}: Direct import of forbidden module '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_IMPORTS:
                errors.append(f"Line {node.lineno}: Import from forbidden module '{node.module}'")

        # Check 2: Forbidden Types in Function Arguments (Conditional)
        if check_types and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                if arg.annotation:
                    type_names = get_annotation_names(arg.annotation)
                    violations = type_names.intersection(FORBIDDEN_TYPES)
                    if violations:
                        violation_str = ", ".join(violations)
                        errors.append(
                            f"Line {node.lineno}: Function '{node.name}' argument '{arg.arg}' uses forbidden type(s): {violation_str}"
                        )

    return errors

def main():
    print("🛡️  Running Purity Gate v2 (Externalized Rules)...")

    if not FORBIDDEN_IMPORTS and not FORBIDDEN_TYPES:
         print("⚠️  No rules loaded. Skipping checks.")
         sys.exit(0)

    all_violations = {}

    files_to_check_imports = set()
    files_to_check_types = set()

    # 1. Collect Import Check Candidates
    for d in CHECK_IMPORTS_DIRS:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for file in files:
                    if file.endswith(".py"):
                        files_to_check_imports.add(os.path.join(root, file))

    # 2. Collect Type Check Candidates
    for d in CHECK_TYPES_DIRS:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for file in files:
                    if file.endswith(".py"):
                        files_to_check_types.add(os.path.join(root, file))

    for f in CHECK_TYPES_FILES:
        if os.path.exists(f):
            files_to_check_types.add(f)
            files_to_check_imports.add(f) # Ensure these are also checked for imports

    # 3. Process Files
    # Union of all files
    all_files = files_to_check_imports.union(files_to_check_types)

    for filepath in all_files:
        should_check_types = filepath in files_to_check_types
        errors = check_file_purity(filepath, check_types=should_check_types)
        if errors:
            all_violations[filepath] = errors

    # Report
    if all_violations:
        print("\n❌ Purity Violations Found:")
        for filepath, errors in all_violations.items():
            print(f"\n📄 {filepath}:")
            for err in errors:
                print(f"  - {err}")
        print("\n🚫 Verification FAILED. Please fix the violations above.")
        sys.exit(1)
    else:
        print("\n✅ Purity Check Passed: No violations found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
