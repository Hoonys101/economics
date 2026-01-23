import sys
from pathlib import Path
import os
import logging

# Ensure the project root is in the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from simulation.dtos import GovernmentStateDTO

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("verify_policy_reaction")


def verify_policy_reaction(num_ticks: int = 122):
    """
    Runs a simulation to verify the Central Bank's reaction to an inflation shock.
    """
    logger.info("Initializing Policy Reaction Verification Simulation...")

    # Override config to ensure AI is active
    overrides = {
        "GOVERNMENT_POLICY_MODE": "AI_ADAPTIVE",
    }
    simulation = create_simulation(overrides=overrides)

    initial_base_rate = simulation.central_bank.get_base_rate()
    logger.info(f"Initial Central Bank Base Rate: {initial_base_rate:.4f}")

    rate_before_shock = initial_base_rate

    logger.info(f"Running simulation for {num_ticks} ticks...")

    shock_dto = None

    for tick in range(1, num_ticks + 1):
        # We need to inject the shock on a tick where the government AI makes a decision.
        # The SmartLeviathanPolicy has a 30-tick action interval.
        # Let's burn in for 120 ticks and inject the shock then.
        if tick == 120:
            rate_before_shock = simulation.central_bank.get_base_rate()
            logger.info(
                f"Base rate before shock application at tick {tick}: {rate_before_shock:.4f}"
            )
            logger.warning(f"INJECTING INFLATION SHOCK at tick {tick}")

            # Create a modified DTO with a high inflation rate
            shock_dto = GovernmentStateDTO(
                tick=tick,
                inflation_sma=0.15,  # 15% inflation shock
                unemployment_sma=simulation.tracker.get_latest_indicators().get(
                    "unemployment_rate", 0.05
                ),
                gdp_growth_sma=0,  # Assume neutral growth for isolation
                wage_sma=simulation.tracker.get_latest_indicators().get(
                    "avg_wage", 1000
                ),
                approval_sma=0.5,  # Assume neutral approval
                current_gdp=simulation.tracker.get_latest_indicators().get(
                    "total_production", 10000
                ),
            )

        # Pass the shock DTO to run_tick, it will only be used if the tick matches
        simulation.run_tick(injectable_sensory_dto=shock_dto)

        if tick >= 119:
            current_rate = simulation.central_bank.get_base_rate()
            logger.info(f"Tick {tick}: Central Bank Base Rate: {current_rate:.4f}")

    # --- Verification Checks ---
    logger.info("--- Verification Results ---")

    final_base_rate = simulation.central_bank.get_base_rate()
    logger.info(f"Base rate before shock (at tick 120): {rate_before_shock:.4f}")
    logger.info(f"Final base rate at tick {num_ticks}: {final_base_rate:.4f}")

    if final_base_rate > rate_before_shock:
        print("PASS: Interest Rate Increased")
        logger.info(
            "✅ SUCCESS: Central Bank reacted to inflation by increasing the interest rate."
        )
    else:
        print("FAIL: Interest Rate Did Not Increase")
        logger.error(
            "❌ FAILURE: Central Bank did not increase the interest rate in response to the inflation shock."
        )


if __name__ == "__main__":
    verify_policy_reaction()
