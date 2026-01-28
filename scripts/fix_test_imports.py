import os
import re

MOVES = {
    "agents": "unit.agents",
    "systems": "unit.systems",
    "finance": "unit.finance",
    "modules": "unit.modules",
    "api": "unit.api",
    "components": "unit.components",
    "utils": "unit.utils",
    "helpers": "unit.helpers",
    "mocks": "unit.mocks",
    "phase21": "scenarios.phase21",
    "phase28": "scenarios.phase28",
    "diagnosis": "scenarios.diagnosis",
    "verification": "scenarios.verification"
}

def fix_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = content
                for old, new in MOVES.items():
                    # Replace "from tests.<old>" with "from tests.<new>"
                    pattern = f"from tests.{old}"
                    replacement = f"from tests.{new}"
                    new_content = new_content.replace(pattern, replacement)

                    # Also handle "import tests.<old>" though less common
                    pattern_import = f"import tests.{old}"
                    replacement_import = f"import tests.{new}"
                    new_content = new_content.replace(pattern_import, replacement_import)

                if new_content != content:
                    print(f"Fixed imports in {filepath}")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)

if __name__ == "__main__":
    fix_imports("tests")
