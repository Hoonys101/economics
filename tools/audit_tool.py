import ast
import os
import sys

def get_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception as e:
        return 0

class AuditVisitor(ast.NodeVisitor):
    def __init__(self, filepath, class_map):
        self.filepath = filepath
        self.class_map = class_map
        self.leaky_make_decision = []
        self.leaky_decision_context = []
        self.classes_found = []

    def visit_ClassDef(self, node):
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)

        self.class_map[node.name] = bases
        self.classes_found.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for make_decision(self, ...)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'make_decision':
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id == 'self':
                    self.leaky_make_decision.append((node.lineno, "make_decision(self)"))

        # Check for DecisionContext(...) with raw agents
        is_decision_context = False
        if isinstance(node.func, ast.Name) and node.func.id == 'DecisionContext':
            is_decision_context = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'DecisionContext':
            is_decision_context = True

        if is_decision_context:
            # Check args and keywords for suspicious values
            suspicious = []
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in ['self', 'agent', 'firm', 'household', 'government']:
                    suspicious.append(arg.id)

            for kw in node.keywords:
                 if isinstance(kw.value, ast.Name) and kw.value.id in ['self', 'agent', 'firm', 'household', 'government']:
                    suspicious.append(f"{kw.arg}={kw.value.id}")

            if suspicious:
                self.leaky_decision_context.append((node.lineno, f"DecisionContext with {suspicious}"))

        self.generic_visit(node)

def calculate_depth(class_name, class_map, cache, visited):
    if class_name in cache:
        return cache[class_name]
    if class_name not in class_map:
        return 0 # External or unknown

    if class_name in visited:
        return 0 # Cycle detected

    visited.add(class_name)

    bases = class_map[class_name]
    if not bases:
        depth = 0
    else:
        depth = 1 + max([calculate_depth(b, class_map, cache, visited) for b in bases], default=-1)

    visited.remove(class_name)
    cache[class_name] = depth
    return depth

def main():
    target_dir = "simulation"
    files_gt_800 = []
    class_map = {} # name -> [bases]
    file_visitors = {} # filepath -> visitor

    # 1. Scan files
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            line_count = get_lines(filepath)

            if line_count > 800:
                files_gt_800.append((filepath, line_count))

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
                visitor = AuditVisitor(filepath, class_map)
                visitor.visit(tree)
                file_visitors[filepath] = visitor
            except Exception as e:
                # print(f"Error parsing {filepath}: {e}")
                pass

    # 2. Calculate Inheritance Depth
    depth_cache = {}
    deep_classes = []

    for name in class_map:
        depth = calculate_depth(name, class_map, depth_cache, set())
        if depth >= 4:
            deep_classes.append((name, depth))

    # 3. Output Results
    with open("audit_results.txt", "w") as out:
        out.write("=== God Classes (> 800 lines) ===\n")
        for f, count in sorted(files_gt_800, key=lambda x: x[1], reverse=True):
            out.write(f"{f}: {count}\n")

        out.write("\n=== Deep Inheritance (>= 4) ===\n")
        for cls, d in sorted(deep_classes, key=lambda x: x[1], reverse=True):
             # Try to find which file defined it
             defined_in = "Unknown"
             for fp, v in file_visitors.items():
                 if cls in v.classes_found:
                     defined_in = fp
                     break
             out.write(f"{cls} (Depth {d}) in {defined_in}\n")

        out.write("\n=== Leaky Abstraction: make_decision(self) ===\n")
        for fp, v in file_visitors.items():
            if v.leaky_make_decision:
                for lineno, msg in v.leaky_make_decision:
                    out.write(f"{fp}:{lineno} - {msg}\n")

        out.write("\n=== Leaky Abstraction: DecisionContext(raw_agent) ===\n")
        for fp, v in file_visitors.items():
            if v.leaky_decision_context:
                for lineno, msg in v.leaky_decision_context:
                    out.write(f"{fp}:{lineno} - {msg}\n")

if __name__ == "__main__":
    main()
