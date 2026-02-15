import sys
import os
import logging
import yaml
import json

# Ensure modules are importable
sys.path.append(os.getcwd())

import config
from modules.system.builders.simulation_builder import create_simulation
from modules.simulation.api import ShockConfigDTO
from modules.simulation.shock_injector import ShockInjector
from modules.analysis.phenomena_analyzer import PhenomenaAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PhenomenaAnalysis")

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    logger.info("Starting Phenomena Analysis Simulation")

    # Load configuration
    scenario_config = load_config("config/scenarios/stress_test_phenomena.yaml")

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

    # 3. Setup Analyzer
    analysis_config = scenario_config.get("analysis_config", {})
    analyzer = PhenomenaAnalyzer(analysis_config)

    # 4. Setup Shock (if configured)
    if "shock_start_tick" in scenario_config:
        shock_config = ShockConfigDTO(
            shock_start_tick=scenario_config["shock_start_tick"],
            shock_end_tick=scenario_config["shock_end_tick"],
            tfp_multiplier=scenario_config["tfp_multiplier"],
            baseline_tfp=scenario_config["baseline_tfp"]
        )
        injector = ShockInjector(shock_config, sim)
    else:
        injector = None

    # 5. Run Simulation Loop
    sim_ticks = overrides["SIMULATION_TICKS"]
    logger.info(f"Running simulation for {sim_ticks} ticks...")

    for tick in range(sim_ticks):
        # Apply Shock
        if injector:
            injector.apply(tick)

        # Run Simulation Tick
        if hasattr(sim, "orchestrate_production_and_tech"):
            sim.orchestrate_production_and_tech(tick)

        sim.run_tick()

        # Update Analyzer
        analyzer.run_tick(tick, sim)

    # 6. Generate Report
    report = analyzer.generate_report()

    logger.info("=" * 40)
    logger.info("PHENOMENA ANALYSIS REPORT")
    logger.info("=" * 40)

    # Print JSON representation
    print(json.dumps(report, indent=2, default=str))

    logger.info("=" * 40)
    logger.info("Analysis Complete.")

if __name__ == "__main__":
    main()
