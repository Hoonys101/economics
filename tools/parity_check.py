import os
import json
import importlib.util
import sys
from typing import Dict, Any

# Add root to sys.path to allow imports
sys.path.append(os.getcwd())

RESULTS = {
    "verified": [],
    "design_drift": [],
    "ghost_implementation": [],
    "data_contract_violation": []
}

def check_file_exists(filepath: str, description: str):
    if os.path.exists(filepath):
        RESULTS["verified"].append(f"{description}: Found at {filepath}")
        return True
    else:
        RESULTS["ghost_implementation"].append(f"{description}: Missing at {filepath}")
        return False

def check_class_location(class_name: str, expected_module: str, actual_module: str):
    try:
        # Check actual module
        spec = importlib.util.find_spec(actual_module)
        if spec is None:
            RESULTS["ghost_implementation"].append(f"{class_name}: Module {actual_module} not found")
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, class_name):
            if expected_module == actual_module:
                RESULTS["verified"].append(f"{class_name}: Found in {actual_module}")
            else:
                RESULTS["design_drift"].append(f"{class_name}: Found in {actual_module}, Expected {expected_module}")
        else:
             # Try to find where it is if not in actual_module (though we passed actual_module as where we think it is)
             RESULTS["ghost_implementation"].append(f"{class_name}: Not found in {actual_module}")

    except Exception as e:
        RESULTS["ghost_implementation"].append(f"{class_name}: Error importing {actual_module}: {e}")

def check_golden_sample(golden_path: str, expected_dto_class: str):
    try:
        with open(golden_path, 'r') as f:
            data = json.load(f)

        # Simple heuristic: Check if keys match DTO fields (mock check for now as we don't load DTO class dynamically easily without env setup)
        # We know Initial State has "households" list with flat structure.
        # AgentStateDTO has "inventories", "assets".

        households = data.get("households", [])
        if not households:
            RESULTS["data_contract_violation"].append(f"{golden_path}: No households found")
            return

        sample = households[0]
        # Check for AgentStateDTO fields
        if "inventories" in sample and "assets" in sample:
             RESULTS["verified"].append(f"{golden_path}: Schema matches AgentStateDTO (approx)")
        elif "inventory" in sample and "needs" in sample:
             RESULTS["data_contract_violation"].append(f"{golden_path}: Schema matches DEPRECATED HouseholdStateDTO, not AgentStateDTO")
        else:
             RESULTS["data_contract_violation"].append(f"{golden_path}: Unknown Schema")

    except Exception as e:
        RESULTS["data_contract_violation"].append(f"{golden_path}: Error reading/parsing: {e}")

if __name__ == "__main__":
    # 1. Phase 24 Checks
    check_class_location("BorrowerProfileDTO", "modules.finance.api", "modules.finance.api")
    # Constants are harder to check via import without running code, skipping for now or assuming grep was enough.

    # 2. Phase 18 Checks
    check_class_location("ISettlementSystem", "modules.finance.api", "modules.finance.api")

    # Drift Checks
    check_class_location("GoodsTransactionHandler", "modules.finance.transaction.handlers.goods_handler", "simulation.systems.handlers.goods_handler")
    check_class_location("LaborTransactionHandler", "modules.finance.transaction.handlers.labor_handler", "simulation.systems.handlers.labor_handler")

    # Phase 14 Checks
    check_class_location("BrandEngine", "modules.firm.engines.brand_engine", "modules.firm.engines.brand_engine")
    check_class_location("PricingEngine", "modules.firm.engines.pricing_engine", "modules.firm.engines.pricing_engine")
    check_class_location("ConsumptionManager", "modules.household.consumption_manager", "modules.household.consumption_manager")

    # Sales Engine Drift
    check_class_location("SalesEngine", "modules.firm.engines.sales_engine", "simulation.components.engines.sales_engine")

    # 3. Data Contract
    check_golden_sample("tests/goldens/initial_state.json", "AgentStateDTO")

    # 4. Utils
    check_file_exists("tests/integration/scenarios/verification/verify_inheritance.py", "Inheritance Verification Script")
    check_file_exists("scripts/iron_test.py", "Iron Test Script")
    check_file_exists("communications/team_assignments.json", "Team Assignments")

    # Output
    print(json.dumps(RESULTS, indent=2))

    os.makedirs("reports/audit", exist_ok=True)
    with open("reports/audit/parity_audit_result.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
