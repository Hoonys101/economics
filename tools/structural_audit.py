import ast
import os

def count_lines(node):
    if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
        return 0
    return node.end_lineno - node.lineno + 1

def scan_file(filepath):
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

    # 1. God Classes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            lines = count_lines(node)
            if lines > 800:
                issues.append({
                    'type': 'GOD_CLASS',
                    'file': filepath,
                    'class': node.name,
                    'lines': lines
                })

    # 2. Leaky Abstractions
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check DecisionContext instantiation
            if isinstance(node.func, ast.Name) and node.func.id == 'DecisionContext':
                for keyword in node.keywords:
                    if isinstance(keyword.value, ast.Name) and keyword.value.id == 'self':
                         issues.append({
                            'type': 'LEAKY_ABSTRACTION',
                            'file': filepath,
                            'details': f"DecisionContext instantiated with self in arg '{keyword.arg}'"
                        })
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id == 'self':
                         issues.append({
                            'type': 'LEAKY_ABSTRACTION',
                            'file': filepath,
                            'details': f"DecisionContext instantiated with self as positional arg"
                        })

            # Check make_decision calls
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'make_decision':
                 for arg in node.args:
                     if isinstance(arg, ast.Name) and arg.id == 'self':
                         issues.append({
                            'type': 'LEAKY_ABSTRACTION',
                            'file': filepath,
                            'details': f"make_decision called with self as positional arg"
                        })
                 for keyword in node.keywords:
                     if isinstance(keyword.value, ast.Name) and keyword.value.id == 'self':
                         issues.append({
                            'type': 'LEAKY_ABSTRACTION',
                            'file': filepath,
                            'details': f"make_decision called with self in arg '{keyword.arg}'"
                        })

            # Check for attach(self) pattern (common in component coupling)
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'attach':
                 for arg in node.args:
                     if isinstance(arg, ast.Name) and arg.id == 'self':
                         issues.append({
                            'type': 'LEAKY_ABSTRACTION',
                            'file': filepath,
                            'details': f"Component.attach(self) called - strict decoupling violation"
                        })

            # Check for Engine instantiation with self
            # Heuristic: variable name ending in 'engine' or 'component'
            # This is hard to do perfectly, so we'll look for known patterns from memory if possible.
            # But let's look for assignments to self.something where the call has self as arg.

    # Check assignments: self.engine = Engine(self)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                    # Target is self.field
                    if isinstance(node.value, ast.Call):
                         for arg in node.value.args:
                             if isinstance(arg, ast.Name) and arg.id == 'self':
                                 issues.append({
                                    'type': 'POTENTIAL_LEAK',
                                    'file': filepath,
                                    'details': f"Attribute {target.attr} initialized with self passed as arg"
                                })

    return issues

def main():
    root_dirs = ['modules', 'simulation']
    all_issues = []

    print("Starting Structural Audit...")
    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    issues = scan_file(filepath)
                    all_issues.extend(issues)

    god_classes = [i for i in all_issues if i['type'] == 'GOD_CLASS']
    leaks = [i for i in all_issues if i['type'] == 'LEAKY_ABSTRACTION']
    potential_leaks = [i for i in all_issues if i['type'] == 'POTENTIAL_LEAK']

    print(f"\nFound {len(god_classes)} God Classes (>800 lines):")
    for gc in god_classes:
        print(f"  - {gc['class']} in {gc['file']} ({gc['lines']} lines)")

    print(f"\nFound {len(leaks)} Leaky Abstractions:")
    for leak in leaks:
        print(f"  - {leak['details']} in {leak['file']}")

    print(f"\nFound {len(potential_leaks)} Potential Leaks (Self passed to Constructor):")
    for leak in potential_leaks:
        print(f"  - {leak['details']} in {leak['file']}")

    report_path = 'reports/audit/AUDIT_REPORT_STRUCTURAL.md'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("# AUDIT_REPORT_STRUCTURAL\n\n")
        f.write("## God Classes (>800 lines)\n")
        if god_classes:
            for gc in god_classes:
                f.write(f"- **{gc['class']}** in `{gc['file']}`: {gc['lines']} lines\n")
        else:
            f.write("None found.\n")

        f.write("\n## Leaky Abstractions\n")
        if leaks:
            for leak in leaks:
                f.write(f"- {leak['details']} in `{leak['file']}`\n")
        else:
            f.write("None found.\n")

        f.write("\n## Potential Constructor Leaks\n")
        if potential_leaks:
             for leak in potential_leaks:
                f.write(f"- {leak['details']} in `{leak['file']}`\n")
        else:
             f.write("None found.\n")

if __name__ == "__main__":
    main()
