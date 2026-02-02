import os
import sys
from pathlib import Path
import logging
import random
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any

# Ensure project root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.bank import Bank
import config
from main import create_simulation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("verify_portfolio")

def run_verification(output_file: str = "reports/verify_portfolio.png"):
    """
    Scenario:
    1. Run simulation normally for 50 ticks.
    2. At T=50, Central Bank Rate hikes significantly (5% -> 10%).
    3. Measure Household Deposits vs Consumption/Investment.
    4. Expectation: Deposits spike (Friedman Effect).
    """

    # 1. Setup
    logger.info("Initializing Verification Simulation...")

    # Override config for clarity
    overrides = {
        "SIMULATION_TICKS": 100,
        "INITIAL_BASE_ANNUAL_RATE": 0.05,
        "CB_UPDATE_INTERVAL": 1000, # Disable auto-update to control manually
        "STARTUP_COST": 10000.0,
        "EXPECTED_STARTUP_ROI": 0.15, # Fixed expectation
    }

    sim = create_simulation(overrides=overrides)

    # Track Metrics
    sim.history_data = []

    # 2. Run T=0 to T=49 (Normal Phase)
    logger.info("Running Normal Phase (Rate 5%)...")
    for t in range(50):
        sim.run_tick()
        record_metrics(sim, t, "Normal")

    # 3. Shock Event at T=50
    logger.info(">>> SHOCK EVENT: Rate Hike (5% -> 20%) <<<")
    # Force update bank rate
    sim.bank.update_base_rate(0.20)

    # 4. Run T=50 to T=100 (High Rate Phase)
    logger.info("Running High Rate Phase (Rate 20%)...")
    for t in range(50):
        sim.run_tick()
        record_metrics(sim, 50+t, "HighRate")

    # 5. Analysis
    df = pd.DataFrame(sim.history_data)
    analyze_results(df, output_file)

def record_metrics(sim: Simulation, tick: int, phase: str):
    total_deposits = sum(sim.bank.deposits.get(d_id).amount for d_id in sim.bank.deposits)
    total_cash = sum(h._econ_state.assets for h in sim.households)

    # Calculate Flow (Change in deposits)
    # We rely on total stock for now.

    # Track orders generated this tick? Hard to access retrospectively without hooks.
    # We'll use state snapshots.

    history_entry = {
        "tick": tick,
        "phase": phase,
        "base_rate": sim.bank.base_rate,
        "total_deposits": total_deposits,
        "total_cash": total_cash,
        "deposit_ratio": total_deposits / (total_deposits + total_cash + 1e-9)
    }

    # Append to external list (closure)
    # Actually, pass list or use global?
    # Let's attach to sim for convenience or return
    if not hasattr(sim, "history_data"):
        sim.history_data = []
    sim.history_data.append(history_entry)

def analyze_results(df: pd.DataFrame, output_file: str):
    logger.info("\n--- Verification Results ---")

    # Compare Avg Deposit Ratio before and after T=50
    # Allow some lag for monthly rebalancing (every 30 ticks).
    # Rebalancing happens at T=0, 30, 60, 90.
    # Shock at T=50.
    # Next rebalance at T=60.

    before_shock = df[df['tick'] < 50]
    after_shock = df[df['tick'] >= 60] # Look after next rebalance

    avg_dep_pre = before_shock['total_deposits'].mean()
    avg_dep_post = after_shock['total_deposits'].mean()

    logger.info(f"Avg Deposits (Pre-Shock): {avg_dep_pre:.2f}")
    logger.info(f"Avg Deposits (Post-Shock): {avg_dep_post:.2f}")

    if avg_dep_post > avg_dep_pre:
        logger.info("✅ SUCCESS: Deposits increased after rate hike.")
    else:
        logger.warning("❌ FAILURE: Deposits did not increase significantly.")

    # Visualization
    plt.figure(figsize=(10, 6))
    plt.plot(df['tick'], df['total_deposits'], label='Total Deposits', color='blue')
    plt.axvline(x=50, color='red', linestyle='--', label='Rate Hike (5%->20%)')

    # Mark rebalancing points
    for x in range(0, 100, 30):
        plt.axvline(x=x, color='gray', linestyle=':', alpha=0.5)

    plt.title("Friedman Effect Verification: Deposits vs Interest Rate")
    plt.xlabel("Tick")
    plt.ylabel("Total Deposits")
    plt.legend()
    plt.grid(True)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file)
    logger.info(f"Chart saved to {output_file}")

if __name__ == "__main__":
    # Monkey patch record_metrics to store data in sim object
    run_verification()

    # Access data from the last run (not clean, but works for script)
    # The run_verification function creates 'sim' locally.
    # We need to extract data.
    # Refactoring run_verification to do analysis inside.
