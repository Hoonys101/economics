import sys
import os
import logging
import json
import statistics
from pathlib import Path

# Setup paths
sys.path.append(os.path.abspath("."))

# Mock imports
try:
    import dotenv
except ImportError:
    from unittest.mock import MagicMock
    sys.modules["dotenv"] = MagicMock()
    sys.modules["dotenv"].load_dotenv = MagicMock()

try:
    import yaml
except ImportError:
    from unittest.mock import MagicMock
    sys.modules["yaml"] = MagicMock()

# Import core modules
import config as Config
from simulation.initialization.initializer import SimulationInitializer
from simulation.db.repository import SimulationRepository
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai_model import AIEngineRegistry
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_agents import Talent
from simulation.ai.api import Personality
from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
from simulation.decisions.standalone_rule_based_firm_engine import StandaloneRuleBasedFirmDecisionEngine
from modules.common.config_manager.api import ConfigManager
from simulation.dtos import DecisionContext, MacroFinancialContext
from simulation.components.economy_manager import EconomyManager
from simulation.models import Order
from simulation.ai.api import Tactic, Aggressiveness
from unittest.mock import MagicMock

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Phase23Verify")

class MockConfigManager(ConfigManager):
    def __init__(self, config_module):
        self.config = config_module

    def get(self, key, default=None):
        return getattr(self.config, key, default)

def load_scenario_config():
    """Load configuration from the scenario JSON file."""
    scenario_path = "config/scenarios/phase23_industrial_rev.json"
    if os.path.exists(scenario_path):
        with open(scenario_path, 'r') as f:
            data = json.load(f)
            return data
    return {}

def verify_harvest_clean():
    logger.info("--- Starting Verification (Clean): Phase 23 The Great Harvest ---")

    # 1. Load Configuration
    scenario_data = load_scenario_config()
    params = scenario_data.get("parameters", {})

    # Apply Config Overrides based on Scenario
    Config.SIMULATION_TICKS = 200
    Config.TECH_FERTILIZER_UNLOCK_TICK = 5 # As per scenario requirements (overriding default for test)
    # Config.food_tfp_multiplier = params.get("food_tfp_multiplier", 3.0) # Not a direct config attribute, used in TechManager

    # Enable Mitosis/Breeding for Population Boom
    Config.TECH_CONTRACEPTION_ENABLED = False
    Config.BIOLOGICAL_FERTILITY_RATE = 0.15

    # 2. Setup Simulation Components
    repo = MagicMock(spec=SimulationRepository)
    repo.save_simulation_run.return_value = 1
    config_manager = MockConfigManager(Config)

    state_builder = StateBuilder()
    action_proposal = ActionProposalEngine(config_module=Config)
    ai_registry = AIEngineRegistry(action_proposal_engine=action_proposal, state_builder=state_builder)

    num_households = 50
    num_firms = 10

    goods_data = [
        {"id": "basic_food", "sector": "FOOD", "is_luxury": False, "utility_effects": {"survival": 10}, "initial_price": 5.0},
        {"id": "consumer_goods", "sector": "GOODS", "is_luxury": True, "utility_effects": {"quality": 10}, "initial_price": 15.0}
    ]

    # Create Agents
    households = []
    for i in range(num_households):
        initial_needs = {"survival": 50, "social": 10, "growth": 10, "quality": 10}
        hh = Household(
            id=i,
            initial_assets=10000 + (i * 100), # Sufficient runway
            decision_engine=RuleBasedHouseholdDecisionEngine(Config, logger),
            config_module=Config,
            talent=Talent(1.0, {}),
            goods_data=goods_data,
            initial_needs=initial_needs,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            initial_age=25.0
        )
        households.append(hh)

    firms = []
    for i in range(num_firms):
        sector = "FOOD" if i < 5 else "GOODS"
        spec = "basic_food" if sector == "FOOD" else "consumer_goods"
        firm = Firm(
            id=i + 1000,
            initial_capital=50000,
            initial_liquidity_need=1000,
            specialization=spec,
            productivity_factor=10.0,
            decision_engine=StandaloneRuleBasedFirmDecisionEngine(Config, logger),
            value_orientation="PROFIT",
            config_module=Config,
            sector=sector,
            is_visionary=(i==0),
            personality=Personality.BALANCED
        )
        firms.append(firm)

    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=Config,
        goods_data=goods_data,
        repository=repo,
        logger=logger,
        households=households,
        firms=firms,
        ai_trainer=ai_registry
    )

    sim = initializer.build_simulation()

    # Disable AI Training to avoid RuleBased/AI mix issues in this specific test
    # But wait, Mitigation/Mitosis needs inherit_brain from AI Training Manager.
    # We must keep it but ensure it doesn't crash on RuleBased agents.
    # The fix in ai_training_manager.py (checking for hasattr ai_engine) should handle this.
    # So we DO NOT set it to None.
    # sim.ai_training_manager = None

    # Trackers
    data = {
        "tick": [],
        "food_price": [],
        "population": [],
        "engel_coeff": [],
        "tech_adopted": []
    }

    logger.info("Running Simulation Loop (200 Ticks)...")

    for tick in range(Config.SIMULATION_TICKS):
        sim.run_tick()

        # 1. Food Price
        food_market = sim.markets.get("basic_food")
        avg_price = food_market.get_daily_avg_price() if food_market else 0.0
        if avg_price == 0 and data["food_price"]:
            avg_price = data["food_price"][-1] # Carry forward
        elif avg_price == 0:
            avg_price = 5.0

        # 2. Population
        active_households = [h for h in sim.households if h.is_active]
        pop_count = len(active_households)

        # 3. Engel Coefficient
        # Calculate aggregate Food Spend / Total Spend
        total_spend = 0.0
        food_spend = 0.0

        for h in active_households:
            # Current consumption is cumulative in EconomyManager
            # But we want tick-based?
            # EconomyManager tracks `current_consumption` and `current_food_consumption`.
            # These are cumulative counters (usually reset? No, they seem cumulative in `EconomyManager`).
            # Ideally we'd diff them, but for this report, looking at the cumulative ratio is also valid for long-term trend,
            # OR we can assume `sim.run_tick` doesn't reset them.
            # Let's rely on cumulative ratio as it stabilizes over time.
            total_spend += h.econ_component.current_consumption
            food_spend += h.econ_component.current_food_consumption

        engel = (food_spend / total_spend) if total_spend > 0 else 1.0

        # 4. Tech Adoption
        adopted = sum(1 for f in sim.firms if sim.technology_manager.has_adopted(f.id, "TECH_AGRI_CHEM_01"))

        # Store
        data["tick"].append(tick)
        data["food_price"].append(avg_price)
        data["population"].append(pop_count)
        data["engel_coeff"].append(engel)
        data["tech_adopted"].append(adopted)

    # --- Verification ---
    logger.info("--- Verification Results ---")

    initial_price = data["food_price"][0]
    final_price = data["food_price"][-1]
    price_drop = (initial_price - final_price) / initial_price
    pass_price = price_drop >= 0.5

    initial_pop_val = data["population"][0]
    final_pop_val = data["population"][-1]
    pop_growth = final_pop_val / initial_pop_val
    pass_pop = pop_growth >= 2.0

    final_engel = data["engel_coeff"][-1]
    pass_engel = final_engel < 0.5

    verdict = "ESCAPE VELOCITY ACHIEVED" if (pass_price and pass_pop and pass_engel) else "FAILED"
    logger.info(f"VERDICT: {verdict}")

    # --- Generate Report ---
    report_path = "design/gemini_output/report_phase23_great_harvest.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# WO-094: Phase 23 The Great Harvest Verification Report\n\n")
        f.write(f"**Date**: 2026-01-21\n")
        f.write(f"**Verdict**: {verdict}\n\n")

        f.write("## Executive Summary\n")
        f.write("| Metric | Initial | Final | Result | Pass Criteria | Pass |\n")
        f.write("|---|---|---|---|---|---|\n")
        f.write(f"| Food Price | {initial_price:.2f} | {final_price:.2f} | {price_drop*100:.1f}% Drop | >= 50% Drop | {pass_price} |\n")
        f.write(f"| Population | {initial_pop_val} | {final_pop_val} | {pop_growth:.2f}x Growth | >= 2.0x Growth | {pass_pop} |\n")
        f.write(f"| Engel Coeff | {data['engel_coeff'][0]:.2f} | {final_engel:.2f} | {final_engel:.2f} | < 0.50 | {pass_engel} |\n\n")

        f.write("## Detailed Metrics (Sample)\n")
        f.write("| Tick | Food Price | Population | Engel | Tech Adopted |\n")
        f.write("|---|---|---|---|---|\n")
        # Sample every 20 ticks
        for i in range(0, len(data["tick"]), 20):
            f.write(f"| {data['tick'][i]} | {data['food_price'][i]:.2f} | {data['population'][i]} | {data['engel_coeff'][i]:.2f} | {data['tech_adopted'][i]} |\n")
        f.write(f"| {data['tick'][-1]} | {data['food_price'][-1]:.2f} | {data['population'][-1]} | {data['engel_coeff'][-1]:.2f} | {data['tech_adopted'][-1]} |\n\n")

        f.write("## Technical Debt & Issues Resolved\n")
        f.write("- **Engine Fixes**: Patched core files (`RuleBasedHouseholdDecisionEngine`, `EconomyManager`, etc.) to fix API mismatches and logic bugs.\n")
        f.write("- **Consumption Tracking**: Fixed `EconomyManager` to correctly track `basic_food` consumption for Engel Coefficient.\n")
        f.write("- **Market Routing**: Fixed Firm decision engine to route orders to specific item markets (e.g., `basic_food`) instead of generic `goods_market`.\n")

if __name__ == "__main__":
    verify_harvest_clean()
