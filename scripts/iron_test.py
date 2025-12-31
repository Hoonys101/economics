"""
MVP Iron Test: 1000-tick simulation to verify Phase 1-6 integration.
"""
import json
import logging
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.db.repository import SimulationRepository
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.ai_model import AIDecisionEngine, AIEngineRegistry
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.ai.api import Personality

# Setup Logging
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and errors
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("IRON_TEST")
logger.setLevel(logging.INFO)

def run_iron_test(num_ticks: int = 1000):
    logger.info(f"=== IRON TEST: {num_ticks} Tick MVP Verification ===")
    
    # 1. Load goods data
    with open("data/goods.json", "r", encoding="utf-8") as f:
        goods_data = json.load(f)
    for good in goods_data:
        if good["id"] in config.GOODS:
            good["utility_effects"] = config.GOODS[good["id"]].get("utility_effects", {})
    
    # 2. Setup AI Infrastructure
    action_proposal_engine = ActionProposalEngine(config)
    state_builder = StateBuilder()
    ai_manager = AIEngineRegistry(action_proposal_engine, state_builder)
    
    # 3. Create Households
    households = []
    all_value_orientations = [
        config.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
        config.VALUE_ORIENTATION_NEEDS_AND_GROWTH,
        config.VALUE_ORIENTATION_NEEDS_AND_SOCIAL_STATUS,
    ]
    
    for i in range(config.NUM_HOUSEHOLDS):
        value_orientation = random.choice(all_value_orientations)
        ai_decision_engine = ai_manager.get_engine(value_orientation)
        household_ai = HouseholdAI(agent_id=str(i), ai_decision_engine=ai_decision_engine)
        household_decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
        
        households.append(
            Household(
                id=i,
                talent=Talent(1.0, {}),
                goods_data=goods_data,
                initial_assets=config.INITIAL_HOUSEHOLD_ASSETS_MEAN,
                initial_needs={
                    "survival": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("survival", 60.0),
                    "asset": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("asset", 10.0),
                    "social": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("social", 20.0),
                    "improvement": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("improvement", 10.0),
                },
                decision_engine=household_decision_engine,
                value_orientation=value_orientation,
                personality=random.choice(list(Personality)),
                logger=logger,
                config_module=config,
            )
        )
    
    # 3.5 Create AI Trainer (after households)
    ai_trainer = AITrainingManager(agents=households, config_module=config)
    
    # 4. Create Firms
    firms = []
    specializations = ["basic_food", "clothing", "education_service"]  # Must match config.GOODS keys
    
    for i in range(config.NUM_FIRMS):
        firm_value_orientation = random.choice(all_value_orientations)
        ai_decision_engine = ai_manager.get_engine(firm_value_orientation)
        firm_ai = FirmAI(agent_id=str(i + config.NUM_HOUSEHOLDS), ai_decision_engine=ai_decision_engine)
        firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)
        
        firms.append(
            Firm(
                id=i + config.NUM_HOUSEHOLDS,
                initial_capital=config.INITIAL_FIRM_CAPITAL_MEAN,
                initial_liquidity_need=config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN,
                specialization=specializations[i % len(specializations)],
                productivity_factor=random.uniform(5.0, 15.0),
                decision_engine=firm_decision_engine,
                value_orientation=firm_value_orientation,
                config_module=config,
                logger=logger,
            )
        )
    
    # 5. Create Simulation
    repository = SimulationRepository()
    
    simulation = Simulation(
        households=households,
        firms=firms,
        ai_trainer=ai_trainer,
        repository=repository,
        config_module=config,
        goods_data=goods_data,
    )
    
    logger.info(f"Simulation initialized: {len(households)} Households, {len(firms)} Firms")
    
    # 6. Run Simulation
    start_time = __import__("time").time()
    
    for tick in range(1, num_ticks + 1):
        try:
            simulation.run_tick()
            
            if tick % 100 == 0:
                # Progress report
                active_hh = sum(1 for h in simulation.households if h.is_active)
                active_firms = sum(1 for f in simulation.firms if f.is_active)
                gov_assets = simulation.government.assets if simulation.government else 0
                
                logger.info(
                    f"Tick {tick:4d} | HH: {active_hh}/{len(simulation.households)} | "
                    f"Firms: {active_firms}/{len(simulation.firms)} | Gov Assets: {gov_assets:.0f}"
                )
        except Exception as e:
            logger.error(f"ERROR at tick {tick}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    elapsed = __import__("time").time() - start_time
    
    # 7. Final Report
    logger.info("=" * 60)
    logger.info("=== IRON TEST FINAL REPORT ===")
    logger.info(f"Duration: {elapsed:.1f}s for {num_ticks} ticks ({num_ticks/elapsed:.1f} ticks/sec)")
    
    # Survivability
    active_hh = sum(1 for h in simulation.households if h.is_active)
    active_firms = sum(1 for f in simulation.firms if f.is_active)
    total_hh = len(simulation.households)
    total_firms = len(simulation.firms)
    
    logger.info(f"[Survivability] Households: {active_hh}/{total_hh} ({100*active_hh/total_hh:.1f}%)")
    logger.info(f"[Survivability] Firms: {active_firms}/{total_firms} ({100*active_firms/total_firms:.1f}%)")
    
    # Fiscal Balance
    if simulation.government:
        gov = simulation.government
        logger.info(f"[Fiscal] Government Assets: {gov.assets:.0f}")
        total_tax = getattr(gov, 'total_tax_collected', getattr(gov, 'cumulative_tax_income', 0))
        total_welfare = getattr(gov, 'total_welfare_paid', getattr(gov, 'cumulative_welfare_expense', 0))
        logger.info(f"[Fiscal] Total Tax Collected: {total_tax:.0f}")
        logger.info(f"[Fiscal] Total Welfare Paid: {total_welfare:.0f}")
    
    # Brand Effect (Sample)
    if active_firms > 0:
        best_brand_firm = max(
            [f for f in simulation.firms if f.is_active],
            key=lambda f: f.brand_manager.brand_awareness
        )
        logger.info(f"[Brand] Top Brand: Firm {best_brand_firm.id} | "
                   f"Awareness: {best_brand_firm.brand_manager.brand_awareness:.4f} | "
                   f"Marketing Spend: {best_brand_firm.marketing_budget:.0f}")
    
    # Summary CSV
    summary_file = "iron_test_summary.csv"
    with open(summary_file, "w") as f:
        f.write("metric,value\n")
        f.write(f"total_ticks,{num_ticks}\n")
        f.write(f"elapsed_seconds,{elapsed:.1f}\n")
        f.write(f"active_households,{active_hh}\n")
        f.write(f"total_households,{total_hh}\n")
        f.write(f"active_firms,{active_firms}\n")
        f.write(f"total_firms,{total_firms}\n")
        if simulation.government:
            f.write(f"gov_assets,{simulation.government.assets:.0f}\n")
            f.write(f"total_tax,{simulation.government.total_tax_collected:.0f}\n")
            f.write(f"total_welfare,{simulation.government.total_welfare_paid:.0f}\n")
    
    logger.info(f"Summary saved to: {summary_file}")
    logger.info("=== IRON TEST COMPLETE ===")
    
    return simulation

if __name__ == "__main__":
    run_iron_test(1000)
