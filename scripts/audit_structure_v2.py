import ast
import os
import sys
from typing import List, Dict, Set, Any

TARGET_DIR = "simulation"
GOD_CLASS_LINE_THRESHOLD = 800
INHERITANCE_DEPTH_THRESHOLD = 4
OUTPUT_FILE = "design/gemini_output/audit_raw_output.txt"

class AuditVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.classes = []
        self.leaky_decision_calls = []
        self.leaky_context_inits = []
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        bases = [self._get_base_name(b) for b in node.bases]
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        self.classes.append({
            "name": node.name,
            "lineno": node.lineno,
            "bases": bases,
            "method_count": len(methods)
        })
        self.generic_visit(node)
        self.current_class = None

    def visit_Call(self, node):
        # Check for make_decision(self) calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["make_decision", "make_decisions"]:
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id == "self":
                        self.leaky_decision_calls.append(node.lineno)

        # Check for DecisionContext(..., agent=self, ...)
        if self._is_decision_context_call(node):
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Name) and keyword.value.id == "self":
                     self.leaky_context_inits.append(f"Line {node.lineno}: Arg '{keyword.arg}' = self")

        self.generic_visit(node)

    def _get_base_name(self, base):
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return "Unknown"

    def _is_decision_context_call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "DecisionContext":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "DecisionContext":
            return True
        return False

def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            content = f.read()
            lines = content.splitlines()
            line_count = len(lines)
            tree = ast.parse(content)
        except Exception as e:
            return {"error": str(e), "filepath": filepath}

    visitor = AuditVisitor(filepath)
    visitor.visit(tree)

    return {
        "filepath": filepath,
        "line_count": line_count,
        "classes": visitor.classes,
        "leaky_decision_calls": visitor.leaky_decision_calls,
        "leaky_context_inits": visitor.leaky_context_inits
    }

def calculate_inheritance_depth(class_name: str, class_map: Dict[str, Any], visited: Set[str]) -> int:
    if class_name not in class_map:
        return 0 # Unknown external base class, assume depth 0 added
    if class_name in visited:
        return 0 # Cycle detected

    visited.add(class_name)
    max_depth = 0
    for base in class_map[class_name]["bases"]:
        depth = calculate_inheritance_depth(base, class_map, visited)
        if depth > max_depth:
            max_depth = depth
    visited.remove(class_name)

    return 1 + max_depth

def main():
    results = []
    print(f"Scanning {TARGET_DIR}...")

    # 1. Collect Data
    for root, _, files in os.walk(TARGET_DIR):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                results.append(analyze_file(filepath))

    # 2. Build Class Map for Depth Calculation
    class_map = {}
    for r in results:
        if "classes" in r:
            for cls in r["classes"]:
                class_map[cls["name"]] = cls

    # --- Report Generation ---
    report_lines = []
    report_lines.append("=== STRUCTURAL AUDIT REPORT ===")

    # 3. God Classes (Line Count)
    report_lines.append("\n[God Class Candidates (Lines > 800)]")
    god_classes = [r for r in results if r.get("line_count", 0) > GOD_CLASS_LINE_THRESHOLD]
    if god_classes:
        for r in god_classes:
            report_lines.append(f"  - {r['filepath']}: {r['line_count']} lines")
    else:
        report_lines.append("  None found.")

    # 4. Complexity (Depth & Methods)
    report_lines.append("\n[Class Complexity (Methods > 20 or Depth > 4)]")
    found_complexity = False
    for r in results:
        if "classes" in r:
            for cls in r["classes"]:
                depth = calculate_inheritance_depth(cls["name"], class_map, set())
                # BaseAgent and ILearningAgent are often bases, adding 1 or 2 levels.
                # If depth > 4, it means A -> B -> C -> D -> E

                if depth > INHERITANCE_DEPTH_THRESHOLD or cls["method_count"] > 20:
                    found_complexity = True
                    report_lines.append(f"  - {r['filepath']} :: {cls['name']}")
                    report_lines.append(f"      Methods: {cls['method_count']}")
                    report_lines.append(f"      Inheritance Depth (Internal): {depth} (Bases: {cls['bases']})")

    if not found_complexity:
        report_lines.append("  None found.")

    # 5. Leaky Abstractions
    report_lines.append("\n[Leaky Abstraction: make_decision(self)]")
    leaky_calls = [r for r in results if r.get("leaky_decision_calls")]
    if leaky_calls:
        for r in leaky_calls:
            for lineno in r["leaky_decision_calls"]:
                report_lines.append(f"  - {r['filepath']}:{lineno} passes 'self' to make_decision/make_decisions")
    else:
        report_lines.append("  None found.")

    report_lines.append("\n[Leaky Abstraction: DecisionContext(..., arg=self)]")
    leaky_contexts = [r for r in results if r.get("leaky_context_inits")]
    if leaky_contexts:
        for r in leaky_contexts:
            for msg in r["leaky_context_inits"]:
                report_lines.append(f"  - {r['filepath']} : {msg}")
    else:
        report_lines.append("  None found.")

    # Output
    output_content = "\n".join(report_lines)
    print(output_content)

if __name__ == "__main__":
    main()
