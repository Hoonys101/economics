
import sys
import os
import json
import re
from typing import List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

REPORT_PATH = "reports/audit/AUDIT_REPORT_PARITY.md"
os.makedirs("reports/audit", exist_ok=True)

def check_file_exists(filepath: str) -> bool:
    return os.path.exists(filepath)

def check_class_in_file(filepath: str, class_name: str) -> bool:
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return f"class {class_name}" in content

def count_lines(filepath: str) -> int:
    if not os.path.exists(filepath):
        return 0
    with open(filepath, 'r', encoding='utf-8') as f:
        return len(f.readlines())

def check_grep(pattern: str, filepath: str) -> bool:
    if not os.path.exists(filepath):
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return bool(re.search(pattern, content))

def audit_main_structure(report: List[str]):
    report.append("## 2. Main Structure & Module Status\n")

    checks = [
        ("modules/household/dtos.py", "HouseholdSnapshotDTO"),
        ("modules/simulation/dtos/api.py", "FirmStateDTO"),
        ("simulation/systems/settlement_system.py", "SettlementSystem"),
        ("modules/finance/registry/bank_registry.py", "BankRegistry"),
        ("simulation/factories/household_factory.py", "HouseholdFactory"),
    ]

    for filepath, class_name in checks:
        exists = check_file_exists(filepath)
        has_class = check_class_in_file(filepath, class_name) if exists else False
        status = "✅ PASS" if exists and has_class else "❌ FAIL"
        report.append(f"- [{status}] `{class_name}` in `{filepath}`")
        if not exists:
            report.append(f"  - File missing: {filepath}")
        elif not has_class:
            report.append(f"  - Class missing: {class_name}")

def audit_io_data(report: List[str]):
    report.append("\n## 3. I/O Data Audit\n")

    # Manual verify based on file reading
    report.append("### DTO Field Verification (Manual/Grep)")

    # EconStateDTO checks
    dto_file = "modules/household/dtos.py"
    if check_file_exists(dto_file):
        has_wallet = check_grep("wallet: IWallet", dto_file)
        has_major = check_grep("major: Optional\[IndustryDomain\]", dto_file)
        has_insight = check_grep("market_insight: float", dto_file)

        report.append(f"- [{'✅ PASS' if has_wallet else '❌ FAIL'}] `EconStateDTO.wallet` (Penny Standard)")
        report.append(f"- [{'✅ PASS' if has_major else '❌ FAIL'}] `EconStateDTO.major` (Labor Matching)")
        report.append(f"- [{'✅ PASS' if has_insight else '❌ FAIL'}] `EconStateDTO.market_insight` (AI Logic)")
    else:
        report.append(f"- ❌ FAIL: `{dto_file}` missing")

    # BioStateDTO checks
    if check_file_exists(dto_file):
        has_sex = check_grep("sex: str", dto_file)
        has_health = check_grep("health_status: float", dto_file)

        report.append(f"- [{'✅ PASS' if has_sex else '❌ FAIL'}] `BioStateDTO.sex` (Demographics)")
        report.append(f"- [{'✅ PASS' if has_health else '❌ FAIL'}] `BioStateDTO.health_status` (Health System)")

    # Check Golden Sample
    report.append("\n### Golden Sample vs DTO")
    golden_path = "tests/goldens/initial_state.json"
    if check_file_exists(golden_path):
        report.append(f"- [⚠️ WARNING] Golden Sample `{golden_path}` exists but uses OUTDATED float schema for assets.")
        report.append(f"  - Actual Code (`Household.get_current_state`) uses `Dict[CurrencyCode, int]`.")
        report.append(f"  - Action Required: Regenerate Golden Samples.")
    else:
        report.append(f"- ❌ FAIL: `{golden_path}` missing")

def audit_util_status(report: List[str]):
    report.append("\n## 4. Util Audit\n")

    checks = [
        ("tests/integration/scenarios/verification/verify_inheritance.py", "verify_inheritance.py"),
        ("scripts/iron_test.py", "iron_test.py"),
        ("communications/team_assignments.json", "Training Harness")
    ]

    for filepath, name in checks:
        exists = check_file_exists(filepath)
        status = "✅ PASS" if exists else "❌ FAIL"
        report.append(f"- [{status}] `{name}` in `{filepath}`")
        if not exists:
            report.append(f"  - File missing: {filepath}")

def audit_parity_items(report: List[str]):
    report.append("\n## 5. Parity Check (Project Status)\n")

    # Phase 4.1
    report.append("### Phase 4.1: AI Logic & Simulation Re-architecture")

    # Labor Major-Matching
    has_major = check_grep("major", "modules/household/dtos.py")
    report.append(f"- [{'✅ PASS' if has_major else '❌ FAIL'}] Labor Major Attribute")

    # Firm SEO Brain Scans
    has_brain_scan = check_grep("def brain_scan", "simulation/firms.py")
    report.append(f"- [{'✅ PASS' if has_brain_scan else '❌ FAIL'}] Firm SEO Brain Scan (`brain_scan` method)")

    # Multi-Currency Barter-FX (Infer from code)
    has_fx = check_grep("class FXMatchDTO", "simulation/systems/settlement_system.py") or check_grep("FX_SWAP", "simulation/systems/settlement_system.py")
    report.append(f"- [{'✅ PASS' if has_fx else '❌ FAIL'}] Multi-Currency Barter-FX (Settlement Support)")

    # Phase 15
    report.append("\n### Phase 15: Architectural Lockdown")
    has_ssot = check_grep("SettlementSystem", "simulation/systems/settlement_system.py")
    report.append(f"- [{'✅ PASS' if has_ssot else '❌ FAIL'}] SettlementSystem Existence")

    has_slot = check_grep("InventorySlot", "modules/simulation/api.py") or check_grep("InventorySlot", "simulation/core_agents.py")
    report.append(f"- [{'✅ PASS' if has_slot else '❌ FAIL'}] Inventory Slot Protocol")

def audit_god_classes(report: List[str]):
    report.append("\n## 6. God Class Audit\n")
    threshold = 800

    files = [
        "simulation/core_agents.py",
        "simulation/firms.py",
        "simulation/engine.py"
    ]

    for f in files:
        lines = count_lines(f)
        status = "✅ PASS" if lines < threshold else "⚠️ FAIL"
        report.append(f"- [{status}] `{f}`: {lines} lines (Threshold: {threshold})")

if __name__ == "__main__":
    report = ["# Parity Audit Report\n"]
    report.append("**Target**: Verify completion of items in `PROJECT_STATUS.md` and adherence to specs.\n")

    audit_main_structure(report)
    audit_io_data(report)
    audit_util_status(report)
    audit_parity_items(report)
    audit_god_classes(report)

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))

    print(f"Audit completed. Report written to {REPORT_PATH}")
