import sys
import os
import logging
import yaml

# Ensure modules are importable
sys.path.append(os.getcwd())

import config
from utils.simulation_builder import create_simulation
from modules.simulation.api import ShockConfigDTO
from modules.simulation.shock_injector import ShockInjector
from modules.analysis.api import VerificationConfigDTO
from modules.analysis.storm_verifier import StormVerifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StressTestWO148")

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    logger.info("Starting WO-148: The Perfect Storm Stress Test")

    # Load configuration
    scenario_config = load_config("config/scenarios/stress_test_wo148.yaml")

    # 1. Setup Config overrides
    overrides = {
        "ENABLE_MONETARY_STABILIZER": scenario_config.get("ENABLE_MONETARY_STABILIZER", True),
        "ENABLE_FISCAL_STABILIZER": scenario_config.get("ENABLE_FISCAL_STABILIZER", True),
        "SIMULATION_TICKS": scenario_config.get("SIMULATION_TICKS", 200),
        "NUM_HOUSEHOLDS": scenario_config.get("NUM_HOUSEHOLDS", 50),
        "NUM_FIRMS": scenario_config.get("NUM_FIRMS", 10),
    }

    # 2. Create Simulation
    logger.info("Initializing Simulation...")
    sim = create_simulation(overrides=overrides)

    # 3. Setup Shock and Verifier
    shock_config = ShockConfigDTO(
        shock_start_tick=scenario_config["shock_start_tick"],
        shock_end_tick=scenario_config["shock_end_tick"],
        tfp_multiplier=scenario_config["tfp_multiplier"],
        baseline_tfp=scenario_config["baseline_tfp"]
    )

    # Sim satisfies ISimulationState protocol
    injector = ShockInjector(shock_config, sim)

    verification_config = VerificationConfigDTO(
        max_starvation_rate=scenario_config["max_starvation_rate"],
        max_debt_to_gdp=scenario_config["max_debt_to_gdp"],
        zlb_threshold=scenario_config["zlb_threshold"],
        deficit_spending_threshold=scenario_config["deficit_spending_threshold"],
        basic_food_key=scenario_config["basic_food_key"],
        starvation_threshold=scenario_config["starvation_threshold"]
    )

    verifier = StormVerifier(verification_config, sim)

    # 4. Run Simulation Loop
    logger.info(f"Running simulation for {config.SIMULATION_TICKS} ticks...")

    for tick in range(config.SIMULATION_TICKS):
        # Apply Shock
        injector.apply(tick)

        # Run Simulation Tick
        # Mirroring main.py logic
        if hasattr(sim, "orchestrate_production_and_tech"):
            sim.orchestrate_production_and_tech(tick)

        sim.run_tick()

        # Verify
        # Use public interface via ISimulationState protocol
        snapshot = sim.get_market_snapshot()
        verifier.update(tick, snapshot)

    # 5. Generate Report
    report = verifier.generate_report()

    logger.info("Stress Test Completed.")
    logger.info(f"Report: {report}")

    # 6. Assertions
    if report["success"]:
        logger.info("SUCCESS: The Perfect Storm stress test passed.")
    else:
        logger.error("FAILURE: The Perfect Storm stress test failed.")
        logger.error(f"Details: Starvation={report['starvation_rate']:.2%}, PeakDebt/GDP={report['peak_debt_to_gdp']:.2f}")
        # We exit with 0 to allow the CI/Plan to continue, but log error.
        # Or strict failure? "The Perfect Storm stress test failed."
        # If strict failure, I should exit 1.
        # But this is a "Test Spec" implementation. If the simulation logic itself fails the test (economy collapses),
        # it might be a valid result of the stress test (system not resilient enough yet).
        # However, the task is "Implement ShockInjector", not "Fix Economy".
        # So I will not fail the build if the economy fails, unless the *code* crashes.
        # But wait, Step 5 in draft says: `assert report["success"], "The Perfect Storm stress test failed."`
        # So I should probably raise error.
        # I'll raise SystemExit(1) if it fails, to signal the user.
        sys.exit(1)

if __name__ == "__main__":
    main()
