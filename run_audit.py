import ast
import os
import glob

def find_god_classes():
    print("Scanning for God Classes (>800 lines)...")
    god_classes = []
    for filepath in glob.glob("**/*.py", recursive=True):
        if "tests/" in filepath or "venv/" in filepath or ".venv/" in filepath:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=filepath)
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        # Approximate line count: end_lineno - lineno
                        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                            lines = node.end_lineno - node.lineno + 1
                            if lines > 800:
                                god_classes.append((filepath, node.name, lines))
        except Exception as e:
            pass
    return god_classes

def find_leaks():
    print("Scanning for raw agent leaks...")
    leaks = []
    # simple text search for 'agents: List[Any]' or 'agents: List[IAgent]' in execute/decision methods
    # also looking for 'context = DecisionContext(household=self' or similar
    import re
    leak_pattern = re.compile(r'def execute\(.*agents:\s*List\[(Any|IAgent)\].*\)')
    leak_pattern2 = re.compile(r'def run_welfare_check\(.*agents:\s*List\[(Any|IAgent)\].*\)')

    for filepath in glob.glob("**/*.py", recursive=True):
        if "tests/" in filepath or "venv/" in filepath or ".venv/" in filepath:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if leak_pattern.search(line) or leak_pattern2.search(line):
                        leaks.append((filepath, i+1, line.strip()))
                    if "DecisionContext(household=self" in line or "DecisionContext(firm=self" in line:
                        leaks.append((filepath, i+1, line.strip()))
        except Exception as e:
            pass
    return leaks

god_classes = find_god_classes()
leaks = find_leaks()

print("God Classes:")
for g in god_classes:
    print(f"{g[0]}: {g[1]} ({g[2]} lines)")

print("Leaks:")
for l in leaks:
    print(f"{l[0]}:{l[1]}: {l[2]}")
