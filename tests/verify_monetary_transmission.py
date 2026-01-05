
import sys
import os
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import create_simulation
import config
from simulation.core_agents import Household
from simulation.ai.enums import Personality

# Global recorder
CONSUMPTION_RECORD = {
    "ant": 0.0,
    "grasshopper": 0.0,
    "ant_count": 0,
    "grasshopper_count": 0
}

# Original consume method
original_consume = Household.consume

def patched_consume(self, item_id: str, quantity: float, current_time: int) -> None:
    # Call original
    original_consume(self, item_id, quantity, current_time)

    # Record
    is_ant = (self.value_orientation == config.VALUE_ORIENTATION_WEALTH_AND_NEEDS)
    if is_ant:
        CONSUMPTION_RECORD["ant"] += quantity
        CONSUMPTION_RECORD["ant_count"] += 1
    else:
        CONSUMPTION_RECORD["grasshopper"] += quantity
        CONSUMPTION_RECORD["grasshopper_count"] += 1

# Apply Patch
Household.consume = patched_consume

def run_scenario(interest_rate_override: float, label: str):
    print(f"\n--- Running Scenario: {label} (Rate: {interest_rate_override:.1%}) ---")

    # Reset Record
    CONSUMPTION_RECORD["ant"] = 0.0
    CONSUMPTION_RECORD["grasshopper"] = 0.0
    CONSUMPTION_RECORD["ant_count"] = 0
    CONSUMPTION_RECORD["grasshopper_count"] = 0

    # Override Config
    overrides = {
        "INITIAL_BASE_ANNUAL_RATE": interest_rate_override,
        "TICKS_PER_YEAR": 100,
        "BATCH_SAVE_INTERVAL": 1000, # Disable frequent DB saves for speed
        "STOCK_MARKET_ENABLED": False,
        "NUM_HOUSEHOLDS": 20,
        "NEUTRAL_REAL_RATE": 0.02,
        "DSR_CRITICAL_THRESHOLD": 0.4,
        "INTEREST_SENSITIVITY_ANT": 5.0,
        "INTEREST_SENSITIVITY_GRASSHOPPER": 1.0,
    }

    sim = create_simulation(overrides=overrides)

    # Force initial inflation expectations to 0
    for h in sim.households:
        h.expected_inflation = {k: 0.0 for k in h.expected_inflation}
        h.assets = 10000.0

    # Run for 50 ticks
    # We ignore the first few ticks to let market stabilize (production start)
    for tick in range(50):
        sim.run_tick()

    # Calculate Per Agent Per Tick
    # Note: CONSUMPTION_RECORD accumulates total quantity over 50 ticks across all agents.
    # We want Avg Consumption Per Agent Per Tick.

    # Count agents
    ant_agents = len([h for h in sim.households if h.value_orientation == config.VALUE_ORIENTATION_WEALTH_AND_NEEDS])
    gh_agents = len(sim.households) - ant_agents

    total_ant_consumption = CONSUMPTION_RECORD["ant"]
    total_gh_consumption = CONSUMPTION_RECORD["grasshopper"]

    avg_ant = (total_ant_consumption / ant_agents) / 50 if ant_agents > 0 else 0
    avg_gh = (total_gh_consumption / gh_agents) / 50 if gh_agents > 0 else 0

    print(f"[{label}] Total Cons - Ant: {total_ant_consumption:.1f}, GH: {total_gh_consumption:.1f}")
    print(f"[{label}] Avg/Tick - Ant: {avg_ant:.4f}, GH: {avg_gh:.4f}")

    return avg_ant, avg_gh

def main():
    # 1. Baseline: 2% (Neutral)
    ant_base, gh_base = run_scenario(0.02, "BASELINE")

    # 2. High Rate: 10% (Tight)
    ant_high, gh_high = run_scenario(0.10, "HIGH_RATE")

    print("\n--- Verification Results ---")

    # Check 1: Aggregate Reduction
    total_base = ant_base + gh_base
    total_high = ant_high + gh_high

    if total_base == 0:
        print("FAIL: Baseline consumption is zero. Simulation error.")
        sys.exit(1)

    reduction = (total_base - total_high) / total_base
    print(f"Total Consumption Reduction: {reduction:.1%}")

    if total_high < total_base:
        print("PASS: High interest rate reduced consumption.")
    else:
        print("FAIL: Consumption did not decrease.")

    # Check 2: Sensitivity Difference
    # Ant sensitivity is 5.0, GH is 1.0
    ant_reduction = (ant_base - ant_high) / ant_base if ant_base > 0 else 0
    gh_reduction = (gh_base - gh_high) / gh_base if gh_base > 0 else 0

    print(f"Ant Reduction: {ant_reduction:.1%}")
    print(f"GH Reduction: {gh_reduction:.1%}")

    if ant_reduction > gh_reduction:
        print("PASS: Ants (Wealth-Oriented) reduced consumption more than Grasshoppers.")
    else:
        print("WARNING: Ants did not reduce more. Check if GH hit Debt Penalty?")

    # Final assertion
    if total_high < total_base and ant_reduction > 0.05:
        print("SUCCESS: Monetary Transmission Mechanism Verified.")
        sys.exit(0)
    else:
        print("FAILURE: Verification criteria not met.")
        sys.exit(1)

if __name__ == "__main__":
    main()
