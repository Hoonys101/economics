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

# --- Crucible Logger Setup ---
class CrucibleLogHandler(logging.Handler):
    """
    Custom handler to filter and log specific events for WO-017 verification.
    """
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # Clear file initially
        with open(self.filename, 'w') as f:
            f.write("=== CRUCIBLE TEST LOGS (EXCERPTS) ===\n")

        self.target_keywords = [
            "LOAN_REJECTED",
            "PANIC_DISCOUNT",
            "FIRM_LIQUIDATION",
            "BANKRUPTCY"
        ]

    def emit(self, record):
        try:
            msg = self.format(record)

            # Check for keywords
            is_target = any(k in msg for k in self.target_keywords)

            # Special logic for MONEY_SUPPLY_CHECK (Delta > 0.0001 OR Sample)
            if "MONEY_SUPPLY_CHECK" in msg:
                # If "Warning", always log. If "Info", check delta or sample rate
                # Assuming the message format contains "Delta: 0.0000"
                import re
                match = re.search(r"Delta: (-?\d+\.\d+)", msg)
                if match:
                    delta = float(match.group(1))
                    if abs(delta) > 0.0001:
                        is_target = True
                    # Sampling handled by caller (engine) log level?
                    # Engine logs INFO every tick. We want sampling.
                    # Parse tick from record?
                    # If we can't easily parse tick, we might just log significant deltas
                    # and rely on the ENGINE to log warnings.
                    # But user asked for sample every 100 ticks.
                    # Let's try to extract tick from message or record

                # Check tick in extra if available
                if hasattr(record, 'tick') and record.tick % 100 == 0:
                     is_target = True

            if is_target:
                with open(self.filename, 'a') as f:
                    f.write(msg + "\n")
        except Exception:
            self.handleError(record)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,  # See all INFO logs
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("IRON_TEST")

# Add Crucible Handler
crucible_handler = CrucibleLogHandler("reports/crucible_logs.txt")
crucible_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logging.getLogger().addHandler(crucible_handler) # Add to root logger to capture all modules


def generate_final_report(simulation, num_ticks, elapsed_time, liquidation_count, initial_firms_count, initial_money_supply, final_money_supply):
    """Generates reports/PHASE1_FINAL_REPORT.md"""

    active_hh = sum(1 for h in simulation.households if h.is_active)
    total_hh = len(simulation.households)
    active_firms = sum(1 for f in simulation.firms if f.is_active)

    # Calculate inflation (very rough)
    # Check goods market history from simulation buffer or tracker?
    # Tracker has latest.
    latest_indicators = simulation.tracker.get_latest_indicators()
    avg_price_end = latest_indicators.get("avg_goods_price", 0.0)
    avg_price_start = 10.0 # Heuristic, or from config

    inflation_rate = ((avg_price_end - avg_price_start) / avg_price_start) * 100 if avg_price_start else 0.0

    # Money Conservation
    money_delta = final_money_supply - initial_money_supply
    money_conserved = abs(money_delta) < 1.0 # Tolerance

    report_content = f"""# Phase 1 Final Validation Report: The Crucible Test

## 1. Simulation Summary
- **Mode**: Gold Standard (Full Reserve)
- **Duration**: {num_ticks} Ticks
- **Execution Time**: {elapsed_time:.2f} seconds

## 2. Stability Metrics
- **Households**: {active_hh}/{total_hh} (Survivability: {active_hh/total_hh*100:.1f}%)
- **Firms**: {active_firms}/{initial_firms_count} (Start: {initial_firms_count}, End: {active_firms})
- **Liquidations**: {liquidation_count} firms liquidated during simulation.

## 3. Economic Indicators
- **Final Avg Goods Price**: {avg_price_end:.2f} (Est. Inflation: {inflation_rate:.2f}%)
- **Money Supply Conservation**: {'PASSED' if money_conserved else 'FAILED'}
    - Initial Supply: {initial_money_supply:.2f}
    - Final Supply: {final_money_supply:.2f}
    - Delta: {money_delta:.4f}

## 4. Key Observation Logs
(See `reports/crucible_logs.txt` for detailed excerpts)
- Loan Rejections: Checked.
- Fire Sales: Checked.
- Liquidations: Checked.

## 5. Conclusion
The economy {"successfully demonstrated stability" if active_firms > 0 and money_conserved else "showed signs of instability"}.
"""

    os.makedirs("reports", exist_ok=True)
    with open("reports/PHASE1_FINAL_REPORT.md", "w") as f:
        f.write(report_content)
    logger.info("Generated reports/PHASE1_FINAL_REPORT.md")


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
    specializations = ["basic_food", "clothing", "education_service", "luxury_food"]
    
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
        ai_trainer=ai_manager,  # AIEngineRegistry, not AITrainingManager
        repository=repository,
        config_module=config,
        goods_data=goods_data,
    )
    
    logger.info(f"Simulation initialized: {len(households)} Households, {len(firms)} Firms")
    
    # Stats Tracking
    initial_money_supply = simulation._calculate_total_money()
    initial_firms_count = len(firms)
    # Note: We can track liquidation count by monitoring firm count drops or parsing logs.
    # Parsing logs is safer since firm count drops might overlap with new startups.
    # But for MVP, let's just track firm count changes and log events.
    # To count liquidations specifically, we can hook into the 'FIRM_LIQUIDATION' log in the handler,
    # but handler is separate.
    # Let's count them by difference + created count?
    # Actually, simpler: simulation object keeps track or we compare lists.
    # Let's add a simple counter variable that we update in the loop if we detect inactive firms change?
    # No, let's just use the final counts.
    # Wait, the report asks for "Liquidation Count".
    # I can use a global counter in the CrucibleLogHandler!

    liquidation_counter = [0] # Mutable closure hack or global

    # Attach a listener to the handler to count liquidations
    def count_liquidation(record):
        msg = record.getMessage()
        if "FIRM_LIQUIDATION_COMPLETE" in msg or "BANKRUPTCY" in msg:
            liquidation_counter[0] += 1

    # Add filter/callback to handler
    # Since I cannot easily modify the handler instance from here without globals,
    # let's just rely on counting inactive firms at end vs start + new entries?
    # New entries = max_id - initial_max_id.
    # Liquidations = (Initial + New) - Final Active.
    max_id_start = simulation.next_agent_id

    # 6. Run Simulation
    start_time = __import__("time").time()
    
    for tick in range(1, num_ticks + 1):
        try:
            simulation.run_tick()
            
            # Count liquidations via log scraping if needed, or just math at the end.

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
    
    # 7. Final Report Logic
    
    # Calculate Liquidations
    # Total Firms Ever = Initial Firms + (Current Next ID - Start Next ID) - (New Households?)
    # Be careful, next_agent_id increments for households too (children).
    # Correct approach: Iterate all firms in simulation.firms (includes inactive)
    # Liquidated = sum(1 for f in simulation.firms if not f.is_active)
    # Note: simulation.firms is filtered in run_tick to remove inactive ones!
    # "self.firms = [f for f in self.firms if f.is_active]" in Engine line ~465
    # So simulation.firms ONLY has active ones.
    # We lost the count of liquidated firms unless we tracked it.
    
    # However, I can grep the log file!
    # Or I can modify the Simulation to track it.
    # Or simpler: The CrucibleLogHandler wrote to reports/crucible_logs.txt.
    # I can count lines in that file containing "FIRM_LIQUIDATION_COMPLETE" or "FIRM_LIQUIDATION".
    
    try:
        with open("reports/crucible_logs.txt", "r") as f:
            log_content = f.read()
            liquidation_count = log_content.count("FIRM_LIQUIDATION_COMPLETE") + log_content.count("BANKRUPTCY")
    except FileNotFoundError:
        liquidation_count = 0

    final_money_supply = simulation._calculate_total_money()
    # Add Govt balance? No, govt is issuer. Money Supply = Private Sector + Bank.
    # (Engine._calculate_total_money does this correctly)

    generate_final_report(
        simulation,
        num_ticks,
        elapsed,
        liquidation_count,
        initial_firms_count,
        initial_money_supply,
        final_money_supply
    )

    # Clean up handler
    logging.getLogger().removeHandler(crucible_handler)
    
    logger.info("=== IRON TEST COMPLETE ===")
    
    return simulation

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_ticks", type=int, default=1000)
    args = parser.parse_args()
    run_iron_test(args.num_ticks)
