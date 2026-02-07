import os
import ast
import sys

def get_line_count(node):
    return node.end_lineno - node.lineno + 1

def is_god_class(node):
    return get_line_count(node) > 800

def is_near_miss(node):
    return 600 < get_line_count(node) <= 800

LEAKY_TYPES = {'BaseAgent', 'Household', 'Firm', 'Government', 'Bank'}
LEAKY_VAR_NAMES = {'agent', 'household', 'firm', 'government', 'bank'}

def check_abstraction_leaks(node, filepath):
    leaks = []
    if isinstance(node, ast.FunctionDef):
        for arg in node.args.args:
            # Check annotation
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    if arg.annotation.id in LEAKY_TYPES:
                        leaks.append(f"Argument '{arg.arg}' has leaky type '{arg.annotation.id}' in function '{node.name}'")
                elif isinstance(arg.annotation, ast.Constant) and isinstance(arg.annotation.value, str):
                     if arg.annotation.value in LEAKY_TYPES:
                        leaks.append(f"Argument '{arg.arg}' has leaky type '{arg.annotation.value}' in function '{node.name}'")

            # Check argument name (heuristic)
            if arg.arg in LEAKY_VAR_NAMES and arg.arg != 'self':
                 safe = False
                 if arg.annotation:
                     if isinstance(arg.annotation, ast.Name) and ("DTO" in arg.annotation.id or "Context" in arg.annotation.id):
                         safe = True
                     if isinstance(arg.annotation, ast.Constant) and isinstance(arg.annotation.value, str) and ("DTO" in arg.annotation.value or "Context" in arg.annotation.value):
                         safe = True

                 if not safe:
                     leaks.append(f"Argument '{arg.arg}' might be a raw agent (name match) in function '{node.name}'")

    return leaks

def check_imports(tree, filepath):
    leaks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and ("simulation.agents" in node.module or "simulation.models.agents" in node.module):
                 leaks.append(f"Importing raw agents from {node.module}")
    return leaks

def audit_file(filepath):
    god_classes = []
    near_misses = []
    leaks = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return [], [], []

    # Check imports for leaks in engines
    if "engine" in filepath.lower() or "decision" in filepath.lower():
        import_leaks = check_imports(tree, filepath)
        leaks.extend(import_leaks)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            lc = get_line_count(node)
            if is_god_class(node):
                god_classes.append((node.name, lc))
            elif is_near_miss(node):
                near_misses.append((node.name, lc))

        # Check leaks only in engines
        if "engine" in filepath.lower() or "decision" in filepath.lower():
            leak_findings = check_abstraction_leaks(node, filepath)
            for leak in leak_findings:
                leaks.append(leak)

    return god_classes, near_misses, leaks

def main():
    root_dirs = ['simulation', 'modules']

    all_god_classes = []
    all_near_misses = []
    all_leaks = []

    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    g, n, l = audit_file(filepath)
                    if g:
                        for name, lines in g:
                            all_god_classes.append(f"{filepath} :: {name} ({lines} lines)")
                    if n:
                        for name, lines in n:
                            all_near_misses.append(f"{filepath} :: {name} ({lines} lines)")
                    if l:
                        for leak in l:
                            all_leaks.append(f"{filepath} :: {leak}")

    print("=== GOD CLASS AUDIT (> 800 lines) ===")
    if all_god_classes:
        for item in all_god_classes:
            print(item)
    else:
        print("No God Classes found.")

    print("\n=== NEAR MISSES (600-800 lines) ===")
    if all_near_misses:
        for item in all_near_misses:
            print(item)
    else:
        print("No Near Misses found.")

    print("\n=== ABSTRACTION LEAK AUDIT (Engines) ===")
    if all_leaks:
        for item in all_leaks:
            print(item)
    else:
        print("No Abstraction Leaks found.")

if __name__ == "__main__":
    main()
