
import logging
import sys
from pathlib import Path
import os

# Add project root to sys.path before importing local modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import random
import config
import logging.config

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_wo054")

def run_experiment():
    """
    Runs the WO-054 Verification Experiment.
    Target: IGE (Intergenerational Elasticity) Reduction.
    """
    logger.info("Starting WO-054 Verification Experiment (Education ROI)...")

    # 1. Initialize Simulation
    # Override config to enable WO-054 mechanics
    overrides = {
        "HALO_EFFECT": 0.15,
        "SIMULATION_TICKS": 500, # 500 ticks as requested

        # WO-054 Configs
        "PUBLIC_EDU_BUDGET_RATIO": 0.20,
        "SCHOLARSHIP_WEALTH_PERCENTILE": 0.20,
        "SCHOLARSHIP_POTENTIAL_THRESHOLD": 0.7,

        # Enable Tech Feedback
        "TECH_DIFFUSION_RATE": 0.05,
        "TECH_FERTILIZER_UNLOCK_TICK": 50, # Early unlock to see diffusion

        # Reset parameters to somewhat normal but stressed enough to show gap
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 5000.0,
        "INITIAL_FIRM_CAPITAL_MEAN": 50000.0,
        "GOVERNMENT_STIMULUS_ENABLED": True,

        # RuleBased for consistency in short run
        "DEFAULT_ENGINE_TYPE": "RuleBased",
    }

    from main import create_simulation
    sim = create_simulation(overrides)

    # 2. Run Simulation
    target_ticks = 500

    logger.info(f"Running simulation for {target_ticks} ticks...")

    history_data = []

    for tick in range(target_ticks):
        try:
            sim.run_tick()
        except Exception as e:
            logger.error(f"Simulation crashed at tick {tick}: {e}")
            import traceback
            traceback.print_exc()
            break

        # Periodic Data Collection
        if tick % 10 == 0:
            for agent in sim.households:
                if agent.is_active:
                    data = {
                        "agent_id": agent.id,
                        "education_level": getattr(agent, "education_level", 0),
                        "initial_assets": getattr(agent, "initial_assets_record", 0.0),
                        "tick": tick
                    }
                    history_data.append(data)

        if tick % 50 == 0:
            avg_edu = sim.technology_manager.human_capital_index
            logger.info(f"Tick {tick}: Avg Edu Level {avg_edu:.2f}")

    # 3. Analysis
    logger.info("Collecting agent data...")
    if not history_data:
        logger.error("No history data collected.")
        return

    df = pd.DataFrame(history_data)

    # Analyze the LAST snapshot
    last_tick = df["tick"].max()
    final_df = df[df["tick"] == last_tick]

    if final_df.empty:
        logger.error("No final data.")
        return

    # 5. Generational Mobility (Ladder)
    # Correlation between Initial Assets and Education Level
    # WO-054 Target: Drop from 0.96 to < 0.7
    corr_wealth_edu = final_df["initial_assets"].corr(final_df["education_level"])

    logger.info(f"Final Correlation (Initial Assets vs Education): {corr_wealth_edu:.4f}")

    # 6. Verification
    pass_criteria = True
    status_msg = ""

    if corr_wealth_edu >= 0.7:
        pass_criteria = False
        status_msg += f"FAIL: IGE (Wealth-Edu Corr) {corr_wealth_edu:.4f} >= 0.7. (Target < 0.7)"
    else:
        status_msg += f"PASS: IGE (Wealth-Edu Corr) {corr_wealth_edu:.4f} < 0.7."

    # Tech Diffusion Check
    # We can check adoption count
    adopted_count = sum(len(v) for v in sim.technology_manager.adoption_registry.values())
    logger.info(f"Total Tech Adoptions: {adopted_count}")

    avg_edu_final = sim.technology_manager.human_capital_index
    logger.info(f"Final Avg Education: {avg_edu_final:.2f}")

    final_status = "[PASS]" if pass_criteria else "[FAIL]"

    print(f"WO-054 VERIFICATION REPORT")
    print(f"==========================")
    print(f"Status: {final_status}")
    print(f"IGE (Wealth-Edu Corr): {corr_wealth_edu:.4f}")
    print(f"Avg Education Level: {avg_edu_final:.2f}")
    print(f"Tech Adoptions: {adopted_count}")
    print(f"Message: {status_msg}")

if __name__ == "__main__":
    run_experiment()
