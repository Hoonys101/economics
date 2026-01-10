from typing import Dict, Any, Optional
import logging
from simulation.engine import Simulation
import main as simulation_main
import config

logger = logging.getLogger("dashboard_connector")

def get_engine_instance() -> Simulation:
    """
    Factory function to create and initialize the Simulation object
    with default configuration from config.py.
    This acts as the bridge between the Streamlit Dashboard and the Simulation Engine.
    """
    # Use the create_simulation factory from main.py to ensure consistent initialization
    # (Households, Firms, AI models, Repository, etc.)
    simulation = simulation_main.create_simulation()
    return simulation

def run_tick(simulation: Simulation) -> int:
    """
    Advances the simulation by one tick.
    Returns the new tick number.
    """
    simulation.run_tick()
    return simulation.time

def get_metrics(simulation: Simulation) -> Dict[str, Any]:
    """
    Extracts key economic metrics from the simulation state.
    Returns a dictionary suitable for dashboard visualization.
    """
    # Ensure tracker has data (it tracks at end of run_tick, but we might check at tick 0)
    # If tick 0, get initial stats or empty/zero values.

    indicators = simulation.tracker.get_latest_indicators()

    # Calculate average assets manually if not in indicators
    # Note: indicators usually have aggregate data.

    total_population = len([h for h in simulation.households if h.is_active])

    # Use 'total_production' as GDP proxy if available, or calculate sum of production
    gdp = indicators.get("total_production", 0.0)

    # Calculate average assets
    active_households = [h for h in simulation.households if h.is_active]
    total_assets = sum(h.assets for h in active_households)
    avg_assets = total_assets / total_population if total_population > 0 else 0.0

    # Unemployment Rate
    unemployment_rate = indicators.get("unemployment_rate", 0.0)

    return {
        "tick": simulation.time,
        "total_population": total_population,
        "gdp": gdp,
        "average_assets": avg_assets,
        "unemployment_rate": unemployment_rate,
        # Additional useful metrics
        "inflation_rate": indicators.get("inflation_rate", 0.0),
        "total_consumption": indicators.get("total_consumption", 0.0)
    }

def update_params(simulation: Simulation, new_params: Dict[str, Any]) -> None:
    """
    Updates simulation configuration at runtime.
    """
    for key, value in new_params.items():
        if hasattr(simulation.config_module, key):
            setattr(simulation.config_module, key, value)
            logger.info(f"[Dashboard] Updated config: {key} -> {value}")
        else:
            logger.warning(f"[Dashboard] Unknown config key: {key}")
