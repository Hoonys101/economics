import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.abspath("."))

from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.firms import Firm
import config as Config
import simulation.db.database

simulation.db.database.DATABASE_NAME = ":memory:"
from simulation.db.repository import SimulationRepository
from simulation.ai_model import AIEngineRegistry

# --- Configuration for Verification ---
Config.NUM_HOUSEHOLDS = 50
Config.NUM_FIRMS = 5
Config.SIMULATION_TICKS = 150  # Run enough to see adoption
Config.TECH_FERTILIZER_UNLOCK_TICK = 10  # Early unlock
Config.TECH_DIFFUSION_RATE = 0.2  # Fast diffusion for test
Config.FIRM_MIN_PRODUCTION_TARGET = 10.0
Config.ENABLE_VANITY_SYSTEM = False  # Disable for simpler test
Config.STOCK_MARKET_ENABLED = False  # Disable for simpler test

from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine


def verify_industrial_revolution():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("IndustrialRevVerify")

    logger.info("--- Starting Verification: WO-053 Industrial Revolution ---")

    # 1. Setup Simulation
    repo = SimulationRepository()

    # Initialize AI dependencies
    state_builder = StateBuilder()
    action_proposal = ActionProposalEngine(config_module=Config)
    ai_registry = AIEngineRegistry(
        action_proposal_engine=action_proposal, state_builder=state_builder
    )

    # Create agents
    from simulation.core_agents import Talent
    from simulation.ai.api import Personality
    from simulation.decisions.rule_based_household_engine import (
        RuleBasedHouseholdDecisionEngine,
    )
    from simulation.decisions.standalone_rule_based_firm_engine import (
        StandaloneRuleBasedFirmDecisionEngine,
    )
    import random

    dummy_goods = [{"id": "basic_food", "sector": "FOOD"}]
    initial_needs = {
        "survival": 50,
        "social": 10,
        "growth": 10,
        "survival_need": 50,
        "imitation_need": 0,
        "recognition_need": 0,
        "wealth_need": 0,
    }

    households = [
        Household(
            id=i,
            initial_assets=1000,
            decision_engine=RuleBasedHouseholdDecisionEngine(Config, logger),
            config_module=Config,
            talent=Talent(1.0, {}),
            goods_data=dummy_goods,
            initial_needs=initial_needs,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
        )
        for i in range(Config.NUM_HOUSEHOLDS)
    ]
    firms = [
        Firm(
            id=i + 1000,
            initial_capital=50000,
            initial_liquidity_need=1000,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=StandaloneRuleBasedFirmDecisionEngine(Config, logger),
            value_orientation="PROFIT",
            config_module=Config,
            sector="FOOD",
            is_visionary=(i == 0),
            personality=Personality.BALANCED,
        )  # Firm 0 is Visionary
        for i in range(Config.NUM_FIRMS)
    ]

    sim = Simulation(households, firms, ai_registry, repo, Config, goods_data=[])

    # 2. Run Pre-Unlock Phase (Tick 0-9)
    logger.info("Running Pre-Unlock Phase...")
    for _ in range(9):
        sim.run_tick()

    # Check TFP before unlock
    firm_0_tfp_before = sim.firms[0].productivity_factor
    logger.info(f"Firm 0 TFP Before: {firm_0_tfp_before}")

    # 3. Run Unlock & Diffusion Phase (Tick 10-50)
    logger.info("Running Unlock & Diffusion Phase...")

    tech_unlocked = False
    adopted_count = 0

    for _ in range(41):  # Tick 9 -> 50
        sim.run_tick()

        # Check Tech Manager State
        if "TECH_AGRI_CHEM_01" in sim.technology_manager.active_techs:
            if not tech_unlocked:
                logger.info(f"✅ Tech Unlocked at Tick {sim.time}!")
                tech_unlocked = True

        # Check Adoption
        current_adopted = sum(
            1
            for f in sim.firms
            if sim.technology_manager.has_adopted(f.id, "TECH_AGRI_CHEM_01")
        )
        if current_adopted > adopted_count:
            logger.info(
                f"📈 Adoption increased: {adopted_count} -> {current_adopted} firms."
            )
            adopted_count = current_adopted

    # 4. Verification Assertions
    logger.info("--- Verification Results ---")

    # A. Tech Unlock
    if tech_unlocked:
        logger.info("✅ Tech Unlock Verified.")
    else:
        logger.error("❌ Tech Unlock Failed.")

    # B. Visionary Adoption
    if sim.technology_manager.has_adopted(firms[0].id, "TECH_AGRI_CHEM_01"):
        logger.info("✅ Visionary Firm Adoption Verified.")
    else:
        logger.error("❌ Visionary Firm Adoption Failed.")

    # C. Productivity Boost
    # Firm 0's actual output or effective TFP should be 3x base
    mult = sim.technology_manager.get_productivity_multiplier(firms[0].id, "FOOD")
    if mult == 3.0:
        logger.info(f"✅ Productivity Multiplier Verified: {mult}")
    else:
        logger.error(f"❌ Productivity Multiplier Mismatch: {mult} (Expected 3.0)")

    # D. Diffusion
    if adopted_count > 1:
        logger.info(
            f"✅ Diffusion Verified (Total Adopted: {adopted_count}/{len(firms)})"
        )
    else:
        logger.warning(
            f"⚠️ Diffusion Slow/Failed (Total Adopted: {adopted_count}). Check rate."
        )

    logger.info("--- Verification Complete ---")


if __name__ == "__main__":
    verify_industrial_revolution()
