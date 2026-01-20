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

    overrides = {
        "SIMULATION_TICKS": 25, # Run a bit longer
        "INITIAL_FIRM_CAPITAL_MEAN": 50000.0, # Ensure enough capital to survive start
    }

    sim = create_simulation(overrides=overrides)

    # Check if scenario loaded
    if not sim.stress_scenario_config.is_active:
        print("❌ Scenario NOT Active! Check ConfigManager.")
        # Try to force it if env var failed
        sim.stress_scenario_config.is_active = True
        sim.stress_scenario_config.scenario_name = "phase29_depression"
        sim.stress_scenario_config.start_tick = 5
        sim.stress_scenario_config.base_interest_rate_multiplier = 3.0
        sim.stress_scenario_config.corporate_tax_rate_delta = 0.1
        sim.stress_scenario_config.demand_shock_multiplier = 0.7
        print("⚠️ Forced Scenario Activation manually.")
    else:
        print(f"✅ Scenario Loaded: {sim.stress_scenario_config.scenario_name}")

    # Inject Debt to Firms to ensure Interest Expense
    print(">>> Injecting Loans for Interest Verification...")
    for firm in sim.firms:
        # Borrow 20,000
        if sim.bank:
            sim.bank.grant_loan(firm.id, 20000.0, 100)

    # 5. Run for 20 ticks
    print(">>> Running Simulation for 20 ticks...")
    initial_interest_rate = sim.bank.base_rate
    print(f"Initial Interest Rate: {initial_interest_rate}")

    scenario_active_tick = sim.stress_scenario_config.start_tick

    # Track metrics
    interest_rate_increased = False
    max_rate = initial_interest_rate

    for i in range(1, 21):
        sim.run_tick()
        current_tick = sim.time

        # Check Interest Rate Change
        if sim.bank.base_rate > max_rate:
             max_rate = sim.bank.base_rate
             interest_rate_increased = True
             print(f"Tick {current_tick}: Interest Rate Increased to {max_rate}")

    # 6. Verification
    print("\n>>> Final Verification Report")

    # 1. Verify Interest Rate
    if interest_rate_increased and max_rate >= initial_interest_rate * 2.9: # Approx 3.0
        print(f"✅ Interest Rate Multiplier Applied: {max_rate} (Initial: {initial_interest_rate})")
    else:
        print(f"❌ Interest Rate Check Failed: Max {max_rate}, Initial {initial_interest_rate}")

    # 2. Verify Corporate Resilience (Dividend Suspension)
    # Check if any firm had Z-Score < 1.81 and Dividend Rate became 0.0
    distressed_firms = 0
    suspended_dividends = 0
    total_interest_expense_detected = False

    for firm in sim.firms:
        # Skip very young firms (Startups often have low Z-Score due to 0 profit history)
        if firm.age < 5:
            continue

        z_score = firm.finance.calculate_altman_z_score()

        # Check if interest was recorded (expenses > maintenance)
        # Maintenance is 50.0. If expenses > 60.0, likely interest.
        # But expenses reset every tick.
        # We can't check history easily unless we tracked it.
        # But we can check `total_debt` and `retained_earnings`.

        if z_score < 1.81 or firm.finance.consecutive_loss_turns >= 3:
            distressed_firms += 1
            if firm.dividend_rate == 0.0:
                suspended_dividends += 1
            print(f"Distressed Firm {firm.id}: Z={z_score:.2f}, DivRate={firm.dividend_rate}")

    print(f"Distressed Firms (Age >= 5): {distressed_firms}")
    print(f"Suspended Dividends: {suspended_dividends}")

    if distressed_firms > 0:
        if suspended_dividends == distressed_firms:
             print("✅ All distressed firms suspended dividends.")
        else:
             print("❌ Not all distressed firms suspended dividends.")
    else:
        print("⚠️ No firms became distressed. Logic verification skipped for dividends.")

    sim.finalize_simulation()
    print(">>> Verification Complete.")

if __name__ == "__main__":
    verify_phase29()
