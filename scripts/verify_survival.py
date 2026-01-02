import sys
import logging
import sqlite3
import random
import config

# Mock Database to Memory BEFORE other imports that might use it
from simulation.db import database
database.DATABASE_NAME = ":memory:"
database.db_manager._conn = None

from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.ai_model import AIEngineRegistry
from simulation.db.repository import SimulationRepository
from simulation.ai.enums import Personality
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.firm_ai import FirmAI
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifySurvival")

def run_survival_test():
    logger.info("Starting Survival Verification (1000 Ticks)...")

    repository = SimulationRepository()
    action_proposal = ActionProposalEngine(config)
    state_builder = StateBuilder()
    ai_registry = AIEngineRegistry(action_proposal, state_builder)

    households = []

    goods_data = []
    for k, v in config.GOODS.items():
        g = v.copy()
        g["id"] = k
        goods_data.append(g)

    for i in range(config.NUM_HOUSEHOLDS):
        personality = random.choice([Personality.MISER, Personality.STATUS_SEEKER, Personality.GROWTH_ORIENTED])
        value_orientation = random.choice([config.VALUE_ORIENTATION_WEALTH_AND_NEEDS, config.VALUE_ORIENTATION_NEEDS_AND_GROWTH])

        talent = Talent(base_learning_rate=0.1, max_potential={})

        ai_engine = HouseholdAI(str(i), ai_registry.get_engine("wealth_and_needs"))
        decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine, config, logger)

        h = Household(
            id=i,
            talent=talent,
            goods_data=goods_data,
            initial_assets=random.gauss(config.INITIAL_HOUSEHOLD_ASSETS_MEAN, config.INITIAL_HOUSEHOLD_ASSETS_MEAN * 0.2),
            initial_needs=config.INITIAL_HOUSEHOLD_NEEDS_MEAN.copy(),
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            personality=personality,
            config_module=config,
            logger=logger
        )
        decision_engine.household = h
        households.append(h)

    firms = []
    for i in range(config.NUM_FIRMS):
        firm_id = len(households) + i
        value_orientation = random.choice([config.VALUE_ORIENTATION_WEALTH_AND_NEEDS, config.VALUE_ORIENTATION_NEEDS_AND_GROWTH])

        ai_engine = FirmAI(str(firm_id), ai_registry.get_engine("wealth_and_needs"))
        decision_engine = AIDrivenFirmDecisionEngine(ai_engine, config, logger)

        f = Firm(
            id=firm_id,
            initial_capital=config.INITIAL_FIRM_CAPITAL_MEAN,
            initial_liquidity_need=config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN,
            specialization=random.choice(["basic_food", "clothing"]),
            productivity_factor=config.FIRM_PRODUCTIVITY_FACTOR,
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            config_module=config,
            logger=logger
        )
        decision_engine.firm = f
        firms.append(f)

    # --- Initial Employment Setup ---
    employment_rate = 1.0
    num_employed = int(config.NUM_HOUSEHOLDS * employment_rate)

    for i in range(num_employed):
        h = households[i]
        f = firms[i % config.NUM_FIRMS]

        h.is_employed = True
        h.employer_id = f.id
        h.current_wage = config.INITIAL_WAGE
        h.hired_at_tick = 0

        f.employees.append(h)
        f.employee_wages[h.id] = config.INITIAL_WAGE

    logger.info(f"Initialized Employment: {num_employed} households assigned to firms.")

    # 5. Initialize Simulation
    sim = Simulation(
        households=households,
        firms=firms,
        ai_trainer=ai_registry,
        repository=repository,
        config_module=config,
        goods_data=goods_data,
        logger=logger
    )

    # 6. Run Loop
    for t in range(1000):
        try:
            sim.run_tick()

            if t % 100 == 0:
                active_h = len([h for h in sim.households if h.is_active])
                gov_cash = sim.government.assets
                total_production = sim.tracker.get_latest_indicators().get("total_production", 0)
                logger.info(f"Tick {t} | Active: {active_h} | Gov: {gov_cash:.1f} | Prod: {total_production:.1f}")

        except Exception as e:
            logger.error(f"Tick {t} Failed: {e}")
            raise e

    # 7. Final Verification
    active_households = len([h for h in sim.households if h.is_active])
    survival_rate = active_households / config.NUM_HOUSEHOLDS
    gov_cash = sim.government.assets
    approval = getattr(sim.government, "approval_rating", 0.5)
    tax_rate = getattr(sim.government, "income_tax_rate", 0.2)

    logger.info(f"FINAL RESULT | Active: {active_households}/{config.NUM_HOUSEHOLDS} ({survival_rate*100:.1f}%) | Gov Cash: {gov_cash:.2f}")
    logger.info(f"FINAL GOV STATE | Approval: {approval:.2f} | Tax Rate: {tax_rate:.2f}")

    print(f"Active: {active_households} ({survival_rate*100:.1f}%)")
    print(f"Gov Cash: {gov_cash:.2f}")

if __name__ == "__main__":
    run_survival_test()
