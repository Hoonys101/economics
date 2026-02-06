import os
import re

ROOT_DIRS = ["modules", "simulation"]
EXCLUDE_DIRS = ["__pycache__"]
SAFE_PATTERNS = [
    r"self\._inventory",
    r"_econ_state\.inventory",
    r"def inventory\(self\)", # Property definition
    r"@inventory\.setter",
    r"self\.inventory: Dict", # Type hint
    r"self\.inventory =", # Initialization (if any left)
    r"class .*InventoryHandler", # Interface
    r"IInventoryHandler",
    r"_inventory", # If usage is explicitly _inventory, checking for .inventory matches ._inventory too so I need to be careful
]

def audit():
    print("Auditing for legacy .inventory access...")
    violations = []

    for root_dir in ROOT_DIRS:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if not file.endswith(".py"): continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Could not read {filepath}: {e}")
                    continue

                for i, line in enumerate(lines):
                    # Check for .inventory access
                    # We look for ".inventory" literal
                    if ".inventory" in line:
                        # Exclude ._inventory
                        if "._inventory" in line:
                            continue

                        # Exclude checks
                        is_safe = False
                        for pattern in SAFE_PATTERNS:
                            if re.search(pattern, line):
                                is_safe = True
                                break

                        if not is_safe:
                            # Contextual check: Imports often contain .inventory (e.g. from modules.inventory.api)
                            if "import " in line:
                                continue

                            violations.append(f"{filepath}:{i+1}: {line.strip()}")

    if violations:
        print(f"Found {len(violations)} potential violations:")
        for v in violations:
            print(v)
        # We don't exit 1 because we want to see the output and maybe fix them or document them
        # exit(1)
    else:
        print("No violations found!")

if __name__ == "__main__":
    audit()
