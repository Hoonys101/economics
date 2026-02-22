import ast
import os
import sys
import re
from collections import defaultdict
from typing import List, Dict, Set, Tuple

# Configuration
GOD_CLASS_THRESHOLD = 800
REPORT_DIR = "reports/audit"
REPORT_FILE = os.path.join(REPORT_DIR, "AUDIT_REPORT_STRUCTURAL.md")
SIMULATION_DIR = "simulation"
MODULES_DIR = "modules"

def ensure_report_dir():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

class GodClassVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.god_classes = []

    def visit_ClassDef(self, node):
        start = node.lineno
        # end_lineno might be None in older python versions, but usually present in 3.8+
        end = getattr(node, 'end_lineno', start)
        lines = end - start + 1
        if lines >= GOD_CLASS_THRESHOLD:
            self.god_classes.append((node.name, lines, self.filename))
        self.generic_visit(node)

class LeakVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.leaks = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'DecisionContext':
            self._check_decision_context(node)
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'DecisionContext':
            self._check_decision_context(node)

        # Check for make_decision calls where self is passed
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'make_decision':
            self._check_make_decision(node)

        self.generic_visit(node)

    def _check_decision_context(self, node):
        # Check arguments for 'self'
        for arg in node.args:
            if isinstance(arg, ast.Name) and arg.id == 'self':
                self.leaks.append((node.lineno, "DecisionContext instantiated with 'self' as positional argument", self.filename))

        # Check keywords for 'self'
        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Name) and keyword.value.id == 'self':
                # Heuristic: if the arg name is 'household' or 'firm' or 'agent'
                if keyword.arg in ['household', 'firm', 'agent', 'state']:
                     self.leaks.append((node.lineno, f"DecisionContext instantiated with 'self' for '{keyword.arg}'", self.filename))

    def _check_make_decision(self, node):
        for arg in node.args:
            if isinstance(arg, ast.Name) and arg.id == 'self':
                 self.leaks.append((node.lineno, "make_decision called with 'self'", self.filename))

def find_god_classes(root_dir) -> List[Tuple[str, int, str]]:
    god_classes = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    visitor = GodClassVisitor(filepath)
                    visitor.visit(tree)
                    god_classes.extend(visitor.god_classes)
                except Exception as e:
                    print(f"Error parsing {filepath}: {e}")
    return god_classes

def find_abstraction_leaks(root_dir) -> List[Tuple[int, str, str]]:
    leaks = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    visitor = LeakVisitor(filepath)
                    visitor.visit(tree)
                    leaks.extend(visitor.leaks)
                except Exception as e:
                    print(f"Error parsing {filepath}: {e}")
    return leaks

def get_imports(filepath):
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass
    return imports

def check_dependencies(root_dir) -> Dict[str, List[str]]:
    violations = defaultdict(list)

    # 1. Check simulation -> tests
    # 2. Check modules/household -> modules/firm
    # 3. Check modules/firm -> modules/household
    # 4. Check simulation/utils -> simulation/agents or simulation/systems

    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            module_path = os.path.relpath(filepath, start=".").replace(os.sep, ".")
            imports = get_imports(filepath)

            for imp in imports:
                if filepath.startswith(os.path.join("simulation")) and "tests" in imp:
                    violations["simulation_imports_tests"].append((filepath, imp))

                if filepath.startswith(os.path.join("modules", "household")) and "modules.firm" in imp:
                    violations["household_imports_firm"].append((filepath, imp))

                if filepath.startswith(os.path.join("modules", "firm")) and "modules.household" in imp:
                    violations["firm_imports_household"].append((filepath, imp))

                if filepath.startswith(os.path.join("simulation", "utils")):
                    if "simulation.agents" in imp or "simulation.systems" in imp:
                        # Exclude simple type checking imports if possible? Hard with static analysis.
                        # But strictly utils shouldn't depend on core systems.
                        violations["utils_imports_core"].append((filepath, imp))

    return violations

def check_sequence() -> List[str]:
    # Heuristic check for TickOrchestrator sequence
    issues = []
    filepath = "simulation/orchestration/tick_orchestrator.py"
    if not os.path.exists(filepath):
        return ["TickOrchestrator file not found."]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract phases list
    # Look for self.phases = [ ... ]
    match = re.search(r"self\.phases: List\[IPhaseStrategy\] = \[(.*?)\]", content, re.DOTALL)
    if not match:
        # Try without type hint
        match = re.search(r"self\.phases = \[(.*?)\]", content, re.DOTALL)

    if match:
        phases_block = match.group(1)
        # Clean up comments and whitespace
        phases = []
        for line in phases_block.split('\n'):
            line = line.split('#')[0].strip()
            if line and ',' in line or 'Phase' in line:
                # Extract phase class name
                phase_match = re.search(r"(Phase\w+)", line)
                if phase_match:
                    phases.append(phase_match.group(1))

        # Expected sequence (roughly)
        # Decisions -> Matching -> Transactions -> Lifecycle

        # Map phases to categories
        categories = {
            "Phase1_Decision": "Decisions",
            "Phase2_Matching": "Matching",
            "Phase3_Transaction": "Transactions",
            "Phase_Consumption": "Lifecycle",
            "Phase_Bankruptcy": "Lifecycle",
            "Phase_Death": "Lifecycle"
        }

        # Check order
        seen_categories = []
        for phase in phases:
            cat = categories.get(phase)
            if cat:
                seen_categories.append(cat)

        # Check for violations
        # We want Decisions < Matching < Transactions

        try:
            dec_idx = seen_categories.index("Decisions")
            mat_idx = seen_categories.index("Matching")
            trans_idx = seen_categories.index("Transactions")

            if not (dec_idx < mat_idx < trans_idx):
                issues.append(f"Sacred Sequence Violation: Order is {seen_categories}")
        except ValueError:
            issues.append(f"Missing Key Phases in Sequence: {seen_categories}")

    else:
        issues.append("Could not parse phases list in TickOrchestrator.")

    return issues

def generate_report(god_classes, leaks, dependency_violations, sequence_issues):
    ensure_report_dir()

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit\n\n")
        f.write("**Generated by**: `tools/structural_audit.py`\n")
        f.write("**Target**: `simulation/`, `modules/`\n\n")

        f.write("## 1. God Classes (> 800 lines)\n")
        if god_classes:
            for name, lines, path in god_classes:
                f.write(f"- **{name}** ({lines} lines): `{path}`\n")
        else:
            f.write("No God Classes found.\n")
        f.write("\n")

        f.write("## 2. Abstraction Leaks (Raw Agent Injection)\n")
        if leaks:
            for lineno, msg, path in leaks:
                f.write(f"- `{path}:{lineno}`: {msg}\n")
        else:
            f.write("No abstraction leaks found.\n")
        f.write("\n")

        f.write("## 3. Dependency Violations\n")
        if any(dependency_violations.values()):
            for category, violations in dependency_violations.items():
                f.write(f"### {category}\n")
                for path, imp in violations:
                    f.write(f"- `{path}` imports `{imp}`\n")
        else:
            f.write("No dependency violations found.\n")
        f.write("\n")

        f.write("## 4. Sequence Verification\n")
        if sequence_issues:
            for issue in sequence_issues:
                f.write(f"- {issue}\n")
        else:
            f.write("Sacred Sequence verified: Decisions -> Matching -> Transactions -> Lifecycle seems correct.\n")
        f.write("\n")

    print(f"Report generated at {REPORT_FILE}")

def main():
    print("Starting Structural Audit...")

    god_classes = find_god_classes(".")
    leaks = find_abstraction_leaks(".")
    dependency_violations = check_dependencies(".")
    sequence_issues = check_sequence()

    generate_report(god_classes, leaks, dependency_violations, sequence_issues)
    print("Audit Complete.")

if __name__ == "__main__":
    main()
