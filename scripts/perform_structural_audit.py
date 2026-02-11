import os
import ast
import re
from typing import List, Tuple, Dict

def get_python_files(root_dir: str) -> List[str]:
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        if "tests" in root or "scripts" in root or "migrations" in root or ".venv" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def scan_god_classes(filepaths: List[str], threshold: int = 800) -> List[Tuple[str, str, int]]:
    god_classes = []
    for filepath in filepaths:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

                lines = content.splitlines()

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        start_line = node.lineno
                        # end_lineno is available in Python 3.8+
                        if hasattr(node, "end_lineno") and node.end_lineno:
                            end_line = node.end_lineno
                            line_count = end_line - start_line + 1
                            if line_count > threshold:
                                god_classes.append((filepath, node.name, line_count))
                        else:
                            # Fallback estimation if end_lineno not available (should be in modern python)
                            pass
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
    return god_classes

def scan_abstraction_leaks(filepaths: List[str]) -> List[Tuple[str, int, str]]:
    leaks = []
    for filepath in filepaths:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "DecisionContext":
                            for keyword in node.keywords:
                                if keyword.arg in ["household", "firm"]:
                                    leaks.append((filepath, node.lineno, f"DecisionContext instantiated with raw agent '{keyword.arg}'"))
        except Exception as e:
            pass
    return leaks

def check_sacred_sequence(filepath: str) -> List[str]:
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

            # Simple heuristic: Check order of phases in the list definition
            phases_order = [
                "Phase_Production",
                "Phase1_Decision",
                "Phase2_Matching",
                "Phase3_Transaction",
                "Phase_Consumption" # Late Lifecycle
            ]

            found_phases = []
            for line in content.splitlines():
                for phase in phases_order:
                    if phase in line:
                        found_phases.append(phase)

            # Remove duplicates while preserving order
            seen = set()
            unique_found = []
            for p in found_phases:
                if p not in seen:
                    unique_found.append(p)
                    seen.add(p)

            # Check if order matches expected relative order
            # This is tricky because there are many phases.
            # We just check if Decision comes before Matching, and Matching before Transaction.

            try:
                decision_idx = unique_found.index("Phase1_Decision")
                matching_idx = unique_found.index("Phase2_Matching")
                transaction_idx = unique_found.index("Phase3_Transaction")

                if not (decision_idx < matching_idx < transaction_idx):
                     issues.append(f"Sacred Sequence Violation: Expected Decision -> Matching -> Transaction, found {unique_found}")
            except ValueError:
                # Phases might be missing in the file or named differently
                pass

    except Exception as e:
        issues.append(f"Error checking sequence in {filepath}: {e}")

    return issues

def generate_report(god_classes, leaks, sequence_issues, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Structural Audit Report\n\n")

        f.write("## 1. God Classes (> 800 lines)\n")
        if god_classes:
            for path, name, count in sorted(god_classes, key=lambda x: x[2], reverse=True):
                f.write(f"- **{name}** in `{path}`: {count} lines\n")
        else:
            f.write("No God Classes found.\n")
        f.write("\n")

        f.write("## 2. Abstraction Leaks (DecisionContext)\n")
        if leaks:
            for path, line, msg in leaks:
                f.write(f"- `{path}:{line}`: {msg}\n")
        else:
            f.write("No Abstraction Leaks found in DecisionContext usage.\n")
        f.write("\n")

        f.write("## 3. Sacred Sequence Verification\n")
        if sequence_issues:
            for issue in sequence_issues:
                f.write(f"- {issue}\n")
        else:
            f.write("Sacred Sequence (Decision -> Matching -> Transaction) appears correct in TickOrchestrator.\n")
        f.write("\n")

if __name__ == "__main__":
    root_dir = "."
    files = get_python_files(root_dir)

    print(f"Scanning {len(files)} files...")

    god_classes = scan_god_classes(files)
    leaks = scan_abstraction_leaks(files)

    orchestrator_path = "simulation/orchestration/tick_orchestrator.py"
    sequence_issues = []
    if os.path.exists(orchestrator_path):
        sequence_issues = check_sacred_sequence(orchestrator_path)
    else:
        sequence_issues.append(f"Orchestrator file not found: {orchestrator_path}")

    output_path = "reports/audits/audit_results_raw.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_report(god_classes, leaks, sequence_issues, output_path)
    print(f"Report generated at {output_path}")
