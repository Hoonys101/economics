import sys
import os
from pathlib import Path
import logging

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Set Env Var for ConfigManager BEFORE importing main or creating simulation
# ConfigManager typically supports SIMULATION__ACTIVE_SCENARIO -> simulation.active_scenario
os.environ["SIMULATION__ACTIVE_SCENARIO"] = "phase29_depression"

from main import create_simulation
import config

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase29Verifier")

def verify_phase29():
    print(">>> Setting up Phase 29 Depression Verification...")

    # Overrides to isolate Interest Expense and accelerate verification
    overrides = {
        "SIMULATION_TICKS": 25,
        "INITIAL_FIRM_CAPITAL_MEAN": 50000.0,
        "FIRM_MAINTENANCE_FEE": 0.0, # Disable maintenance to isolate interest expense
        "TICKS_PER_YEAR": 100.0,
        "CORPORATE_TAX_RATE": 0.0, # Disable tax to simplify expense check
    }

    sim = create_simulation(overrides=overrides)

    # Check if scenario loaded
    if not sim.stress_scenario_config.is_active:
        print("❌ Scenario NOT Active! Check ConfigManager.")
        # Force it if env var failed
        sim.stress_scenario_config.is_active = True
        sim.stress_scenario_config.scenario_name = "phase29_depression"
        sim.stress_scenario_config.start_tick = 5
        sim.stress_scenario_config.base_interest_rate_multiplier = 3.0
        sim.stress_scenario_config.corporate_tax_rate_delta = 0.1
        sim.stress_scenario_config.demand_shock_multiplier = 0.7
        print("⚠️ Forced Scenario Activation manually.")
    else:
        print(f"✅ Scenario Loaded: {sim.stress_scenario_config.scenario_name}")

    # Inject Debt to a specific firm for precise Interest Verification
    test_firm = sim.firms[0]
    loan_amount = 20000.0
    loan_duration = 100

    print(f">>> Injecting Loan of {loan_amount} to Firm {test_firm.id}...")
    if sim.bank:
        sim.bank.grant_loan(test_firm.id, loan_amount, loan_duration)
    else:
        print("❌ Bank system missing! Cannot verify interest.")
        return

    # Ensure firm has no employees to avoid wage expenses
    # (Assuming we can clear them or they are not hired yet if we didn't run ticks?
    # create_simulation hires people. We need to fire them.)
    test_firm.hr.employees = []
    test_firm.hr.employee_wages = {}
    test_firm.inventory = {} # Clear inventory to avoid holding costs
    test_firm.productivity_factor = 0.0 # Disable production to minimize inventory noise

    # 5. Run for 20 ticks
    print(">>> Running Simulation for 20 ticks...")
    initial_interest_rate = sim.bank.base_rate
    print(f"Initial Interest Rate: {initial_interest_rate}")

    scenario_active_tick = sim.stress_scenario_config.start_tick

    # Track metrics
    interest_rate_increased = False
    max_rate = initial_interest_rate
    interest_expense_verified = False

    for i in range(1, 21):
        sim.run_tick()
        current_tick = sim.time

        # Check Interest Rate Change
        if sim.bank.base_rate > max_rate:
             max_rate = sim.bank.base_rate
             interest_rate_increased = True
             print(f"Tick {current_tick}: Interest Rate Increased to {max_rate}")

        # Verify Interest Expense on Test Firm
        # Interest = Principal * Rate / Ticks_Per_Year
        # Ticks Per Year = 100
        # Rate changes from 0.05 to 0.15

        # After shock (Tick 5+), Rate should be ~0.15
        if current_tick > scenario_active_tick + 2: # Give it a moment to stabilize
            expected_rate = initial_interest_rate * 3.0 # 0.15
            expected_interest = loan_amount * expected_rate / 100.0 # 20000 * 0.15 / 100 = 30.0

            actual_expenses = test_firm.finance.expenses_this_tick

            # Check if Interest is accounted for (Expenses >= Interest)
            # We allow a small margin for float error
            if actual_expenses >= expected_interest - 0.1:
                 if not interest_expense_verified:
                     print(f"✅ Verified Interest Expense Accounting: Actual {actual_expenses:.2f} >= Expected Interest {expected_interest:.2f}")
                     interest_expense_verified = True
            else:
                if not interest_expense_verified:
                    print(f"Tick {current_tick}: Expense Missing? Actual: {actual_expenses}, Expected Interest: {expected_interest}")


    # 6. Verification Report
    print("\n>>> Final Verification Report")

    # 1. Verify Interest Rate
    if interest_rate_increased and max_rate >= initial_interest_rate * 2.9:
        print(f"✅ Interest Rate Multiplier Applied: {max_rate} (Initial: {initial_interest_rate})")
    else:
        print(f"❌ Interest Rate Check Failed: Max {max_rate}, Initial {initial_interest_rate}")

    # 2. Verify Interest Expense Accounting
    if interest_expense_verified:
        print("✅ FinanceDepartment Interest Expense Accounting Verified.")
    else:
        print("❌ FinanceDepartment Interest Expense Verification Failed.")

    # 3. Verify Corporate Resilience (Dividend Suspension)
    distressed_firms = 0
    suspended_dividends = 0

    for firm in sim.firms:
        # Re-calc Z-Score
        z_score = firm.finance.calculate_altman_z_score()

        # Artificial distress check (since we only ran 20 ticks, firms might not be naturally distressed yet)
        # But Phase 29 shock is severe.

        is_distressed = z_score < 1.81 or firm.finance.consecutive_loss_turns >= 3

        if is_distressed:
            distressed_firms += 1
            if firm.dividend_rate == 0.0:
                suspended_dividends += 1
            # print(f"Distressed Firm {firm.id}: Z={z_score:.2f}, DivRate={firm.dividend_rate}")

    print(f"Distressed Firms: {distressed_firms}")
    print(f"Suspended Dividends: {suspended_dividends}")

    if distressed_firms > 0:
        if suspended_dividends == distressed_firms:
             print("✅ All distressed firms suspended dividends.")
        else:
             print("❌ Not all distressed firms suspended dividends.")
    else:
        print("⚠️ No firms became distressed naturally. Forcing distress to test logic...")
        # Force a firm to be distressed
        firm = sim.firms[1]
        firm.finance.consecutive_loss_turns = 10
        firm.dividend_rate = 0.1 # Reset

        # Run one tick to let Manager react
        sim.run_tick()

        if firm.dividend_rate == 0.0:
            print("✅ CorporateManager correctly suspended dividends for artificially distressed firm.")
        else:
            print(f"❌ CorporateManager FAILED to suspend dividends. Rate: {firm.dividend_rate}")

    sim.finalize_simulation()
    print(">>> Verification Complete.")

if __name__ == "__main__":
    verify_phase29()
