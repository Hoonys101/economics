from typing import Dict, Any, Optional
import logging
from simulation.engine import Simulation
import main as simulation_main

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

    # --- WO-043: Advanced Metrics ---
    # 1. Labor Share = (Total Labor Income / Nominal GDP) * 100
    total_labor_income = indicators.get("total_labor_income", 0.0)
    avg_goods_price = indicators.get("avg_goods_price", 0.0)
    total_production = indicators.get("total_production", 0.0)
    nominal_gdp = total_production * avg_goods_price

    labor_share = 0.0
    if nominal_gdp > 0:
        labor_share = (total_labor_income / nominal_gdp) * 100.0

    # 2. Velocity of Money = Nominal GDP / Money Supply
    money_supply = indicators.get("money_supply", 0.0)
    velocity_of_money = 0.0
    if money_supply > 0:
        velocity_of_money = nominal_gdp / money_supply

    # 3. Inventory Turnover = Total Sales Volume / Total Inventory
    total_sales_volume = indicators.get("total_sales_volume", 0.0)
    total_inventory = indicators.get("total_inventory", 0.0)
    inventory_turnover = 0.0
    if total_inventory > 0:
        inventory_turnover = total_sales_volume / total_inventory

    return {
        "tick": simulation.time,
        "total_population": total_population,
        "gdp": gdp,
        "average_assets": avg_assets,
        "unemployment_rate": unemployment_rate,
        # Additional useful metrics
        "inflation_rate": indicators.get("inflation_rate", 0.0),
        "total_consumption": indicators.get("total_consumption", 0.0),
        # WO-043 Metrics
        "money_supply": money_supply,
        "nominal_gdp": nominal_gdp,
        "total_labor_income": total_labor_income,
        "labor_share": labor_share,
        "velocity_of_money": velocity_of_money,
        "inventory_turnover": inventory_turnover
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

def get_agent_details(simulation: Simulation, agent_id: int) -> Dict[str, Any]:
    """
    Returns detailed info for a specific agent.
    Focuses on Household agents and their System 2 Planner state.
    """
    agent = simulation.agents.get(agent_id)
    if not agent:
        return {"error": f"Agent {agent_id} not found"}

    # Extract System 2 projection if available
    # System2Planner is usually initialized on Household
    system2 = getattr(agent, 'system2_planner', None)
    projection = system2.cached_projection if system2 else {}

    details = {
        "id": agent.id,
        "assets": agent.assets,
        "is_active": getattr(agent, "is_active", False),
        "gender": getattr(agent, "gender", "N/A"),
        "age": getattr(agent, "age", 0),
        "children_count": len(getattr(agent, "children_ids", [])),
        "npv_wealth": projection.get("npv_wealth", 0.0),
        "bankruptcy_tick": projection.get("bankruptcy_tick", None),
        "last_leisure_type": getattr(agent, "last_leisure_type", "N/A"),
    }

    return details
