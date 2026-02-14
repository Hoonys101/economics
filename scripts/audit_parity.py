import os
import ast
import re
import sys
from pathlib import Path
from datetime import datetime

# Paths
ROOT_DIR = Path(".")
REPORT_DIR = ROOT_DIR / "reports" / "audit"
REPORT_FILE = REPORT_DIR / "AUDIT_REPORT_PARITY.md"

# Ensure report directory exists
os.makedirs(REPORT_DIR, exist_ok=True)

class AuditResult:
    def __init__(self):
        self.passes = []
        self.failures = []
        self.warnings = []

    def log_pass(self, message):
        self.passes.append(message)
        print(f"[PASS] {message}")

    def log_fail(self, message):
        self.failures.append(message)
        print(f"[FAIL] {message}")

    def log_warn(self, message):
        self.warnings.append(message)
        print(f"[WARN] {message}")

    def summary(self):
        return f"""
## Audit Summary
- **PASS**: {len(self.passes)}
- **FAIL**: {len(self.failures)}
- **WARN**: {len(self.warnings)}
"""

def check_file_exists(filepath):
    if not os.path.exists(filepath):
        return False
    return True

def check_content_regex(filepath, regex, description):
    if not check_file_exists(filepath):
        return False, f"File not found: {filepath}"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(regex, content):
        return True, f"Found '{description}' in {filepath}"
    else:
        return False, f"Missing '{description}' in {filepath}"

def check_class_in_file(filepath, class_name):
    if not check_file_exists(filepath):
        return False, f"File not found: {filepath}"

    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True, f"Class '{class_name}' found in {filepath}"

    return False, f"Class '{class_name}' NOT found in {filepath}"

def audit_narrative(audit):
    print("\n--- Auditing Narrative ---")
    # Check for narrative strings in server.py or similar
    # Since these might be in data files or logs, we check widely if not found in specific files

    # Check "Digital Soul"
    found, msg = check_content_regex("PROJECT_STATUS.md", "Digital Soul", "Digital Soul term")
    if found: audit.log_pass(msg)
    else: audit.log_warn(msg)

    # Check "Atomic Value"
    found, msg = check_content_regex("PROJECT_STATUS.md", "Atomic Value", "Atomic Value term")
    if found: audit.log_pass(msg)
    else: audit.log_warn(msg)

    # Check "Invisible Coordination"
    found, msg = check_content_regex("PROJECT_STATUS.md", "Invisible Coordination", "Invisible Coordination term")
    if found: audit.log_pass(msg)
    else: audit.log_warn(msg)

def audit_security(audit):
    print("\n--- Auditing Security ---")
    # Verify X-GOD-MODE-TOKEN
    found, msg = check_content_regex("server.py", "X-GOD-MODE-TOKEN", "X-GOD-MODE-TOKEN header check")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

    found, msg = check_content_regex("server.py", "verify_god_mode_token", "verify_god_mode_token function call")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

def audit_finance(audit):
    print("\n--- Auditing Finance ---")
    # Inspect ISettlementSystem for int types
    filepath = "simulation/finance/api.py"
    found, msg = check_content_regex(filepath, "amount: int", "amount: int in ISettlementSystem")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

def audit_household_engines(audit):
    print("\n--- Auditing Household Engines ---")
    engines = {
        "LifecycleEngine": "modules/household/engines/lifecycle.py",
        "BudgetEngine": "modules/household/engines/budget.py",
        "ConsumptionEngine": "modules/household/engines/consumption_engine.py",
        "NeedsEngine": "modules/household/engines/needs.py"
    }

    for cls, path in engines.items():
        found, msg = check_class_in_file(path, cls)
        if found: audit.log_pass(msg)
        else: audit.log_fail(msg)

def audit_firm_engines(audit):
    print("\n--- Auditing Firm Engines ---")
    engines = {
        "ProductionEngine": "simulation/components/engines/production_engine.py",
        "AssetManagementEngine": "simulation/components/engines/asset_management_engine.py",
        "RDEngine": "simulation/components/engines/rd_engine.py",
        "PricingEngine": "modules/firm/engines/pricing_engine.py",
        "BrandEngine": "modules/firm/engines/brand_engine.py"
    }

    for cls, path in engines.items():
        found, msg = check_class_in_file(path, cls)
        if found: audit.log_pass(msg)
        else: audit.log_fail(msg)

def audit_matching_engine(audit):
    print("\n--- Auditing Matching Engine ---")
    # Verify OrderBookMatchingEngine class
    found, msg = check_class_in_file("simulation/markets/matching_engine.py", "OrderBookMatchingEngine")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

    # Verify usage in OrderBookMarket
    found, msg = check_content_regex("simulation/markets/order_book_market.py", "self.matching_engine = OrderBookMatchingEngine", "Matching Engine instantiation in OrderBookMarket")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

def audit_real_estate(audit):
    print("\n--- Auditing Real Estate ---")
    # Verify RealEstateUtilizationComponent usage in Firm
    found, msg = check_content_regex("simulation/firms.py", "self.real_estate_utilization_component.apply", "RealEstateUtilizationComponent.apply called in Firm")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

    found, msg = check_class_in_file("simulation/components/engines/real_estate_component.py", "RealEstateUtilizationComponent")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

def audit_dto_purity(audit):
    print("\n--- Auditing DTO Purity ---")
    # Check TaxService
    found, msg = check_class_in_file("modules/finance/service.py", "TaxService")
    if found: audit.log_pass(msg)
    else: audit.log_fail(msg)

    # Check if TaxService uses Claim DTO (simple regex check for import or usage)
    found, msg = check_content_regex("modules/finance/service.py", "from modules.common.dtos import Claim", "Claim DTO import in TaxService")
    if found: audit.log_pass(msg)
    else: audit.log_warn(msg)

def main():
    audit = AuditResult()

    print("Starting Parity Audit...")

    audit_narrative(audit)
    audit_security(audit)
    audit_finance(audit)
    audit_household_engines(audit)
    audit_firm_engines(audit)
    audit_matching_engine(audit)
    audit_real_estate(audit)
    audit_dto_purity(audit)

    print("\nAudit Complete.")
    print(audit.summary())

    # Write Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Parity Audit Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(audit.summary() + "\n\n")

        f.write("## Passed Checks\n")
        for msg in audit.passes:
            f.write(f"- [x] {msg}\n")

        f.write("\n## Failed Checks\n")
        for msg in audit.failures:
            f.write(f"- [ ] **FAIL**: {msg}\n")

        f.write("\n## Warnings\n")
        for msg in audit.warnings:
            f.write(f"- [!] {msg}\n")

if __name__ == "__main__":
    main()
