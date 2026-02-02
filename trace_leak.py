import ast
import os
import sys

def check_file(filepath):
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())

    leaks = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            if node.name == "make_decision":
                # Check for usage of input_dto.markets or similar
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if child.attr == "markets":
                            # This is a potential leak if accessing input_dto.markets
                            leaks.append(f"{filepath}:{child.lineno} Access to .markets attribute found in make_decision")

                    # Also check for "markets.get" if "markets" was unpacked
                    if isinstance(child, ast.Call):
                         if isinstance(child.func, ast.Attribute) and child.func.attr == "get":
                             if isinstance(child.func.value, ast.Name) and child.func.value.id == "markets":
                                 leaks.append(f"{filepath}:{child.lineno} markets.get() call found")

    Visitor().visit(tree)
    return leaks

files_to_check = [
    "simulation/core_agents.py",
    "simulation/firms.py"
]

all_leaks = []
for f in files_to_check:
    if os.path.exists(f):
        all_leaks.extend(check_file(f))
    else:
        print(f"File not found: {f}")

if all_leaks:
    print("Leaks found:")
    for leak in all_leaks:
        print(leak)
    sys.exit(1)
else:
    print("No leaks found.")
    sys.exit(0)
