"""
Iron Test Script (Phase 21.5)
Goal: Find the balance point where automation does not destroy the economy.
Tasks:
1. Run simulation for 1000 ticks.
2. Track Labor Share, Unemployment, and GDP.
3. Analyze results against thresholds.
4. Output report.
"""
import sys
import os
import argparse
import logging
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.db.repository import SimulationRepository
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.ai_model import AIEngineRegistry
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.ai.api import Personality
import random

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("IRON_TEST")

def calculate_labor_share(tracker, simulation):
    """
    Calculates Labor Share = Total Wage Income / Nominal GDP
    Nominal GDP = Total Production Quantity * Average Goods Price
    """
    indicators = tracker.get_latest_indicators()

    # Nominal GDP = Production * Price
    total_production = indicators.get("total_production", 0.0)
    avg_price = indicators.get("avg_goods_price", 0.0)
    # Fallback to 10.0 if avg_price is 0 (initial)
    if avg_price <= 0: avg_price = 10.0

    nominal_gdp = total_production * avg_price

    # Total Wages (User Instruction: Fallback Logic)
    total_wages = indicators.get("total_labor_income", 0.0)

    # Fallback if tracker misses it
    if total_wages == 0:
        total_wages = sum(
            sum(f.employee_wages.values())
            for f in simulation.firms if f.is_active
        )

    if nominal_gdp > 0:
        return total_wages / nominal_gdp
    return 0.0

def run_simulation(ticks: int):
    logger.info(f"=== IRON TEST START: {ticks} Ticks ===")
    
    # 1. Setup Data
    with open("data/goods.json", "r", encoding="utf-8") as f:
        goods_data = json.load(f)
    
    # 2. AI Setup
    action_proposal = ActionProposalEngine(config)
    state_builder = StateBuilder()
    ai_registry = AIEngineRegistry(action_proposal, state_builder)
    
    # 3. Agents
    households = []
    for i in range(config.NUM_HOUSEHOLDS):
        h_ai = HouseholdAI(str(i), ai_registry.get_engine(config.VALUE_ORIENTATION_WEALTH_AND_NEEDS))
        decision = AIDrivenHouseholdDecisionEngine(h_ai, config, logger)
        households.append(Household(
            id=i,
            talent=Talent(1.0, {}),
            goods_data=goods_data,
            initial_assets=config.INITIAL_HOUSEHOLD_ASSETS_MEAN,
            decision_engine=decision,
            initial_needs=config.INITIAL_HOUSEHOLD_NEEDS_MEAN.copy(),
            value_orientation=config.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
            personality=Personality.BALANCED,
            config_module=config,
            logger=logger
        ))
        
    firms = []
    specializations = list(config.FIRM_SPECIALIZATIONS.values())
    for i in range(config.NUM_FIRMS):
        f_ai = FirmAI(str(i + config.NUM_HOUSEHOLDS), ai_registry.get_engine(config.VALUE_ORIENTATION_WEALTH_AND_NEEDS))
        decision = AIDrivenFirmDecisionEngine(f_ai, config, logger)
        spec = specializations[i % len(specializations)]
        firms.append(Firm(
            id=i + config.NUM_HOUSEHOLDS,
            initial_capital=config.INITIAL_FIRM_CAPITAL_MEAN,
            initial_liquidity_need=100.0,
            specialization=spec,
            productivity_factor=20.0, # High productivity for automation test
            decision_engine=decision,
            value_orientation=config.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
            config_module=config,
            logger=logger,
            personality=Personality.BALANCED
        ))
        
    # 4. Engine
    repo = SimulationRepository() # In-memory SQLite default? No, file based.
    # Note: If we run this multiple times, we might bloat DB. But it's fine for test.
    
    # AI Trainer needs agents list
    # Re-instantiate AITrainingManager correctly
    ai_trainer = AITrainingManager(households + firms, config)

    simulation = Simulation(
        households=households,
        firms=firms,
        ai_trainer=ai_registry,
        repository=repo,
        config_module=config,
        goods_data=goods_data,
        logger=logger
    )
    
    # 5. Baseline for GDP
    simulation.run_tick() # Tick 1
    initial_indicators = simulation.tracker.get_latest_indicators()
    initial_gdp = initial_indicators.get("total_production", 0.0)
    logger.info(f"Baseline GDP (Physical): {initial_gdp}")
    
    # Metrics tracking
    min_labor_share = 1.0
    max_unemployment = 0.0
    final_pop = len(households)
    
    passed = True
    failure_reason = ""

    # 6. Loop
    for t in range(2, ticks + 1):
        try:
            simulation.run_tick()
            
            indicators = simulation.tracker.get_latest_indicators()

            # --- Checks ---

            # 1. GDP Threshold (50% of Initial Physical GDP)
            current_gdp = indicators.get("total_production", 0.0)
            if initial_gdp > 0 and current_gdp < (initial_gdp * 0.5):
                passed = False
                failure_reason = f"GDP Collapse at tick {t} ({current_gdp:.2f} < {initial_gdp*0.5:.2f})"
                # Don't break, finish run to see full effect

            # 2. Labor Share
            l_share = calculate_labor_share(simulation.tracker, simulation)
            if l_share < min_labor_share: min_labor_share = l_share

            # 3. Unemployment
            u_rate = indicators.get("unemployment_rate", 0.0) / 100.0
            if u_rate > max_unemployment: max_unemployment = u_rate

            if t % 100 == 0:
                logger.info(f"Tick {t} | LaborShare: {l_share:.2%} | Unemp: {u_rate:.1%} | GDP: {current_gdp:.2f}")

        except Exception as e:
            logger.error(f"Simulation Crashed at tick {t}: {e}")
            passed = False
            failure_reason = f"Crash: {e}"
            import traceback
            traceback.print_exc()
            break

    # Final Checks
    final_indicators = simulation.tracker.get_latest_indicators()
    final_gdp = final_indicators.get("total_production", 0.0)
    final_pop = sum(1 for h in households if h.is_active)
    
    # Verification Rules
    if final_pop < config.NUM_HOUSEHOLDS * 0.5: # Pop collapse check
        passed = False
        failure_reason += " | Population Collapse"

    if min_labor_share < 0.30:
        passed = False
        failure_reason += f" | Labor Share Too Low (Min: {min_labor_share:.1%})"

    # Note: User requirements say "Verification: Labor Share >= 30%".
    # User instructions for Analysis: "Labor Share < 30% -> Increase Cost".
    # This implies failing the test is EXPECTED during tuning.
    
    simulation.finalize_simulation()
    
    # Report
    with open("reports/iron_test_phase21_result.md", "w") as f:
        f.write(f"# Iron Test Phase 21 Result\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Ticks: {ticks}\n")
        f.write(f"- Final Population: {final_pop}\n")
        f.write(f"- Final GDP: {final_gdp:.2f}\n")
        f.write(f"- Min Labor Share: {min_labor_share:.1%}\n")
        f.write(f"- Max Unemployment: {max_unemployment:.1%}\n")
        f.write(f"- Automation Cost: {getattr(config, 'AUTOMATION_COST_PER_PCT', 'N/A')}\n")
        f.write(f"- Labor Reduction: {getattr(config, 'AUTOMATION_LABOR_REDUCTION', 'N/A')}\n")
        f.write(f"\n## Verdict: {'PASS' if passed else 'FAIL'}\n")
        if not passed:
            f.write(f"**Reason**: {failure_reason}\n")

    logger.info(f"Test Complete. Verdict: {'PASS' if passed else 'FAIL'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Remove default=1000 from ticks to correctly detect if user provided it
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--num_ticks", type=int, help="Legacy support", default=None)

    args = parser.parse_args()

    # Priority: --ticks > --num_ticks > Default (1000)
    if args.ticks is not None:
        ticks = args.ticks
    elif args.num_ticks is not None:
        ticks = args.num_ticks
    else:
        ticks = 1000

    run_simulation(ticks)
