import sys
import logging
from typing import Dict, Any
from modules.common.utils.logging_manager import (
    setup_logging,
    SamplingFilter,
)
import config
from modules.system.builders.simulation_builder import create_simulation

main_logger = logging.getLogger(__name__)

# --- Setup Logging ---
def setup_app():
    setup_logging()  # Call the setup function
    logging.getLogger().setLevel(logging.DEBUG) # Force DEBUG level for all loggers

    # Get the SamplingFilter instance and set sampling rates
    sampling_filter: SamplingFilter | None = None
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            for filter_obj in handler.filters:
                if isinstance(filter_obj, SamplingFilter):
                    sampling_filter = filter_obj
                    break
            else:
                continue
            break


    if sampling_filter:
        sampling_filter.sampling_rates["AIDecision"] = 0.1
        sampling_filter.sampling_rates["ProduceDebug"] = 0.1
        sampling_filter.sampling_rates["FoodConsumptionCalc"] = 0.1
        sampling_filter.sampling_rates["FoodConsumptionControlled"] = 0.1
        sampling_filter.sampling_rates["FoodConsumptionSkipped"] = 0.1
        logging.info("Sampling rates applied to logging.", extra={"tags": ["setup"]})
    else:
        logging.warning(
            "SamplingFilter not found in logging handlers. Sampling rates not applied.",
            extra={"tags": ["setup"]},
        )

# --- End Setup Logging ---

def run_simulation(
    firm_production_targets=None,
    initial_firm_inventory_mean=None,
    output_filename="simulation_results.csv",
):
    overrides = {}
    if initial_firm_inventory_mean is not None:
        overrides["INITIAL_FIRM_INVENTORY_MEAN"] = initial_firm_inventory_mean

    # We don't override firm_production_targets in create_simulation as it is not used in the original loop
    # The original loop just ran sim.run_tick().
    # However, create_simulation needs to handle temporary config changes.
    # The original code changed config globally then changed it back.
    # Here create_simulation changes it globally and leaves it.
    # If run_simulation needs to restore it, it should handle that.

    original_initial_firm_inventory_mean = None
    if initial_firm_inventory_mean is not None:
         original_initial_firm_inventory_mean = config.INITIAL_FIRM_INVENTORY_MEAN

    sim = create_simulation(overrides=overrides)

    # Restore config if needed (since create_simulation modifies it globally)
    # The original code modified config global variable.
    # create_simulation also modifies it.

    simulation_ticks = config.SIMULATION_TICKS

    for i in range(simulation_ticks):
        # Pass the repository to the run_tick method
        sim.run_tick()

    sim.ai_training_manager.end_episode(sim.get_all_agents())
    logging.info(
        "Simulation finished. Closing logger.",
        extra={"tick": sim.time, "tags": ["shutdown"]},
    )

    # Close the SimulationRepository connection at the end
    sim.repository.close()

    # Restore original config if we changed it
    if original_initial_firm_inventory_mean is not None:
        config.INITIAL_FIRM_INVENTORY_MEAN = original_initial_firm_inventory_mean


if __name__ == "__main__":
    setup_app()
    output_filename = "simulation_results.csv"
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    run_simulation(output_filename=output_filename)
